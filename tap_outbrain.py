#!/usr/bin/env python3

import argparse
import datetime
import dateutil.parser
import json
import os
import sys

import backoff
import requests
import stitchstream

import schemas

logger = stitchstream.get_logger()

BASE_URL = 'https://api.outbrain.com/amplify/v0.1'

BASE_URL = 'http://private-anon-8db7159ad4-amplifyv01.apiary-mock.com'

DEFAULT_STATE = {
    'campaign_performance': {}
}

DEFAULT_START_DATE = '2017-01-01'

REQUEST_COUNT = 0

def giveup(error):
    response = error.response
    return not (response.status_code == 429 or
                response.status_code >= 500)

@backoff.on_exception(backoff.expo,
                      (requests.exceptions.RequestException),
                      max_tries=5,
                      giveup=giveup,
                      factor=2,
                      base=15)
def request(url, access_token, params={}):
    global REQUEST_COUNT

    logger.debug("Making request: GET {} {}".format(url, params))

    response = requests.get(
        url,
        headers={'OB-TOKEN-V1': access_token},
        params=params)

    logger.debug("Got response code: {}".format(response.status_code))

    REQUEST_COUNT += 1
    response.raise_for_status()
    return response


def parse_datetime(datetime):
    dt = dateutil.parser.parse(datetime)

    # TODO the assumption is that the timestamp comes in in UTC, but that
    #      may not be true. verify w/ outbrain.
    return dt.isoformat('T') + 'Z'


def parse_campaign_performance(item, header, campaign_id):
    return {
        'campaignId': campaign_id,
        'fromDate': item.get('metadata', {}).get('fromDate'),
        'impressions': item.get('metrics', {}).get('impressions', 0),
        'clicks': item.get('metrics', {}).get('clicks', 0),
        'ctr': item.get('metrics', {}).get('ctr', 0.0),
        'spend': item.get('metrics', {}).get('spend', 0.0),
        'ecpc': item.get('metrics', {}).get('ecpc', 0.0),
        'conversions': item.get('metrics', {}).get('conversions', 0),
        'conversionRate': item.get('metrics', {}).get('conversionRate', 0.0),
        'cpa': item.get('metrics', {}).get('cpa', 0.0),
    }


def sync_campaign_performance(state, access_token, account_id, campaign_id):
    has_more = True
    from_date = state.get('campaign_performance', {}) \
                     .get(campaign_id, DEFAULT_START_DATE)
    params = {
        'campaignId': campaign_id,
        'from': from_date,
        'sort': '-from',
        'breakdown': 'daily',
        'limit': 100,
    }

    while has_more:
        response = request(
            '{}/reports/marketers/{}/periodic'.format(BASE_URL, account_id),
            access_token,
            params)

        logger.info(response.text)

        logger.info('Pulling campaign performance from {}'.format(from_date))
        response_body = response.json()

        header = response_body.get('metadata')
        items = response_body.get('metrics')

        campaign_performance = [
            parse_campaign_performance(item, header, campaign_id)
            for item in items]

        stitchstream.write_records('campaign_performance',
                                   campaign_performance)

        last_record = logger.info(campaign_performance[-1])
        logger.info(last_record)

        new_from_date = last_record.get('fromDate')
        state['campaign_performance'][campaign_id] = new_from_date
        stitchstream.write_state(state)
        from_date = new_from_date

        logger.info(response)
        has_more = False


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
        response = request(
            '{}/marketers/{}/campaigns'.format(BASE_URL, account_id),
            access_token, params)

        response_body = response.json()
        campaigns = response_body.get('campaigns', [])

        campaigns = [parse_campaign(campaign) for campaign in campaigns]

        for campaign in campaigns:
            sync_campaign_performance(state,
                                      access_token,
                                      account_id,
                                      campaign.get('id'))

        stitchstream.write_records('campaigns', campaigns)

        logger.info(response)
        has_more = False


def do_sync(args):
    state = DEFAULT_STATE

    with open(args.config) as config_file:
        config = json.load(config_file)

    access_token = config.get('access_token')
    account_id = config.get('account_id')

    if access_token is None:
        logger.fatal("Missing `access_token`.")
        raise RuntimeError

    if account_id is None:
        logger.fatal("Missing `account_id`.")
        raise RuntimeError

    stitchstream.write_schema('campaigns', schemas.campaign)
    stitchstream.write_schema('campaign_performance',
                              schemas.campaign_performance)

    sync_campaigns(state, access_token, account_id)


def do_check(args):
    pass


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()

    parser_check = subparsers.add_parser('check')
    parser_check.set_defaults(func=do_check)

    parser_sync = subparsers.add_parser('sync')
    parser_sync.set_defaults(func=do_sync)

    for subparser in [parser_check, parser_sync]:
        subparser.add_argument(
            '-c', '--config', help='Config file', required=True)
        subparser.add_argument(
            '-s', '--state', help='State file')

    args = parser.parse_args()

    if 'func' in args:
        args.func(args)
    else:
        parser.print_help()
        exit(1)

if __name__ == '__main__':
    main()
