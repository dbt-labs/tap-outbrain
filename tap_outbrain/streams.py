from tap_outbrain import schemas

link = {
    "tap_stream_id": "link",
    "key_properties": ["id"],
    "schema": schemas.link,
}

campaign = {
    "tap_stream_id": "campaign",
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
    link,
    campaign,
    campaign_performance,
    link_performance,
)
