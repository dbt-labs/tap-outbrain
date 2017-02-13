#!/usr/bin/env python3

import argparse
import base64
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
    'campaign_performance': {}
}

DEFAULT_START_DATE = '2016-01-01'


# TODO
#  - campaign pagination -- not needed if there are fewer than 100 campaigns

def giveup(error):
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


def parse_campaign_performance(result, campaign_id):
    metrics = result.get('metrics', {})
    metadata = result.get('metadata', {})

    return {
        'campaignId': campaign_id,
        'fromDate': metadata.get('fromDate'),
        'impressions': metrics.get('impressions', 0),
        'clicks': metrics.get('clicks', 0),
        'ctr': metrics.get('ctr', 0.0),
        'spend': metrics.get('spend', 0.0),
        'ecpc': metrics.get('ecpc', 0.0),
        'conversions': metrics.get('conversions', 0),
        'conversionRate': metrics.get('conversionRate', 0.0),
        'cpa': metrics.get('cpa', 0.0),
    }


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
    # sync 2 days before last saved date, or DEFAULT_START_DATE
    from_date = datetime.datetime.strptime(
        state.get('campaign_performance', {})
             .get(campaign_id, DEFAULT_START_DATE),
        '%Y-%m-%d').date() - datetime.timedelta(days=2)

    to_date = datetime.date.today()

    date_ranges = get_date_ranges(from_date, to_date, interval_in_days=100)

    last_request_start = None

    for date_range in date_ranges:
        logger.info(
            'Pulling campaign performance for id {} from {} to {}'
            .format(campaign_id,
                    date_range.get('from_date'),
                    date_range.get('to_date')))

        last_request_start = time.time()
        response = request(
            '{}/reports/marketers/{}/periodic'.format(BASE_URL, account_id),
            access_token,
            {
                'campaignId': campaign_id,
                'from': date_range.get('from_date'),
                'to': date_range.get('to_date'),
                'breakdown': 'daily',
                'limit': 100,
                'sort': '+fromDate',
            })
        last_request_end = time.time()

        logger.info('Done in {} sec'.format(time.time() - last_request_start))

        campaign_performance = [
            parse_campaign_performance(
                result, campaign_id)
            for result in response.json().get('results')]

        stitchstream.write_records('campaign_performance',
                                   campaign_performance)

        last_record = campaign_performance[-1]
        new_from_date = last_record.get('fromDate')

        state['campaign_performance'][campaign_id] = new_from_date
        stitchstream.write_state(state)

        from_date = new_from_date

        if last_request_start is not None and \
           time.time() - last_request_end < 15:
            to_sleep = 15 - (time.time() - last_request_end)
            logger.info(
                'Limiting to 4 requests per minute. Sleeping {} sec '
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
    params = {}
    has_more = True

    while has_more:
        logger.info('Syncing campaigns.')

        start = time.time()
        response = request(
            '{}/marketers/{}/campaigns'.format(BASE_URL, account_id),
            access_token, params)

        campaigns = [parse_campaign(campaign) for campaign
                     in response.json().get('campaigns', [])]

        stitchstream.write_records('campaigns', campaigns)

        logger.info('Done in {} sec'.format(time.time() - start))

        logger.info(
            'Syncing campaign performance for {} campaigns.'
            .format(len(campaigns)))

        campaigns_done = 0

        for campaign in campaigns:
            sync_campaign_performance(state,
                                      access_token,
                                      account_id,
                                      campaign.get('id'))

            campaigns_done = campaigns_done + 1

            logger.info(
                '{}/{} campaigns synced.'
                .format(campaigns_done, len(campaigns)))

        has_more = False

    logger.info('Done!')


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

    access_token = generate_token(username, password)

    if access_token is None:
        logger.fatal("Failed to generate a new access token.")
        raise RuntimeError

    stitchstream.write_schema('campaigns', schemas.campaign)
    stitchstream.write_schema('campaign_performance',
                              schemas.campaign_performance)

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
