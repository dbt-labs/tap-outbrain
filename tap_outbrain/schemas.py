link = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'string',
            'description': ('ID of this PromotedLink, i.e. '
                            '"00f4b02153ee75f3c9dc4fc128ab041962"')
        },
        'campaignId': {
            'type': 'string',
            'description': ('The ID of the campaign to which the '
                            'PromotedLink belongs, i.e. '
                            '"00f4b02153ee75f3c9dc4fc128ab041963"')
        },
        'text': {
            'type': 'string',
            'description': ('The text of the PromotedLink, i.e. "Google to '
                            'take over huge NASA hangar, give execs\' private '
                            'planes a home"'),
        },
        'lastModified': {
            'type': 'string',
            'format': 'date-time',
            'description': ('The time when the PromotedLink was last '
                            'modified, i.e. "2013-03-16T10:32:31Z"')
        },
        'creationTime': {
            'type': 'string',
            'format': 'date-time',
            'description': ('The time when the PromotedLink was created, '
                            'i.e. "2013-01-14T07:19:16Z"')
        },
        'url': {
            'type': 'string',
            'description': ('The URL visitors will be sent to upon clicking '
                            'the PromotedLink, i.e. "http://www.engadget.com'
                            '/2014/02/11/nasa-google-hangar-one/"')
        },
        'siteName': {
            'type': 'string',
            'description': ('The name of the publisher the PromotedLink '
                            'URL points to, i.e. "cnn.com"')
        },
        'sectionName': {
            'type': 'string',
            'description': ('The section name of the site the PromotedLink '
                            'URL points to, i.e. "Sports"')
        },
        'status': {
            'type': 'string',
            'description': ('The review status of the PromotedLink, '
                            'i.e. "PENDING"')
        },
        'cachedImageUrl': {
            'type': 'string',
            'description': ('The URL of the PromotedLink\'s image, cached '
                            'on Outbrain\'s servers, i.e. "http://images'
                            '.outbrain.com/imageserver/v2/s/gtE/n/plcyz/abc'
                            '/iGYzT/plcyz-f8A-158x110.jpg"')
        },
        'enabled': {
            'type': 'boolean',
            'description': ('Designates whether this PromotedLink will be '
                            'served.')
        },
        'archived': {
            'type': 'boolean',
            'description': ('Designates whether this PromotedLink is '
                            'archived.')
        },
        'documentLanguage': {
            'type': 'string',
            'description': ('The 2-letter code for the language of this '
                            'PromotedLink (via the PromotedLinks URL), '
                            'i.e. "EN"')
        },
        'cpc': {
            'type': 'number',
            'description': ('Cost per click, i.e. 0.58')
        }
    }
}


campaign = {
    'type': 'object',
    'properties': {
        'id': {
            'type': 'string',
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
            'description': ('The campaign ID plus the start date (day) '
                            'for this record.')
        },
        'fromDate': {
            'type': 'string',
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

link_performance = {
    'type': 'object',
    'properties': {
        'campaignId': {
            'type': 'string',
            'description': ('The campaign ID for this record.')
        },
        'linkId': {
            'type': 'string',
            'description': ('The link ID for this record.')
        },
        'fromDate': {
            'type': 'string',
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
