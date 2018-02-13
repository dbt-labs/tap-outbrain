#!/usr/bin/env python3

from decimal import Decimal

import argparse
import base64
import copy
import datetime
import json
import os
import sys
import time
import dateutil.parser

import backoff
import requests
import singer
import singer.requests
from singer import utils

import tap_outbrain.schemas as schemas

LOGGER = singer.get_logger()
SESSION = requests.Session()

BASE_URL = 'https://api.outbrain.com/amplify/v0.1'
CONFIG = {}

DEFAULT_STATE = {
    'campaign_performance': {},
    'link_performance': {}
}

DEFAULT_START_DATE = '2016-08-01'


@backoff.on_exception(backoff.constant,
                      (requests.exceptions.RequestException),
                      jitter=backoff.random_jitter,
                      max_tries=5,
                      giveup=singer.requests.giveup_on_http_4xx_except_429,
                      interval=30)
def request(url, access_token, params):
    LOGGER.info("Making request: GET {} {}".format(url, params))
    headers = {'OB-TOKEN-V1': access_token}
    if 'user_agent' in CONFIG:
        headers['User-Agent'] = CONFIG['user_agent']

    req = requests.Request('GET', url, headers=headers, params=params).prepare()
    LOGGER.info("GET {}".format(req.url))
    resp = SESSION.send(req)

    if resp.status_code >= 400:
        LOGGER.error("GET {} [{} - {}]".format(req.url, resp.status_code, resp.content))
        resp.raise_for_status()

    return resp


def generate_token(username, password):
    LOGGER.info("Generating new token using basic auth.")

    auth = requests.auth.HTTPBasicAuth(username, password)
    response = requests.get('{}/login'.format(BASE_URL), auth=auth)
    LOGGER.info("Got response code: {}".format(response.status_code))
    response.raise_for_status()

    return response.json().get('OB-TOKEN-V1')


def parse_datetime(date_time):
    parsed_datetime = dateutil.parser.parse(date_time)

    # the assumption is that the timestamp comes in in UTC
    return parsed_datetime.isoformat('T') + 'Z'


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
        LOGGER.info(
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

        last_request_start = utils.now()
        response = request(
            '{}/reports/marketers/{}/periodic'.format(BASE_URL, account_id),
            access_token,
            params)
        last_request_end = utils.now()

        LOGGER.info('Done in {} sec'.format(
            last_request_end.timestamp() - last_request_start.timestamp()))

        performance = [
            parse_performance(result, extra_persist_fields)
            for result in response.json().get('results')]

        for record in performance:
            singer.write_record(table_name, record, time_extracted=last_request_end)

        last_record = performance[-1]
        new_from_date = last_record.get('fromDate')

        state[table_name][state_sub_id] = new_from_date
        singer.write_state(state)

        from_date = new_from_date

        if last_request_start is not None and \
           (time.time() - last_request_end.timestamp()) < 30:
            to_sleep = 30 - (time.time() - last_request_end.timestamp())
            LOGGER.info(
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
    LOGGER.info('Syncing campaigns.')

    start = utils.now()
    response = request(
        '{}/marketers/{}/campaigns'.format(BASE_URL, account_id),
        access_token, {})

    time_extracted = utils.now()

    campaigns = [parse_campaign(campaign) for campaign
                 in response.json().get('campaigns', [])]

    for record in campaigns:
        singer.write_record('campaigns', record, time_extracted=time_extracted)

    LOGGER.info('Done in {} sec.'.format(time_extracted.timestamp() - start.timestamp()))

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

        LOGGER.info(
            '{} of {} campaigns fully synced.'
            .format(campaigns_done, len(campaigns)))

    LOGGER.info('Done!')


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
        LOGGER.info(
            'Syncing {} links for campaign {} starting from offset {}'
            .format(limit,
                    campaign_id,
                    processed_count))

        start = utils.now()
        response = request(
            '{}/campaigns/{}/promotedLinks'.format(BASE_URL, campaign_id),
            access_token, {
                'limit': 100,
                'offset': processed_count
            })

        time_extracted = utils.now()

        links = [parse_link(link) for link
                 in response.json().get('promotedLinks', [])]

        total_count = response.json().get('totalCount')
        processed_count = processed_count + len(links)

        for link in links:
            singer.write_record('links', link, time_extracted=time_extracted)

            LOGGER.info(
                'Syncing link performance for link {} of {}.'.format(
                    fully_synced_count,
                    total_count))

            sync_link_performance(state, access_token, account_id, campaign_id,
                                  link.get('id'))

            fully_synced_count = fully_synced_count + 1

        LOGGER.info('Done in {} sec, processed {} of {} links.'
                    .format(time_extracted.timestamp() - start.timestamp(),
                            processed_count,
                            total_count))

    LOGGER.info('Done syncing links for campaign {}.'.format(campaign_id))


def do_sync(args):
    #pylint: disable=global-statement
    global DEFAULT_START_DATE
    state = DEFAULT_STATE

    with open(args.config) as config_file:
        config = json.load(config_file)
        CONFIG.update(config)

    missing_keys = []
    if 'username' not in config:
        missing_keys.append('username')
    else:
        username = config['username']

    if 'password' not in config:
        missing_keys.append('password')
    else:
        password = config['password']

    if 'account_id' not in config:
        missing_keys.append('account_id')
    else:
        account_id = config['account_id']

    if 'start_date' not in config:
        missing_keys.append('start_date')
    else:
        # only want the date
        DEFAULT_START_DATE = config['start_date'][:10]

    if missing_keys:
        LOGGER.fatal("Missing {}.".format(", ".join(missing_keys)))
        raise RuntimeError

    access_token = config.get('access_token')

    if access_token is None:
        access_token = generate_token(username, password)

    if access_token is None:
        LOGGER.fatal("Failed to generate a new access token.")
        raise RuntimeError


    singer.write_schema('campaigns',
                        schemas.campaign,
                        key_properties=["id"])
    singer.write_schema('campaign_performance',
                        schemas.campaign_performance,
                        key_properties=["campaignId", "fromDate"],
                        bookmark_properties=["fromDate"])
    singer.write_schema('links',
                        schemas.link,
                        key_properties=["id"])
    singer.write_schema('link_performance',
                        schemas.link_performance,
                        key_properties=["campaignId", "linkId", "fromDate"],
                        bookmark_properties=["fromDate"])

    sync_campaigns(state, access_token, account_id)


def main_impl():
    parser = argparse.ArgumentParser()

    parser.add_argument(
        '-c', '--config', help='Config file', required=True)
    parser.add_argument(
        '-s', '--state', help='State file')

    args = parser.parse_args()

    do_sync(args)


def main():
    try:
        main_impl()
    except Exception as exc:
        LOGGER.critical(exc)
        raise exc


if __name__ == '__main__':
    main()
