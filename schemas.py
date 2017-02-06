campaign = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'string',
            'key': True,
            'description': 'Campaign ID'
        },
        'name': {
            'type': 'string',
            'description': 'Campaign name'
        },
        'campaignOnAir': {
            'type': 'boolean',
            'description': ('Is the campaign on air, same as campaignOnAir '
                            'in Live Status')
        },
        'onAirReason': {
	    'type': 'string',
            'description': ('The reason for the campaign on air status, same '
                            'as onAirReason in Live Status')
        },
        'enabled': {
            'type': 'boolean',
            'description': 'Is the campaign enabled'
        },
        'budget': {
            'type': 'object',
            'description': ('Partial Budget entity of a campaign. For full '
                            'details use Budget'),
            'properties': {
                'id': {
	            'type': 'string',
                    'description': ('The id of this Budget, i.e. '
                                    '"00f4b02153ee75f3c9dc4fc128ab041962"')
                },
                'name': {
                    'type': 'string',
                    'description': ('The name of this Budget, i.e. '
                                    '"First quarter budget"'),
                },
                'shared': {
                    'type': 'boolean',
                    'description': ('Whether the Budget is shared between '
                                    'Campaigns, provided for convenience '
                                    'based on the number of Campaigns '
                                    'associated to this Budget, i.e. true')
                },
                'amount': {
                    'type': 'number',
                    'description': ('The monetary amount of this Budget, '
                                    'i.e. 2000.00')
                },
                'currency': {
                    'type': 'string',
                    'description': ('The currency denomination applied to the '
                                    'budget amount, i.e. "USD"')
                },
                'amountRemaining': {
                    'type': 'number',
                    'description': ('The unspent monetary amount remaining on '
                                    'this Budget, i.e. 150.00')
                },
                'amountSpent': {
                    'type': 'number',
                    'description': ('The spent monetary amount of this '
                                    'Budget, i.e. 1850.00')
                },
                'creationTime': {
                    'type': 'string',
                    'format': 'date-time',
                    'description': ('The time when this Budget was created, '
                                    'i.e. "2013-01-14 07:19:16"')
                },
                'lastModified': {
                    'type': 'string',
                    'format': 'date-time',
                    'description': ('The last modification date of this '
                                    'Budget, i.e. "2014-01-15 12:24:01"')
                },
                'startDate': {
                    'type': 'string',
                    'format': 'date',
                    'description': ('The date this Budget is scheduled to '
                                    'begin spending, i.e. "2014-01-15"')
                },
                'endDate': {
                    'type': 'string',
                    'format': 'date',
                    'description': ('The date this Budget is scheduled to '
                                    'stop spending. If runForever is true '
                                    'this will not be used. i.e. "2014-01-17"')
                },
                'runForever': {
                    'type': 'boolean',
                    'description': ('Designates whether the budged has an end '
                                    'date In case of true, "endDate" '
                                    'attribute will not be part of the '
                                    'Budgets attributes. i.e. true')
                },
                'type': {
                    'type': 'string',
                    'description': ('Controls on which period the Budget '
                                    'refreshes, i.e. "MONTHLY"')
                },
                'pacing': {
                    'type': 'string',
                    'description': ('Controls how fast the Budget will be '
                                    'spent, i.e. "AUTOMATIC"')
                },
                'dailyTarget': {
                    'type': 'number',
                    'description': ('The maximum amount of spend that is '
                                    'allowed per day. Relevant for '
                                    'DAILY_TARGET pacing. i.e. 100.00')
                },
                'maximumAmount': {
                    'type': 'number',
                    'description': ('The maximum amount allowed if defined, '
                                    'i.e. 100.00')
                }
            }
        },
        'cpc': {
            'type': 'number',
            'description': ('Cost per monetized user action (for example '
                            'cost per click). See Currencies for valid '
                            'cost values')
        }
    }
}


campaign_performance = {
    'type': 'object',
    'properties': {
        'campaignId': {
            'type': 'string',
            'key': True,
            'description': ('The campaign ID plus the start date (day) '
                            'for this record.')
        },
        'fromDate': {
            'type': 'string',
            'key': True,
            'format': 'date',
            'description': 'The start date for this record.'
        },
        'impressions': {
            'type': 'number',
            'description': ('Total number of PromotedLinks impressions across '
                            'the entire query range.'),
        },
        'clicks': {
            'type': 'number',
            'description': ('Total PromotedLinks clicks across the entire '
                            'query range.'),
        },
        'ctr': {
            'type': 'number',
            'description': ('The average CTR (Click Through Rate) percentage '
                            'across the entire query range (clicks / '
                            'impressions)/100.'),
        },
        'spend': {
            'type': 'number',
            'description': ('The total amount of money spent across the '
                            'entire query range.'),
        },
        'ecpc': {
            'type': 'number',
            'description': ('The effective (calculated) average CPC (Cost Per '
                            'Click) across the entire query range. '
                            'Calculated as: (spend / clicks)'),
        },
        'conversions': {
            'type': 'number',
            'description': ('The total number of conversions calculated '
                            'across the entire query range.')
        },
        'conversionRate': {
            'type': 'number',
            'description': ('The average rate of conversions per click '
                            'percentage across the entire query range. '
                            'Calculated as: (conversions / clicks)/100')
        },
        'cpa': {
            'type': 'number',
            'description': ('The average CPA (Cost Per Acquisition) '
                            'calculated across the entire query range. '
                            'Calculated as: (spend / conversions)')
        }
    }
}
