#!/usr/bin/env python3

from decimal import Decimal

import argparse
import base64
import copy
import datetime
import dateutil.parser
import json
import os
import sys
import time

import backoff
import requests
import stitchstream

import schemas

logger = stitchstream.get_logger()

BASE_URL = 'https://api.outbrain.com/amplify/v0.1'

DEFAULT_STATE = {
    'campaign_performance': {},
    'link_performance': {}
}

DEFAULT_START_DATE = '2016-08-01'


def giveup(error):
    logger.error(error.response.text)
    response = error.response
    return not (response.status_code == 429 or
                response.status_code >= 500)


@backoff.on_exception(backoff.constant,
                      (requests.exceptions.RequestException),
                      jitter=backoff.random_jitter,
                      max_tries=5,
                      giveup=giveup,
                      interval=30)
def request(url, access_token, params={}):
    logger.info("Making request: GET {} {}".format(url, params))

    try:
        response = requests.get(
            url,
            headers={'OB-TOKEN-V1': access_token},
            params=params)
    except e:
        logger.exception(e)

    logger.info("Got response code: {}".format(response.status_code))

    response.raise_for_status()
    return response


def generate_token(username, password):
    logger.info("Generating new token using basic auth.")

    encoded = base64.b64encode(bytes('{}:{}'.format(username, password),
                                     'utf-8')) \
                    .decode('utf-8')

    try:
        response = requests.get(
            '{}/login'.format(BASE_URL),
            headers={'Authorization': 'Basic {}'.format(encoded)})
    except e:
        logger.exception(e)
        raise e

    logger.info("Got response code: {}".format(response.status_code))

    return response.json().get('OB-TOKEN-V1')


def parse_datetime(datetime):
    dt = dateutil.parser.parse(datetime)

    # TODO the assumption is that the timestamp comes in in UTC, but that
    #      may not be true. verify w/ outbrain.
    return dt.isoformat('T') + 'Z'


def parse_performance(result, extra_fields):
    metrics = result.get('metrics', {})
    metadata = result.get('metadata', {})

    to_return = {
        'fromDate': metadata.get('fromDate'),
        'impressions': int(metrics.get('impressions', 0)),
        'clicks': int(metrics.get('clicks', 0)),
        'ctr': float(metrics.get('ctr', 0.0)),
        'spend': float(metrics.get('spend', 0.0)),
        'ecpc': float(metrics.get('ecpc', 0.0)),
        'conversions': int(metrics.get('conversions', 0)),
        'conversionRate': float(metrics.get('conversionRate', 0.0)),
        'cpa': float(metrics.get('cpa', 0.0)),
    }
    to_return.update(extra_fields)

    return to_return


def get_date_ranges(start, end, interval_in_days):
    if start > end:
        return []

    to_return = []
    interval_start = start

    while interval_start < end:
        to_return.append({
            'from_date': interval_start,
            'to_date': min(end,
                           (interval_start + datetime.timedelta(
                               days=interval_in_days-1)))
        })

        interval_start = interval_start + datetime.timedelta(
            days=interval_in_days)

    return to_return


def sync_campaign_performance(state, access_token, account_id, campaign_id):
    return sync_performance(
        state,
        access_token,
        account_id,
        'campaign_performance',
        campaign_id,
        {'campaignId': campaign_id},
        {'campaignId': campaign_id})


def sync_link_performance(state, access_token, account_id, campaign_id,
                          link_id):
    return sync_performance(
        state,
        access_token,
        account_id,
        'link_performance',
        link_id,
        {'promotedLinkId': link_id},
        {'campaignId': campaign_id,
         'linkId': link_id})


def sync_performance(state, access_token, account_id, table_name, state_sub_id,
                     extra_params, extra_persist_fields):
    """
    This function is heavily parameterized as it is used to sync performance
    both based on campaign ID alone, and by campaign ID and link ID.

    - `state`: state map
    - `access_token`: access token for Outbrain Amplify API
    - `account_id`: Outbrain marketer ID
    - `table_name`: the table name to use. At present, one of
                    `campaign_performance` or `link_performance`.
    - `state_sub_id`: the id to use within the state map to identify this
                      sub-object. For example,

                        state['link_performance'][link_id]

                      is used for the `link_performance` table.
    - `extra_params`: extra params sent to the Outbrain API
    - `extra_persist_fields`: extra fields pushed into the destination data.
                              For example:

                                {'campaignId': '000b...',
                                 'promotedLinkId': '000a...'}

                              is used for `link_performance`.
    """
    # sync 2 days before last saved date, or DEFAULT_START_DATE
    from_date = datetime.datetime.strptime(
        state.get(table_name, {})
             .get(state_sub_id, DEFAULT_START_DATE),
        '%Y-%m-%d').date() - datetime.timedelta(days=2)

    to_date = datetime.date.today()

    interval_in_days = 100

    date_ranges = get_date_ranges(from_date, to_date, interval_in_days)

    last_request_start = None

    for date_range in date_ranges:
        logger.info(
            'Pulling {} for {} from {} to {}'
            .format(table_name,
                    extra_persist_fields,
                    date_range.get('from_date'),
                    date_range.get('to_date')))

        params = {
            'from': date_range.get('from_date'),
            'to': date_range.get('to_date'),
            'breakdown': 'daily',
            'limit': 100,
            'sort': '+fromDate',
            'includeArchivedCampaigns': True,
        }
        params.update(extra_params)

        last_request_start = time.time()
        response = request(
            '{}/reports/marketers/{}/periodic'.format(BASE_URL, account_id),
            access_token,
            params)
        last_request_end = time.time()

        logger.info('Done in {} sec'.format(time.time() - last_request_start))

        performance = [
            parse_performance(result, extra_persist_fields)
            for result in response.json().get('results')]

        stitchstream.write_records(table_name, performance)

        last_record = performance[-1]
        new_from_date = last_record.get('fromDate')

        state[table_name][state_sub_id] = new_from_date
        stitchstream.write_state(state)

        from_date = new_from_date

        if last_request_start is not None and \
           (time.time() - last_request_end) < 30:
            to_sleep = 30 - (time.time() - last_request_end)
            logger.info(
                'Limiting to 2 requests per minute. Sleeping {} sec '
                'before making the next reporting request.'
                .format(to_sleep))
            time.sleep(to_sleep)


def parse_campaign(campaign):
    if campaign.get('budget') is not None:
        campaign['budget']['creationTime'] = parse_datetime(
            campaign.get('budget').get('creationTime'))
        campaign['budget']['lastModified'] = parse_datetime(
            campaign.get('budget').get('lastModified'))

    return campaign


def sync_campaigns(state, access_token, account_id):
    logger.info('Syncing campaigns.')

    start = time.time()
    response = request(
        '{}/marketers/{}/campaigns'.format(BASE_URL, account_id),
        access_token, {})

    campaigns = [parse_campaign(campaign) for campaign
                 in response.json().get('campaigns', [])]

    stitchstream.write_records('campaigns', campaigns)

    logger.info('Done in {} sec.'.format(time.time() - start))

    campaigns_done = 0

    for campaign in campaigns:
        # commenting this for now because it makes the integration take too
        # long for users with many campaigns. outbrain rate limits requests
        # to the reporting API at about 2 requests per minute. if we can
        # get them to raise that, this can be uncommented and will work great.
        #    - Connor (@cmcarthur on Github)
        #
        # sync_links(state, access_token, account_id, campaign.get('id'))

        sync_campaign_performance(state, access_token, account_id,
                                  campaign.get('id'))

        campaigns_done = campaigns_done + 1

        logger.info(
            '{} of {} campaigns fully synced.'
            .format(campaigns_done, len(campaigns)))

    logger.info('Done!')


def parse_link(link):
    link['creationTime'] = parse_datetime(link.get('creationTime'))
    link['lastModified'] = parse_datetime(link.get('lastModified'))

    return link


def sync_links(state, access_token, account_id, campaign_id):
    processed_count = 0
    total_count = -1
    fully_synced_count = 0
    limit = 100

    while processed_count != total_count:
        logger.info(
            'Syncing {} links for campaign {} starting from offset {}'
            .format(limit,
                    campaign_id,
                    processed_count))

        start = time.time()
        response = request(
            '{}/campaigns/{}/promotedLinks'.format(BASE_URL, campaign_id),
            access_token, {
                'limit': 100,
                'offset': processed_count
            })

        links = [parse_link(link) for link
                 in response.json().get('promotedLinks', [])]

        stitchstream.write_records('links', links)

        total_count = response.json().get('totalCount')
        processed_count = processed_count + len(links)

        for link in links:
            logger.info(
                'Syncing link performance for link {} of {}.'.format(
                    fully_synced_count,
                    total_count))

            sync_link_performance(state, access_token, account_id, campaign_id,
                                  link.get('id'))

            fully_synced_count = fully_synced_count + 1

        logger.info('Done in {} sec, processed {} of {} links.'
                    .format(time.time() - start,
                            processed_count,
                            total_count))

    logger.info('Done syncing links for campaign {}.'.format(campaign_id))


def do_sync(args):
    state = DEFAULT_STATE

    with open(args.config) as config_file:
        config = json.load(config_file)

    username = config.get('username')
    password = config.get('password')
    account_id = config.get('account_id')

    if username is None:
        logger.fatal("Missing `username`.")
        raise RuntimeError

    if password is None:
        logger.fatal("Missing `password`.")
        raise RuntimeError

    if account_id is None:
        logger.fatal("Missing `account_id`.")
        raise RuntimeError

    access_token = config.get('access_token')

    if access_token is None:
        access_token = generate_token(username, password)

    if access_token is None:
        logger.fatal("Failed to generate a new access token.")
        raise RuntimeError

    stitchstream.write_schema('campaigns', schemas.campaign)
    stitchstream.write_schema('campaign_performance',
                              schemas.campaign_performance)

    stitchstream.write_schema('links', schemas.link)
    stitchstream.write_schema('link_performance',
                              schemas.link_performance)

    sync_campaigns(state, access_token, account_id)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c', '--config', help='Config file', required=True)
    parser.add_argument(
        '-s', '--state', help='State file')

    args = parser.parse_args()

    do_sync(args)


if __name__ == '__main__':
    main()
