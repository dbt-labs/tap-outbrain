from tap_outbrain import schemas

links = {
    "tap_stream_id": "links",
    "key_properties": ["id"],
    "schema": schemas.link,
}

campaigns = {
    "tap_stream_id": "campaigns",
    "key_properties": ["id"],
    "schema": schemas.campaign,
}


campaign_performance = {
    "tap_stream_id": "campaign_performance",
    "key_properties": ["campaignId", "fromDate"],
    "schema": schemas.campaign_performance,
}

link_performance = {
    "tap_stream_id": "link_performance",
    "key_properties": ["campaignId", "linkId", "fromDate"],
    "schema": schemas.link_performance,
}

STREAMS = (
    links,
    campaigns,
    campaign_performance,
    link_performance,
)
