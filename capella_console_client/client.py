import logging
import sys

from typing import List, Dict, Any, Union, Optional, no_type_check, Tuple
from collections import defaultdict
from pathlib import Path
import tempfile
from capella_console_client.s3 import S3Path

from capella_console_client.config import CONSOLE_API_URL
from capella_console_client.session import CapellaConsoleSession
from capella_console_client.logconf import logger
from capella_console_client.exceptions import (
    InsufficientFundsError,
    OrderRejectedError,
    NoValidStacIdsError,
    TaskNotCompleteError,
)
from capella_console_client.enumerations import ProductType, AssetType

from capella_console_client.assets import (
    _perform_download,
    DownloadRequest,
    _gather_download_requests,
    _get_asset_bytesize,
    _derive_stac_id,
    _filter_items_by_product_types,
)
from capella_console_client.search import StacSearch, SearchResult
from capella_console_client.tasking_request import get_tasking_requests, _task_contains_status, create_tasking_request
from capella_console_client.repeat_request import create_repeat_request
from capella_console_client.validate import (
    _validate_uuid,
    _validate_uuids,
    _validate_stac_id_or_stac_items,
    _validate_and_filter_product_types,
    _validate_and_filter_asset_types,
    _validate_and_filter_stac_ids,
)
from capella_console_client.sort import _sort_stac_items
from capella_console_client.order import get_order, get_non_expired_orders


class CapellaConsoleClient:
    """
    API client for https://api.capellaspace.com.

    API docs: https://docs.capellaspace.com/accessing-data/searching-for-data

    Args:
        api_key: api key for api.capellaspace.com
        token: JWT access token
        verbose: flag to enable verbose logging
        no_token_check: do not check if provided JWT token or API KEY is valid
        base_url: Capella console API base URL override
        search_url: Capella catalog/search/ override
        no_auth: bypass authentication

    NOTE:
        not providing either `api_key` (can be set by CAPELLA_API_KEY env) or `token`
        will prompt you for `api_key`, which is not what you want in a script

    NOTE: precedence order (high to low)
        1. API key
        2. JWT token

    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
        verbose: bool = False,
        no_token_check: bool = False,
        base_url: Optional[str] = CONSOLE_API_URL,
        search_url: Optional[str] = None,
        no_auth: bool = False,
    ):
        self._set_verbosity(verbose)
        self._sesh = CapellaConsoleSession(base_url=base_url, search_url=search_url, verbose=verbose)

        if not no_auth:
            self._sesh.authenticate(api_key, token, no_token_check)

    def _set_verbosity(self, verbose: bool = False):
        self.verbose = verbose
        logger.setLevel(logging.WARNING)
        if verbose:
            logger.setLevel(logging.INFO)

    # USER
    def whoami(self) -> Dict[str, Any]:
        """
        display user info

        Returns:
            Dict[str, Any]: return of GET /user
        """
        resp = self._sesh.get("/user")
        return resp.json()

    # TASKING
    def create_tasking_request(self, **kwargs):
        """
        Create a new tasking request

        Find more information at https://docs.capellaspace.com/constellation-tasking/tasking-requests

        Args:
            geometry: A GeoJSON representation of the area/point of interest. Must be either a polygon or point
            name: Can be used along with description to help characterize and describe the tasking request. Default: ""
            description: Can be used along with name to help characterize and describe the tasking request. Default: ""
            collection_type: The collection type sets the collect mode, number of looks, and resolutions for the resulting imagery. The available collection types can be found by submitting: GET https://api.capellaspace.com/collectiontypes
            collection_tier: Preference for data to be collected within a certain time after window_open. Can be one of "urgent", "priority", "standard", and "flexible". Default: "standard"
            window_open: Earliest time (in UTC) that you would like data to be collected. Default: Now
            window_close: Latest time (in UTC) that you would like data to be collected. Default: Seven days after window_open
            local_time: Times, in the timezone of the area where the image will be collected, during which the collect can be taken. Represented by a list of time ranges as seconds in the day. For example, [[21600, 64800]] would allow collects between 6 AM and 6 PM; [[0, 21600], [64800, 86400]] would allow collects between 6 PM and 12 AM as well as from 12 AM to 6 AM. Alternatively, you can pass string values of "day", "night", or "anytime" which are parsed to [[21600, 64800]], [[0, 21600], [64800, 86400]], and [[0, 86400]] respectively. Default: None
            product_types: List of analytics to add to the order along with the imagery. Currently available analytics are Vessel classification (VC), Default: None
            off_nadir_min: Minimum off-nadir angle permitted. Must be less than off_nadir_max. Default: None
            off_nadir_max: Maximum off-nadir angle permitted. Must be greater than off_nadir_min. Default: None
            image_width: Image width. Units: [m], Default: None
            orbital_planes: List of orbital planes allowed to service request. If empty any spacecraft in any plane can service request. One of 45, 53, 97. Default: None
            asc_dsc: Constraint on ascending/descending pass. One of "ascending", "descending", "either". Default: "either"
            look_direction: Constraint on view angle. One of "right", "left", "either". Default: "either"
            polarization: Image polarization. One of "HH", "VV". Default: None
            archive_holdback: If defined will specify a time period during which the resulting imagery will be kept from the publicly accessible archive. One of "none", "one_year", "thirty_day", "permanent". Default: "none"
            custom_attribute_1: Can be used along with custom_attribute_2 to help you track a Capella task with your own metadata or internal systems. Default: None
            custom_attribute_2: Can be used along with custom_attribute_1 to help you track a Capella task with your own metadata or internal systems. Default: None
            pre_approval: will skip the tasking request cost review step if set to true. Default: false
            azimuth_angle_min: clockwise angle with respect to North in a topocentric geodetic ENZ coordinate system from the target to the satellite. Default: None
            azimuth_angle_max: clockwise angle with respect to North in a topocentric geodetic ENZ coordinate system from the target to the satellite. Default: None
            squint: Determines if generated collects will be squinted. One of: enabled, forward, backward. Default: enabled for point requests, disabled for area requests
            max_squint_angle: max. allowed absolute squint angle when generating collects. Units: [degrees]. Default: None

        Returns:
            Dict[str, Any]: created tasking request metadata
        """
        return create_tasking_request(session=self._sesh, **kwargs)

    def list_tasking_requests(
        self, *tasking_request_ids: Optional[str], for_org: Optional[bool] = False, **kwargs: Optional[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        list/ search tasking requests

        Find more information at https://docs.capellaspace.com/constellation-tasking/tasking-requests

        Args:
            tasking_request_ids: list only specific tasking_request_ids (variadic, specify multiple)
            for_org: list all tasking requests of your organization (instead of only yours) - **requires** organization index/ admin permission

        additionally the following search filters are supported:

         • status: TaskingRequestStatus, one of received, review, submitted, active, accepted, rejected, expired, completed, anomaly, canceled, error, failed
         • submission_time__gt: datetime, e.g. datetime.datetime(2022, 12, 9, 21)


        Returns:
            List[Dict[str, Any]]: metadata of tasking requests
        """
        return get_tasking_requests(*tasking_request_ids, session=self._sesh, for_org=for_org, **kwargs)

    def get_task(self, tasking_request_id: str) -> Dict[str, Any]:
        """
        fetch task for the specified `tasking_request_id`

        Args:
            tasking_request_id: tasking request UUID

        Returns:
            Dict[str, Any]: task metadata
        """
        task_response = self._sesh.get(f"/task/{tasking_request_id}")
        return task_response.json()

    def is_task_completed(self, task: Dict[str, Any]) -> bool:
        """
        check if a task has completed
        """
        return _task_contains_status(task, "completed")

    def get_collects_for_task(self, tasking_request_id: str) -> List[Dict[str, Any]]:
        """
        get all the collects associated with this task (see :py:meth:`get_task()`)

        Args:
            task: task metadata - return of :py:meth:`get_task()`

        Returns:
            List[Dict[str, Any]]: collect metadata associated
        """
        task = self.get_task(tasking_request_id)
        tasking_request_id = task["properties"]["taskingrequestId"]
        if not self.is_task_completed(task):
            raise TaskNotCompleteError(f"TaskingRequest<{tasking_request_id}> is not in completed state")

        collects_list_resp = self._sesh.get(f"/collects/list/{tasking_request_id}")

        return collects_list_resp.json()

    # REPEAT REQUESTS
    def create_repeat_request(self, **kwargs):
        """
        Create a new repeat request

        Find more information at https://docs.capellaspace.com/constellation-tasking/tasking-requests

        Args:
            geometry: A GeoJSON representation of the area/point of interest. Must be either a polygon or point
            name: Can be used along with description to help characterize and describe the tasking request. Default: ""
            description: Can be used along with name to help characterize and describe the tasking request. Default: ""
            collection_tier: Preference for data to be collected within a certain time after window_open. Can be either "flexible" or "routine". Default: "routine"
            collection_type: The collection type sets the collect mode, number of looks, and resolutions for the resulting imagery. The available collection types can be found by submitting: GET https://api.capellaspace.com/collectiontypes
            repeat_start: Starting date (in UTC) when you would like data to begin being collected. Default: Now
            repeat_end: Starting date (in UTC) when you would like data to stop being collected. This and repetition_count are mutually exclusive; only one of them can be defined per request. Default: None
            repetition_interval: Number of days between the start of each derived request. Default: 7
            repetition_count: Total number of acquisitions in the repeat series. This and repeat_end are mutually exclusive; only one of them can be defined per request. Default: None
            local_time: Times, in the timezone of the area where the image will be collected, during which the collect can be taken. Represented by a list of time ranges as seconds in the day. For example, [[21600, 64800]] would allow collects between 6 AM and 6 PM; [[0, 21600], [64800, 86400]] would allow collects between 6 PM and 12 AM as well as from 12 AM to 6 AM. Alternatively, you can pass string values of "day", "night", or "anytime" which are parsed to [[21600, 64800]], [[0, 21600], [64800, 86400]], and [[0, 86400]] respectively. Default: None
            product_types: List of analytics to add to the order along with the imagery. Currently available analytics are Vessel classification (VC), Default: None
            off_nadir_min: Minimum off-nadir angle permitted. Must be less than off_nadir_max. Default: None
            off_nadir_max: Maximum off-nadir angle permitted. Must be greater than off_nadir_min. Default: None
            image_width: Image width. Units: [m], Default: None
            orbital_planes: List of orbital planes allowed to service request. If empty any spacecraft in any plane can service request. One of 45, 53, 97. Default: None
            asc_dsc: Constraint on ascending/descending pass. One of "ascending", "descending", "either". Default: "either"
            look_direction: Constraint on view angle. One of "right", "left", "either". Default: "either"
            polarization: Image polarization. One of "HH", "VV". Default: None
            archive_holdback: If defined will specify a time period during which the resulting imagery will be kept from the publicly accessible archive. One of "none", "one_year", "thirty_day", "permanent". Default: "none"
            custom_attribute_1: Can be used along with custom_attribute_2 to help you track a Capella task with your own metadata or internal systems. Default: None
            custom_attribute_2: Can be used along with custom_attribute_1 to help you track a Capella task with your own metadata or internal systems. Default: None
            azimuth_angle_min: clockwise angle with respect to North in a topocentric geodetic ENZ coordinate system from the target to the satellite. Default: None
            azimuth_angle_max: clockwise angle with respect to North in a topocentric geodetic ENZ coordinate system from the target to the satellite. Default: None
            squint: Determines if generated collects will be squinted. One of: enabled, forward, backward. Default: enabled for point requests, disabled for area requests
            max_squint_angle: max. allowed absolute squint angle when generating collects. Units: [degr

        Returns:
            Dict[str, Any]: created repeat request metadata
        """
        return create_repeat_request(session=self._sesh, **kwargs)

    # ORDER
    def list_orders(self, *order_ids: Optional[str], is_active: Optional[bool] = False) -> List[Dict[str, Any]]:
        """
        list orders

        Args:
            order_id: list only specific orders (variadic, specify multiple) - if omitted all orders are listed
            is_active: list only active (non-expired) orders

        Returns:
            List[Dict[str, Any]]: metadata of orders
        """

        if order_ids:
            _validate_uuids(order_ids)

        # prefilter non expired
        if is_active:
            orders = get_non_expired_orders(session=self._sesh)
            if order_ids:
                orders = [o for o in orders if o["orderId"] in set(order_ids)]
            return orders

        # list specific orders
        if order_ids:
            orders = [self._sesh.get(f"/orders/{order_id}").json() for order_id in order_ids]
            return orders

        # list all orders of customer
        params = {
            "customerId": self._sesh.customer_id,
        }
        resp = self._sesh.get("/orders", params=params)
        orders = resp.json()
        return orders

    def get_stac_items_of_order(self, order_id: str, ids_only: bool = False) -> Union[List[str], SearchResult]:
        """
        get stac items of an existing order

        Args:
            order_id: order id
        """
        _validate_uuid(order_id)
        order_meta = self.list_orders(order_id)[0]

        stac_ids = [item["granuleId"] for item in order_meta["items"]]
        if ids_only:
            return stac_ids

        return self.search(ids=stac_ids)

    def review_order(
        self,
        stac_ids: Optional[List[str]] = None,
        items: Optional[Union[List[Dict[str, Any]], SearchResult]] = None,
        contract_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        stac_ids = _validate_stac_id_or_stac_items(stac_ids, items)
        logger.info(f"reviewing order for {', '.join(stac_ids)}")

        stac_items = items  # type: ignore
        if not items:
            stac_items = self.search(ids=stac_ids)

        if not stac_items:
            raise NoValidStacIdsError(f"No valid STAC IDs in {', '.join(stac_ids)}")

        # review order
        order_payload = self._construct_order_payload(stac_items, contract_id)
        review_order_response = self._sesh.post("/orders/review", json=order_payload).json()

        if not review_order_response.get("authorized", False):
            raise InsufficientFundsError(review_order_response["authorizationDenialReason"]["message"])
        return review_order_response

    def submit_order(
        self,
        stac_ids: Optional[List[str]] = None,
        items: Optional[Union[List[Dict[str, Any]], SearchResult]] = None,
        check_active_orders: bool = False,
        omit_search: bool = False,
        omit_review: bool = False,
        contract_id: Optional[str] = None,
    ) -> str:
        """
        submit an order by `stac_ids` or `items`.

        NOTE: Precedence order (high to low)
            1. stac_ids
            2. items

        Args:
            stac_ids: STAC IDs that active order should include
            items: STAC items, returned by :py:meth:`search`
            check_active_orders: check if any active order containing ALL `stac_ids` is available
                if True: returns that order ID
                if False: submits a new order and returns new order ID
            omit_search: omit search to ensure provided STAC IDs are valid - only works if `items` are provided
            omit_review: omit review stage
            contract_id: charge order on explicit contract (if omitted default contract is used)
            Returns:
                str: order UUID
        """
        stac_ids = _validate_stac_id_or_stac_items(stac_ids, items)

        if check_active_orders:
            order_id = get_order(session=self._sesh, stac_ids=stac_ids)
            if order_id is not None:
                logger.info(f"found existing order {order_id} containing all requested stac ids")
                return order_id

        def _get_stac_items():
            if stac_ids and not omit_search:
                stac_items = self.search(ids=stac_ids)
            else:
                if omit_search and not items:
                    logger.warning(
                        "setting omit_search=True only works in combination providing items instead of stac_ids"
                    )
                    stac_items = self.search(ids=stac_ids)
                else:
                    stac_items = items  # type: ignore

            if not stac_items:
                raise NoValidStacIdsError(f"No valid STAC IDs in {', '.join(stac_ids)}")

            return stac_items

        stac_items = _get_stac_items()

        if not omit_review:
            self.review_order(items=stac_items, contract_id=contract_id)

        logger.info(f"submitting order for {', '.join(stac_ids)}")
        order_payload = self._construct_order_payload(stac_items, contract_id)
        res_order = self._sesh.post("/orders", json=order_payload)

        con = res_order.json()
        order_id = con["orderId"]
        if con["orderStatus"] == "rejected":
            raise OrderRejectedError(f"Order for {', '.join(stac_ids)} rejected.")

        logger.info(f"successfully submitted order {order_id}")
        return order_id  # type: ignore

    def _construct_order_payload(self, stac_items, contract_id: Optional[str] = None):
        by_collect_id = defaultdict(list)
        for item in stac_items:
            by_collect_id[item["collection"]].append(item["id"])

        order_items = []
        for collection, stac_ids_of_coll in by_collect_id.items():
            order_items.extend([{"collectionId": collection, "granuleId": stac_id} for stac_id in stac_ids_of_coll])

        payload = {"items": order_items}
        if contract_id:
            payload["contractId"] = contract_id  # type: ignore

        return payload

    def get_presigned_items(
        self,
        order_id: str,
        stac_ids: Optional[List[str]] = None,
        sort_by: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        get presigned items hrefs for all products contained in order

        Args:
            order_id: active order ID (see :py:meth:`submit_order`)
            stac_ids: filter presigned assets by STAC IDs
            sort_by: list of stac ids to sort by

        Returns:
            List[Dict[str, Any]]: List of assets of respective product, e.g.

            .. highlight:: python
            .. code-block:: python

                [
                    {
                        "<asset_type>": {
                            "title": ...,
                            "href": ...,
                            "type": ...
                        },
                        ...
                    }
                ]

        """

        _validate_uuid(order_id)

        logger.info(f"getting presigned items for order {order_id}")
        response = self._sesh.get(f"/orders/{order_id}/download")

        presigned_stac_items = response.json()

        # ensure sort
        sort_by = _validate_and_filter_stac_ids(sort_by)
        if sort_by:
            presigned_stac_items = _sort_stac_items(items=presigned_stac_items, stac_ids=sort_by)

        # no filter
        if not stac_ids:
            return presigned_stac_items

        stac_ids_set = set(stac_ids)
        return [item for item in presigned_stac_items if item["id"] in stac_ids_set]

    def get_presigned_assets(
        self,
        order_id: str,
        stac_ids: Optional[List[str]] = None,
        sort_by: Optional[List[str]] = None,
        assets_only: Optional[bool] = True,
    ) -> List[Dict[str, Any]]:
        """
        get presigned assets hrefs for all products contained in order

        Args:
            order_id: active order ID (see :py:meth:`submit_order`)
            stac_ids: filter presigned assets by STAC IDs
            sort_by: list of stac ids to sort by

        Returns:
            List[Dict[str, Any]]: List of assets of respective product, e.g.

            .. highlight:: python
            .. code-block:: python

                [
                    {
                        "<asset_type>": {
                            "title": ...,
                            "href": ...,
                            "type": ...
                        },
                        ...
                    }
                ]

        """
        if not assets_only:
            logger.warning(
                "`assets_only` is kept for backwards compatibility but has no effect. Please use `get_presigned_items` instead"
            )
        items_presigned = self.get_presigned_items(order_id, stac_ids, sort_by)
        return [item["assets"] for item in items_presigned]

    def get_asset_bytesize(self, pre_signed_url: str) -> int:
        """get size in bytes of `pre_signed_url`"""
        return _get_asset_bytesize(pre_signed_url)

    # DOWNLOAD
    def download_asset(
        self,
        pre_signed_url: str,
        local_path: Union[Path, str] = None,
        override: bool = False,
        show_progress: bool = False,
    ) -> Union[Path, S3Path]:
        """
        downloads a presigned asset url to disk

        Args:
            pre_signed_url: presigned asset url, see :py:meth:`get_presigned_items`
            local_path: local output path - file is written to OS's temp dir if not provided
            override: override already existing `local_path`
            show_progress: show download status progressbar
        """
        dl_request = DownloadRequest(
            url=pre_signed_url,
            local_path=local_path,  # type: ignore
            asset_key="asset",
        )
        return _perform_download(
            download_requests=[dl_request],
            override=override,
            threaded=False,
            show_progress=show_progress,
        )["asset"]

    def download_products(
        self,
        items_presigned: Optional[List[Dict[str, Any]]] = None,
        order_id: Optional[str] = None,
        tasking_request_id: Optional[str] = None,
        collect_id: Optional[str] = None,
        local_dir: Union[Path, S3Path, str] = Path(tempfile.gettempdir()),
        include: Union[List[Union[str, AssetType]], str] = None,
        exclude: Union[List[Union[str, AssetType]], str] = None,
        override: bool = False,
        threaded: bool = True,
        show_progress: bool = False,
        separate_dirs: bool = True,
        product_types: List[Union[str, ProductType]] = None,
        contract_id: Optional[str] = None,
    ) -> Dict[str, Dict[str, Path]]:
        """
        download all assets of multiple products

        Args:
            items_presigned: stac items with presigned assets, see :py:meth:`get_presigned_items`
            order_id: optionally provide `order_id` instead of `assets_presigned`, see :py:meth:`submit_order`
            tasking_request_id: tasking request UUID of the task request you wish to download all associated products for
            collect_id: collect UUID you wish to download all associated products for

                    NOTE: Precedence order (high to low)
                      1. items_presigned
                      2. order_id
                      3. tasking_request_id
                      4. collect_id

                    Meaning e.g. assets_presigned takes precedence over order_id, ...

            local_dir: Path where assets are saved to, tempdir if not provided
            include: white-listing, which assets should be included, e.g. ["HH"] => only download HH asset
            exclude: black-listing, which assets should be excluded, e.g. ["HH", "thumbnail"] => download ALL except HH and thumbnail assets

                     NOTE: explicit DENY overrides explicit ALLOW

                     asset choices:
                        * 'HH', 'VV', 'raster', 'metadata', 'thumbnail' (external) - raster == 'HH' || 'VV'
                        * 'log', 'profile', 'stats', 'stats_plots' (internal)

            override: override already existing
            threaded: download assets of product in multiple threads
            show_progress: show download status progressbar
            separate_dirs: set to True in order to save the respective product assets into products directories, i.e.
                                /tmp/<stac_id_1>/<stac_id_1>.tif
                                /tmp/<stac_id_2>/<stac_id_2>.tif
                                ...
                            set to False in order to the respective product assets directly into the provided `local_dir`, i.e.
                               /tmp/<stac_id_1>.tif
                               /tmp/<stac_id_2>.tif
                               ...
            product_types: filter by product type, e.g. ["SLC", "GEO"]
            contract_id: charge order on explicit contract (if omitted default contract is used)

        Returns:
            Dict[str, Dict[str, Path]]: Local paths of downloaded files keyed by STAC id and asset type, e.g.

            .. highlight:: python
            .. code-block:: python

                {
                    "stac_id_1": {
                        "<asset_type>": <path-to-asset>,
                        ...
                    }
                }
        """

        one_of_required = (items_presigned, order_id, tasking_request_id, collect_id)

        if not any(map(bool, one_of_required)):
            raise ValueError("please provide one of assets_presigned, order_id, tasking_request_id or collect_id")

        product_types = _validate_and_filter_product_types(product_types)
        include = _validate_and_filter_asset_types(include)
        exclude = _validate_and_filter_asset_types(exclude)

        if not items_presigned:
            items_presigned = self._resolve_items_presigned(
                order_id, tasking_request_id, collect_id, product_types, contract_id
            )

        len_items_presigned = len(items_presigned)
        suffix = "s" if len_items_presigned > 1 else ""

        # filter product_type
        if product_types:
            items_presigned = _filter_items_by_product_types(items_presigned, product_types)
        logger.info(f"downloading {len_items_presigned} product{suffix}")

        # gather download requests
        download_requests = []
        by_stac_id = {}
        for cur_item in items_presigned:
            cur_download_requests = _gather_download_requests(
                cur_item["assets"], local_dir, include, exclude, separate_dirs
            )
            by_stac_id[cur_download_requests[0].stac_id] = {
                cur.asset_key: cur.local_path for cur in cur_download_requests
            }
            download_requests.extend(cur_download_requests)

        if not download_requests:
            logger.warning("Nothing to download")
            return by_stac_id  # type: ignore

        # download
        _perform_download(
            download_requests=download_requests,
            override=override,
            threaded=threaded,
            show_progress=show_progress,
        )
        return by_stac_id  # type: ignore

    def _resolve_items_presigned(
        self,
        order_id: Optional[str] = None,
        tasking_request_id: Optional[str] = None,
        collect_id: Optional[str] = None,
        product_types: List[str] = None,
        contract_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        stac_ids = None

        # 1 - resolve assets_presigned from order_id
        if order_id:
            _validate_uuid(order_id)
        else:
            # 2 - submit order for tasking_request_id
            if tasking_request_id:
                _validate_uuid(tasking_request_id)
                order_id, stac_ids = self._order_products_for_task(tasking_request_id, product_types, contract_id)  # type: ignore
            # 3 - submit order for collect_id
            else:
                _validate_uuid(collect_id)
                order_id, stac_ids = self._order_products_for_collect_ids(
                    collect_ids=[collect_id], product_types=product_types, contract_id=contract_id  # type: ignore
                )

        return self.get_presigned_items(order_id, stac_ids)  # type: ignore

    def _order_products_for_task(
        self, tasking_request_id: str, product_types: List[str] = None, contract_id: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        """
        order all products associated with a tasking request

        Args:
            tasking_request_id: tasking request UUID you wish to order all associated products for
        """
        # gather up all collect IDs associated of this task
        collect_ids = [coll["collectId"] for coll in self.get_collects_for_task(tasking_request_id)]
        return self._order_products_for_collect_ids(collect_ids, product_types)

    def _order_products_for_collect_ids(
        self, collect_ids: List[str], product_types: List[str] = None, contract_id: Optional[str] = None
    ) -> Tuple[str, List[str]]:
        search_kwargs = dict(
            collect_id__in=collect_ids,
        )
        if product_types:
            search_kwargs["product_type__in"] = product_types

        result = self.search(**search_kwargs)
        if not result:
            logger.warning("No STAC items found ... aborting")
            sys.exit(0)

        order_id = self.submit_order(items=result, omit_search=True, check_active_orders=True, contract_id=contract_id)
        return order_id, result.stac_ids

    def download_product(
        self,
        assets_presigned: Optional[Dict[str, Any]] = None,
        order_id: Optional[str] = None,
        local_dir: Union[Path, S3Path, str] = Path(tempfile.gettempdir()),
        include: Union[List[Union[str, AssetType]], str] = None,
        exclude: Union[List[Union[str, AssetType]], str] = None,
        override: bool = False,
        threaded: bool = True,
        show_progress: bool = False,
    ) -> Dict[str, Union[Path, S3Path]]:
        """
        download all assets of a product (TO BE DEPRECATED)

        Args:
            assets_presigned: mapping of presigned assets of multiple products, see :py:meth:`get_presigned_assets`
            order_id: optionally provide `order_id` instead of `assets_presigned`, see :py:meth:`submit_order`

                NOTE: Precedence order (high to low)
                  1. assets_presigned
                  2. order_id

            local_dir: Path where assets are saved to, tempdir if not provided
            include: white-listing, which assets should be included, e.g. ["HH"] => only download HH asset
            exclude: black-listing, which assets should be excluded, e.g. ["HH", "thumbnail"] => download ALL except HH and thumbnail assets
                     NOTE: explicit DENY overrides explicit ALLOW

                     asset choices:
                        * 'HH', 'VV', 'raster', 'metadata', 'thumbnail' (external)
                           Note: raster == 'HH' || 'VV'
                        * 'log', 'profile', 'stats', 'stats_plots' (internal accessible only)

            override: override already existing
            threaded: download assets of product in multiple threads
            show_progress: show download status progressbar

        Returns:
            Dict[str, Path]: Local paths of downloaded files keyed by asset type, e.g.

            .. highlight:: python
            .. code-block:: python

                {
                    "<asset_type>": <path-to-asset>,
                    ...
                }
        """
        logger.warning("this method will be deprecated in future revisions. Please use `download_products` instead.")
        if not assets_presigned and not order_id:
            raise ValueError("please provide either assets_presigned or order_id")

        if not assets_presigned:
            _validate_uuid(order_id)
            assets_presigned = self._get_first_presigned_from_order(order_id)

        include = _validate_and_filter_asset_types(include)
        exclude = _validate_and_filter_asset_types(exclude)
        download_requests = _gather_download_requests(assets_presigned, local_dir, include, exclude)  # type: ignore

        if not download_requests:
            logger.warning("Nothing to download")
            return {}

        return _perform_download(
            download_requests=download_requests,
            override=override,
            threaded=threaded,
            show_progress=show_progress,
        )

    @no_type_check
    def _get_first_presigned_from_order(self, order_id: str) -> Dict[str, Any]:
        assets_presigned = self.get_presigned_assets(order_id)
        if len(assets_presigned) > 1:
            logger.warning(
                f"order {order_id} contains {len(assets_presigned)} products - using first one ({_derive_stac_id(assets_presigned)})"
            )

        return assets_presigned[0]

    # SEARCH
    def search(self, **kwargs) -> SearchResult:
        """
        paginated search for up to 500 matches (if no bigger limit specified)

        Find more information at https://docs.capellaspace.com/accessing-data/searching-for-data

        supported search filters:

         • azimuth_angle: float, e.g. 123.4
         • bbox: List[float, float, float, float], e.g. [12.35, 41.78, 12.61, 42]
         • billable_area: Billable Area in m^2
         • center_frequency: Union[int, float], Center Frequency (GHz)
         • collections: List[str], e.g. ["capella-open-data"]
         • collect_id: str, capella internal collect-uuid, e.g. "78616ccc-0436-4dc2-adc8-b0a1e316b095"
         • collection_type: str, capella collection type, e.g. "spotlight_ultra"
         • constellation: str, e.g. "capella"
         • datetime: str, e.g. "2020-02-12T00:00:00Z"
         • epsg: int, e.g. 32648
         • frequency_band: str, Frequency band, one of "P", "L", "S", "C", "X", "Ku", "K", "Ka"
         • ids: List[str], e.g. `["CAPELLA_C02_SP_GEO_HH_20201109060434_20201109060437"]`
         • image_formation_algorithm: str, Image Formation Algorithm, one of "pfa", "backprojection"
         • intersects: geometry component of the GeoJSON, e.g. {'type': 'Point', 'coordinates': [-113.1, 51.1]}
         • incidence_angle: Union[int, float], Center incidence angle, between 0 and 90
         • instruments: List[str], leveraged instruments, e.g. ["capella-radar-5"]
         • instrument_mode: str, Instrument mode, one of "spotlight", "stripmap", "sliding_spotlight"
         • limit: int, default: 500
         • layover_angle: str, e.g. -0.1
         • local_datetime: str, local datetime, e.g. 2022-12-12TT07:37:42.324551+0800
         • local_time: str, local time, e.g. 07:37:42.324551
         • local_timezone: str, local timezone, e.g. Asia/Shanghai
         • look_angle: Union[int, float], e.g. 28.4
         • looks_azimuth: int, e.g. 5
         • looks_equivalent_number: int, Equivalent number of looks (ENL), e.g. 3
         • looks_range: int, e.g. 5
         • observation_direction: str, Antenna pointing direction, one of "right", "left"
         • orbit_state: str, Orbit State, one of "ascending", "descending"
         • orbital_plane: int, Orbital Plane, inclination angle of orbit
         • pixel_spacing_azimuth: Union[int, float], Pixel spacing azimuth (m), e.g. 0.5
         • pixel_spacing_range: Union[int, float], Pixel spacing range (m), e.g. 0.5
         • platform: str, e.g. "capella-2"
         • polarizations: str, one of "HH", "VV", "HV", "VH"
         • product_type: str, one of "SLC", "GEO"
         • resolution_azimuth: float, Resolution azimuth (m), e.g. 0.5
         • resolution_ground_range: float, Resolution ground range (m), e.g. 0.5
         • resolution_range: float, Resolution range (m), e.g. 0.5
         • squint_angle: float, Squint angle, e.g. 30.1
         • ownership: str, one of "ownedByOrganization", "sharedWithOrganization", "availableForPurchase", "publiclyAvailable"

        supported operations:
         • eq: equality search
         • in: within group
         • gt: greater than
         • gte: greater than equal
         • lt: lower than
         • lte: lower than equal

        sorting:
         • sortby: List[str] - must be supported fields, e.g. ["+datetime"]


        Returns:
            List[Dict[str, Any]]: STAC items matched
        """
        search = StacSearch(session=self._sesh, **kwargs)
        return search.fetch_all()
