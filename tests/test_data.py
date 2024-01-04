from typing import Dict, Any

from capella_console_client.config import CATALOG_DEFAULT_LIMIT

import pytest


DUMMY_STAC_IDS = [
    "CAPELLA_C02_SM_GEO_HH_20210119154519_20210119154523",
    "CAPELLA_C02_SM_GEO_HH_20210119154529_20210119154533",
    "CAPELLA_C02_SM_GEO_HH_20210119154539_20210119154543",
    "CAPELLA_C02_SM_GEO_HH_20210119154549_20210119154553",
]


def create_mock_asset_hrefs(stac_id: str = DUMMY_STAC_IDS[0], polarization: str = "HH"):
    raster_href = f"https://test-data.capellaspace.com/capella-test/2021/1/19/{stac_id}/{stac_id}.png?AWSAccessKeyId=********&Expires=*****&Signature=******&x-amz-security-token=****"
    thumb_href = raster_href.replace(".png", "_thumb.png")
    return {polarization: {"href": raster_href}, "thumbnail": {"href": thumb_href}}


def create_mock_items_presigned(stac_id: str = DUMMY_STAC_IDS[0], polarization: str = "HH", product_type="GEO"):
    assets = create_mock_asset_hrefs(stac_id, polarization)
    return {"id": stac_id, "properties": {"sar:product_type": product_type}, "assets": assets}


TASK_1 = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-100.0000, 40.0000]},
    "properties": {
        "submissionTime": "2020-04-21T21:20:54.385Z",
        "taskingrequestId": "abc",
        "taskingrequestName": "TASKING_REQUEST_NAME",
        "taskingrequestDescription": "TASKING_REQUEST_DESCRIPTION",
        "userId": "MOCK_ID",
        "repeatrequestId": None,
        "windowOpen": "2020-04-21T22:18:57.936Z",
        "windowDuration": 604800,
        "windowClose": "2020-04-28T22:18:57.936Z",
        "collectionTier": "7_day",
        "archiveHoldback": "none",
        "statusHistory": [
            {
                "time": "2020-04-23T13:03:21.532Z",
                "code": "completed",
                "message": "Tasking request has been completed.",
            },
            {
                "time": "2020-04-22T15:30:08.756Z",
                "code": "accepted",
                "message": "Request can be completely satisfied during validity window.",
            },
            {
                "time": "2020-04-22T15:25:32.213Z",
                "code": "submitted",
                "message": "Request approved and submitted for scheduling",
            },
            {
                "time": "2020-04-22T03:06:55.485Z",
                "code": "completed",
                "message": "Tasking request has been completed.",
            },
            {
                "time": "2020-04-21T23:25:08.190Z",
                "code": "accepted",
                "message": "Request can be completely satisfied during validity window.",
            },
            {
                "time": "2020-04-21T23:21:26.214Z",
                "code": "submitted",
                "message": "Request submitted through automatic approval",
            },
            {
                "time": "2020-04-21T23:21:24.491Z",
                "code": "review",
                "message": "Tasking request ready for review.",
            },
            {
                "time": "2020-04-21T23:20:54.385Z",
                "code": "received",
                "message": "Request created",
            },
        ],
        "collectConstraints": {
            "lookDirection": "either",
            "ascDsc": "either",
            "orbitalPlanes": [],
            "localTime": [[0, 86400]],
            "offNadirMin": 25,
            "offNadirMax": 40,
            "collectMode": "spotlight",
            "imageLength": 5000,
            "grrMin": 0.5,
            "grrMax": 0.7,
            "azrMin": 0.5,
            "azrMax": 0.5,
            "neszMax": -10,
            "numLooks": 9,
        },
        "type": "spotlight",
        "preApproval": True,
        "transactionStatus": "in-progress",
        "sandbox": False,
        "order": {
            "summary": {"total": "$20.00", "subtotal": "$20.00"},
            "lineItems": [
                {
                    "taskId": "abc",
                    "accountingSize": {"unit": "sqkm", "value": 25},
                }
            ],
            "archiveHoldback": "none",
            "managedOrganizationIds": ["*"],
        },
    },
}

TASK_2 = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-100.0000, 40.0000]},
    "properties": {
        "submissionTime": "2021-01-21T21:20:54.385Z",
        "taskingrequestId": "def",
        "taskingrequestName": "TASKING_REQUEST_NAME",
        "taskingrequestDescription": "TASKING_REQUEST_DESCRIPTION",
        "userId": "MOCK_ID",
        "repeatrequestId": None,
        "windowOpen": "2021-01-21T22:18:57.936Z",
        "windowDuration": 604800,
        "windowClose": "2021-01-28T22:18:57.936Z",
        "collectionTier": "7_day",
        "archiveHoldback": "none",
        "statusHistory": [
            {
                "time": "2021-01-21T23:25:08.190Z",
                "code": "accepted",
                "message": "Request can be completely satisfied during validity window.",
            },
            {
                "time": "2021-01-21T23:21:26.214Z",
                "code": "submitted",
                "message": "Request submitted through automatic approval",
            },
            {
                "time": "2021-01-21T23:21:24.491Z",
                "code": "review",
                "message": "Tasking request ready for review.",
            },
            {
                "time": "2021-01-21T23:20:54.385Z",
                "code": "received",
                "message": "Request created",
            },
        ],
        "collectConstraints": {
            "lookDirection": "either",
            "ascDsc": "either",
            "orbitalPlanes": [],
            "localTime": [[0, 86400]],
            "offNadirMin": 25,
            "offNadirMax": 40,
            "collectMode": "spotlight",
            "imageLength": 5000,
            "grrMin": 0.5,
            "grrMax": 0.7,
            "azrMin": 0.5,
            "azrMax": 0.5,
            "neszMax": -10,
            "numLooks": 9,
        },
        "type": "spotlight",
        "preApproval": True,
        "transactionStatus": "in-progress",
        "sandbox": False,
        "order": {
            "summary": {"total": "$20.00", "subtotal": "$20.00"},
            "lineItems": [
                {
                    "taskId": "abc",
                    "accountingSize": {"unit": "sqkm", "value": 25},
                }
            ],
            "archiveHoldback": "none",
            "managedOrganizationIds": ["*"],
        },
    },
}

REPEAT_REQUEST = {
    "type": "Feature",
    "geometry": {"type": "Point", "coordinates": [-110.390625, 35.17380800000001]},
    "properties": {
        "submissionTime": "2023-09-08T17:35:26.171Z",
        "repeatrequestId": "PANDA",
        "repeatrequestName": "",
        "repeatrequestDescription": "",
        "orgId": "PANDA_ORG",
        "userId": "PANDA_USER",
        "windowDuration": 604800,
        "repetitionProperties": {
            "repeatStart": "2023-09-08T17:25:26.000Z",
            "repeatEnd": None,
            "repetitionInterval": 7,
            "repetitionCount": None,
            "maintainSceneFraming": False,
            "lookAngleTolerance": 10,
        },
        "collectionTier": "routine",
        "archiveHoldback": "1_year",
        "statusHistory": [{"time": "2023-09-08T17:35:26.172Z", "code": "received", "message": "Request created"}],
        "collectConstraints": {
            "lookDirection": "either",
            "ascDsc": "either",
            "orbitalPlanes": [],
            "localTime": [[0, 86400]],
            "offNadirMin": 25,
            "offNadirMax": 50,
            "elevationMin": 0,
            "elevationMax": 90,
            "imageLength": 5000,
            "imageWidth": 5000,
            "collectMode": "spotlight",
            "azimuth": None,
            "grrMin": 0.4,
            "grrMax": 0.7,
            "srrMin": 0.1,
            "srrMax": 10,
            "azrMin": 0.5,
            "azrMax": 0.5,
            "neszMax": -10,
            "numLooks": 9,
            "polarization": "HH",
            "prfMin": 5000,
            "radarParameters": {
                "prf": None,
                "bandwidth": 500000000,
                "centerFrequency": None,
                "upchirp": True,
                "method": "onboard",
                "ground_poly": None,
                "mode": None,
            },
            "duration": None,
            "prescribedCollectMidtime": None,
        },
        "billingEnvironment": "default",
        "parentRepeatrequest": None,
        "sandbox": True,
        "costPerImageEstimate": "$3,000.00",
        "processingConfig": None,
        "customAttribute1": None,
        "customAttribute2": None,
    },
}


# GET
def get_mock_responses(endpoint: str) -> Dict[str, Any]:
    return {
        "/user": {
            "id": "MOCK_ID",
            "organizationId": "MOCK_ORG_ID",
            "email": "MOCK_EMAIL",
        },
        "/orders": [
            {
                "userId": "MOCK_ID",
                "organizationId": "MOCK_ORG_ID",
                "orderDate": "2020-12-21T19:22:23.849Z",
                "expirationDate": "2020-12-21T20:22:23.849Z",
                "orderId": "1",
                "orderStatus": "completed",
                "items": [
                    {
                        "granuleId": "CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225",
                        "type": "stripmap",
                        "size": 100000000,
                        "collectionId": "capella-test",
                        "previouslyOrdered": False,
                        "collectionDate": "2020-11-27T02:06:41.304Z",
                    }
                ],
            }
        ],
        "/orders/review_success": {
            "authorized": True,
        },
        "/orders/review_insufficient_funds": {
            "authorized": False,
            "authorizationDenialReason": {
                "message": "This order will exceed your active contract period's value commitment. Order cost: $1,000.00; Available Commitment: $0.00}",
                "code": "AUTHORIZATION_INSUFFICIENT_FUNDS",
            },
        },
        "/orders/1/download": [
            {
                "assets": create_mock_asset_hrefs(),
                "id": DUMMY_STAC_IDS[0],
            }
        ],
        "/orders/2/download": [
            {
                "assets": create_mock_asset_hrefs(DUMMY_STAC_IDS[0]),
                "id": DUMMY_STAC_IDS[0],
            },
            {
                "assets": create_mock_asset_hrefs(DUMMY_STAC_IDS[1]),
                "id": DUMMY_STAC_IDS[1],
            },
        ],
        "/tasks/paged?page=1&limit=100&customerId=MOCK_ID": {
            "results": [TASK_1, TASK_2],
            "currentPage": 1,
            "totalPages": 1,
        },
        "/tasks/paged?page=1&limit=100&organizationId=MOCK_ORG_ID": {
            "results": [TASK_1, TASK_2],
            "currentPage": 1,
            "totalPages": 1,
        },
        "/task/abc": TASK_1,
        "/task/def": TASK_2,
        "/collects/list/abc": [
            {
                "center": [-100.0000, 40.0000, 400.0000],
                "centerEcef": [
                    1091094.4086499708,
                    -4846330.966449686,
                    3987158.899398989,
                ],
                "spacecraftId": 100,
                "collectId": "c1",
                "tileId": "t1",
                "tileGroupId": "tg1",
                "taskingrequestId": "abc",
                "repeatrequestId": None,
                "windowOpen": "2021-01-22T05:23:22.805Z",
                "windowClose": "2021-14-22T05:23:48.028Z",
                "windowDuration": 25.223843,
                "accessProperties": {
                    "ascdsc": "ascending",
                    "lookDirection": "left",
                    "localTime": 842,
                    "azimuthOpen": 161.79536059546896,
                    "azimuthClose": 134.4110657760598,
                    "elevationMin": 53.727022,
                    "elevationMax": 54.544628,
                    "offNadirMin": 32.341101,
                    "offNadirMax": 33.068666,
                },
                "collectProperties": {
                    "collectDuration": 25.223843519916645,
                    "imageLength": 5000,
                    "imageWidth": 5000,
                    "grr": 0.5171030232519721,
                    "azr": 0.5,
                    "bandwidth": None,
                    "nesz": -17.437903088007353,
                    "meanSquint": 0,
                    "polarization": "HH",
                },
                "collectStatusHistory": [
                    {
                        "time": "2021-02-03T13:03:20.122Z",
                        "code": "delivered",
                        "message": "The products have been processed and delivered",
                    },
                    {
                        "time": "2021-02-03T07:24:47.785Z",
                        "code": "qa",
                        "message": "Products awaiting QA before delivery",
                    },
                    {
                        "time": "2021-02-03T04:41:37.121Z",
                        "code": "processing",
                        "message": "Processing data from raw to higher level products",
                    },
                    {
                        "time": "2021-01-22T15:06:45.226Z",
                        "code": "delivered",
                        "message": "The products have been processed and delivered",
                    },
                    {
                        "time": "2021-01-22T08:04:23.197Z",
                        "code": "qa",
                        "message": "Products awaiting QA before delivery",
                    },
                    {
                        "time": "2021-01-22T07:08:10.007Z",
                        "code": "processing",
                        "message": "Processing data from raw to higher level products",
                    },
                    {
                        "time": "2021-01-22T06:22:33.423Z",
                        "code": "collected",
                        "message": "Known to have been collected on the spacecraft",
                    },
                    {
                        "time": "2021-01-22T00:50:10.408Z",
                        "code": "tasked",
                        "message": "Collection of image has been incorporated into a schedule and uplinked to spacecraft.",
                    },
                    {
                        "time": "2021-01-21T23:21:11.294Z",
                        "code": "predicted",
                        "message": "Collect created",
                    },
                ],
            }
        ],
    }[endpoint]


def get_canned_search_results_single_page() -> Dict[str, Any]:
    return {
        "features": [
            {
                "id": "CAPELLA_C02_SP_SLC_HH_20210422052316_20210422052318",
                "collection": "capella-archive",
            },
            {
                "id": "CAPELLA_C02_SP_GEC_HH_20210422052305_20210422052329",
                "collection": "capella-archive",
            },
            {
                "id": "CAPELLA_C02_SP_GEO_HH_20210422052305_20210422052329",
                "collection": "capella-archive",
            },
            {
                "id": "CAPELLA_C02_SP_SICD_HH_20210422052316_20210422052318",
                "collection": "capella-archive",
            },
        ],
        "numberMatched": 4,
    }


def get_canned_search_results_multi_page_page1() -> Dict[str, Any]:
    return {
        "features": [
            {
                "id": "CAPELLA_C02_SP_SLC_HH_20210422052316_20210422052318",
                "collection": "capella-archive",
            },
            {
                "id": "CAPELLA_C02_SP_GEC_HH_20210422052305_20210422052329",
                "collection": "capella-archive",
            },
        ],
        "numberMatched": 4,
        "links": [{"rel": "next", "href": "next_href?page=2"}],
    }


def get_canned_search_results_multi_page_page2() -> Dict[str, Any]:
    return {
        "features": [
            {
                "id": "CAPELLA_C02_SP_GEO_HH_20210422052305_20210422052329",
                "collection": "capella-archive",
            },
            {
                "id": "CAPELLA_C02_SP_SICD_HH_20210422052316_20210422052318",
                "collection": "capella-archive",
            },
        ],
        "numberMatched": 4,
        "links": [],
    }


def get_canned_search_results_with_collect_id() -> Dict[str, Any]:
    return {
        "features": [
            {
                "id": "CAPELLA_C02_SP_GEO_HH_20210422052305_20210422052329",
                "collection": "capella-archive",
                "properties": {"capella:collect_id": "0a4722dc-ff2a-4553-9f71-42dfdb99a39e"},
            },
            {
                "id": "CAPELLA_C02_SP_SICD_HH_20210422052316_20210422052318",
                "collection": "capella-archive",
                "properties": {"capella:collect_id": "0a4722dc-ff2a-4553-9f71-42dfdb99a39e"},
            },
        ],
        "numberMatched": 2,
        "links": [],
    }


def post_mock_responses(endpoint: str) -> Dict[str, Any]:
    return {
        "/token": {
            "accessToken": "MOCK_TOKEN",
            "refreshToken": "MOCK_REFRESH_TOKEN",
        },
        "/token/refresh": {
            "accessToken": "REFRESHED_MOCK_TOKEN",
            "refreshToken": "REFRESHED_MOCK_REFRESH_TOKEN",
        },
        "/submitOrder": {
            "userId": "MOCK_ID",
            "organizationId": "MOCK_ORG_ID",
            "orderDate": "2020-12-21T19:22:23.849Z",
            "expirationDate": "2020-12-21T20:22:23.849Z",
            "orderId": "1",
            "orderStatus": "completed",
            "items": [
                {
                    "granuleId": "CAPELLA_C02_SM_SLC_HH_20201126192221_20201126192225",
                    "type": "stripmap",
                    "size": 100000000,
                    "collectionId": "capella-test",
                    "previouslyOrdered": False,
                    "collectionDate": "2020-11-27T02:06:41.304Z",
                }
            ],
        },
        "/orders_rejected": {
            "orderId": "1",
            "userId": "MOCK_ID",
            "organizationId": "MOCK_ORG_ID1",
            "orderStatus": "rejected",
        },
        "/task": TASK_1,
        "/repeat-requests": REPEAT_REQUEST,
    }[endpoint]


def get_search_test_cases():
    # search_kwargs, expected payload, id
    return [
        pytest.param(
            dict(constellation="capella"),
            {"query": {"constellation": {"eq": "capella"}}, "limit": CATALOG_DEFAULT_LIMIT},
            id="constellation",
        ),
        pytest.param(dict(bbox=[1, 2, 3, 4]), {"bbox": [1, 2, 3, 4], "limit": CATALOG_DEFAULT_LIMIT}, id="bbox"),
        pytest.param(
            dict(
                constellation="capella",
                limit=1,
                bbox=[1, 2, 3, 4],
                instrument_mode="spotlight",
                product_type="GEO",
            ),
            {
                "limit": 1,
                "bbox": [1, 2, 3, 4],
                "query": {
                    "constellation": {"eq": "capella"},
                    "sar:instrument_mode": {"eq": "spotlight"},
                    "sar:product_type": {"eq": "GEO"},
                },
            },
            id="multi_filter",
        ),
        pytest.param(
            dict(constellation="other", doesnot="exist", nerf="!"),
            {"query": {"constellation": {"eq": "other"}}, "limit": CATALOG_DEFAULT_LIMIT},
            id="filter_invalid_kwargs",
        ),
        pytest.param(
            dict(constellation__INVALID="other"),
            {"limit": CATALOG_DEFAULT_LIMIT},
            id="invalid_op",
        ),
        pytest.param(
            dict(
                product_type=["SLC", "GEO"],
            ),
            {
                "query": {
                    "sar:product_type": {"in": ["SLC", "GEO"]},
                },
                "limit": CATALOG_DEFAULT_LIMIT,
            },
            id="in_implicit",
        ),
        pytest.param(
            dict(
                product_type__in=["SLC", "GEO"],
            ),
            {
                "query": {
                    "sar:product_type": {"in": ["SLC", "GEO"]},
                },
                "limit": CATALOG_DEFAULT_LIMIT,
            },
            id="in_explicit",
        ),
        pytest.param(
            dict(look_angle__gte=0.9, look_angle__lte=12.0),
            {
                "query": {"view:look_angle": {"gte": 0.9, "lte": 12.0}},
                "limit": CATALOG_DEFAULT_LIMIT,
            },
            id="gte_lte",
        ),
        pytest.param(
            dict(resolution_ground_range__gt=1, look_angle__lt=10),
            {
                "query": {
                    "capella:resolution_ground_range": {"gt": 1},
                    "view:look_angle": {"lt": 10},
                },
                "limit": CATALOG_DEFAULT_LIMIT,
            },
            id="gt_lt",
        ),
        # pytest.param(
        #     dict(platform__startsWith="cap"),
        #     {"query": {"platform": {"startsWith": "cap"},},},
        #     id="startsWith",
        # ),
        pytest.param(
            dict(sortby="id"),
            {
                "sortby": [{"field": "id", "direction": "asc"}],
                "limit": CATALOG_DEFAULT_LIMIT,
            },
            id="singleSortby",
        ),
        pytest.param(
            dict(sortby="-id"),
            {
                "sortby": [{"field": "id", "direction": "desc"}],
                "limit": CATALOG_DEFAULT_LIMIT,
            },
            id="singleSortbyDesc",
        ),
        pytest.param(
            dict(sortby=["-datetime", "+id"]),
            {
                "sortby": [
                    {"field": "properties.datetime", "direction": "desc"},
                    {"field": "id", "direction": "asc"},
                ],
                "limit": CATALOG_DEFAULT_LIMIT,
            },
            id="multiSortby",
        ),
        pytest.param(
            dict(sortby=["-datetime", "+id", "huffelpuff"]),
            {
                "sortby": [
                    {"field": "properties.datetime", "direction": "desc"},
                    {"field": "id", "direction": "asc"},
                ],
                "limit": CATALOG_DEFAULT_LIMIT,
            },
            id="multiSortbyOmits",
        ),
    ]
