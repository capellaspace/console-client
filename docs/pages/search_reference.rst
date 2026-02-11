.. _search_reference:

*******************
Search Query Syntax
*******************


.. _stac-query-fields:

catalog search
##############

.. list-table:: supported query fields for catalog search
    :widths: 30 40 20 20
    :header-rows: 1

    * - field name
      - description
      - type
      - example
    * - ``azimuth_angle``
      - azimuth angle (°), between 0 and 360
      - ``Union[int, float]``
      - ``196.5``
    * - ``bbox``
      - bounding box
      - ``List[float, float, float, float]``
      - ``[12.35, 41.78, 12.61, 42]``
    * - ``billable_area``
      - billable Area (m^2)
      - ``int``
      - ``100000000``
    * - ``center_frequency``
      - center Frequency (GHz)
      - ``Union[int, float]``
      - ``9.65``
    * - ``collections``
      - STAC collections
      - ``List[str]``
      - ``["capella-open-data"]``
    * - ``collection_type``
      - | Capella collection type, one of
        | ``"spotlight_ultra"``, ``"spotlight"``,
        | ``"stripmap_100"``, ``"stripmap_50"``, ``"stripmap_20"``
      - ``str``
      - ``"spotlight_ultra"``
    * - ``collect_id``
      - capella internal collect-uuid
      - ``str``
      - ``"78616ccc-0436-4dc2-adc8-b0a1e316b095"``
    * - ``constellation``
      - constellation identifier
      - ``str``
      - ``"capella"``
    * - ``datetime``
      - mid time of collect in Zulu format
      - ``str``
      - ``"2020-02-12T00:00:00Z"``
    * - ``epsg``
      - EPSG code of the datasource
      - ``int``
      - ``32648``
    * - ``frequency_band``
      - frequency band
      - ``str``
      - ``"X"``
    * - ``ids``
      - STAC identifiers (unique product identifiers)
      - ``List[str]``
      - ``["CAPELLA_C02_SP_GEO_HH_20201109060434_20201109060437"]``
    * - ``image_formation_algorithm``
      - | Image formation algorithm
        | ``"backprojection"``, ``"pfa"``
      - ``str``
      - ``backprojection``
    * - ``intersects``
      - geometry component of GeoJSON
      - ``geometryGeoJSON``
      - ``{'type': 'Point', 'coordinates': [-113.1, 51.1]}``
    * - ``incidence_angle``
      - center incidence angle (°), between 0 and 90
      - ``Union[int, float]``
      - ``31``
    * - ``instruments``
      - leveraged instruments
      - ``List[str]``
      - ``["capella-radar-5"]``
    * - ``instrument_mode``
      - | instrument mode, one of
        | ``"spotlight"``, ``"stripmap"``, ``"sliding_spotlight"``
      - ``str``
      - ``"spotlight"``
    * - ``layover_angle``
      - layover angle (°)
      - ``float``
      - ``-0.1``
    * - ``local_datetime``
      - local datetime
      - ``str``
      - ``2022-12-12TT07:37:42.324551+0800``
    * - ``local_time``
      - local time
      - ``str``
      - ``07:37:42.324551``
    * - ``local_timezone``
      - time zone
      - ``str``
      - ``Asia/Shanghai``
    * - ``look_angle``
      - look angle (°)
      - ``Union[int, float]``
      - ``28.4``
    * - ``looks_azimuth``
      - looks in azimuth
      - ``int``
      - ``7``
    * - ``looks_equivalent_number``
      - equivalent number of looks (ENL)
      - ``int``
      - ``7``
    * - ``looks_range``
      - looks in range
      - ``int``
      - ``1``
    * - ``observation_direction``
      - | antenna pointing direction, one of
        | ``"right"``, ``"left"``
      - ``str``
      - ``"left"``
    * - ``orbit_state``
      - orbit State, one of "ascending", "descending"
      - ``str``
      - ``"ascending"``
    * - ``orbital_plane``
      - | Orbital Plane, inclination angle of orbit, one of
        | ``45``, ``53``, ``97``
      - ``int``
      - ``45``
    * - ``pixel_spacing_azimuth``
      - pixel spacing azimuth (m)
      - ``Union[int, float]``
      - ``5``
    * - ``pixel_spacing_range``
      - pixel spacing range (m)
      - ``Union[int, float]``
      - ``5``
    * - ``platform``
      - platform identifier
      - ``str``
      - ``"capella-6"``
    * - ``polarizations``
      - polarization, one of "HH", "VV"
      - ``List[str]``
      - ``["HH"]``
    * - ``product_type``
      - | product type str, one of
        | ``"SLC"``, ``"GEO"``, ``"GEC"``, ``"SICD"``, ``"SIDD"``, ``"CPHD"``, ``"CSI"`, ``"CSIDD"``
        | ``VC``, ``"VS"``, ``"ACD"``
      - ``str``
      - ``"SLC"``
    * - ``resolution_azimuth``
      - resolution azimuth (m)
      - ``float``
      - ``0.5``
    * - ``resolution_ground_range``
      - resolution ground range (m)
      - ``float``
      - ``0.5``
    * - ``resolution_range``
      - resolution range (m)
      - ``float``
      - ``0.5``
    * - ``squint_angle``
      - squint angle
      - ``float``
      - ``30.1``
    * - ``ownership``
      - | one of ``"ownedByOrganization"``, ``"sharedWithOrganization"``
        | ``"availableForPurchase"``, ``"publiclyAvailable"``
      - ``str``
      - ``"ownedByOrganization"``



.. _query-ops:

query operators
###############

.. list-table:: supported query operators
   :widths: 20 20 60
   :header-rows: 1

   * - operator
     - description
     - example
   * - ``eq``
     - equals
     - .. code:: python3

         product_type__eq="GEO" (== product_type="GEO")
   * - ``in``
     - contains
     - .. code:: python3

         product_type__in=["SLC", "GEO", "GEC"] ( == product_type=["SLC", "GEO", "GEC"])
   * - ``gt``
     - greater than
     - .. code:: python3

         datetime__gt="2021-01-01T00:00:00Z"
   * - ``lt``
     - lower than
     - .. code:: python3

         datetime__lt="2021-02-01T00:00:00Z"
   * - ``gte``
     - greater than equal
     - .. code:: python3

         resolution_range__gte=0.3
   * - ``lte``
     - lower than equal
     - .. code:: python3

         resolution_azimuth__lte=0.5


.. _tr-query-fields:

tasking requests
################

.. list-table:: supported query fields for tasking request search
    :widths: 30 40 20 20
    :header-rows: 1

    * - field name
      - description
      - type
      - example
    * - ``collection_type``
      - | Capella collection type, one of
        | ``"spotlight_ultra"``, ``"spotlight"``,
        | ``"stripmap_100"``, ``"stripmap_50"``, ``"stripmap_20"``
        | ``"parallel_stripmap_100"``, ``"parallel_stripmap_50"``, ``"parallel_stripmap_20"``
      - ``str``
      - ``"spotlight_ultra"``
    * - ``collection_tier``
      - collection tier
      - ``str``
      - ``"priority"``
    * - ``last_status_time``
      - UTC datetime of latest status
      - ``str``
      - ``"2020-02-12"``
    * - ``org_id``
      - organization id to list tasking requests for (requires elevated permissions)
      - ``str``
      - ``""34c78a57-2d68-4b4a-a7ba-c188f9e2645d""``
    * - ``status``
      - | current TaskingRequestStatus
        | ``"received"``, ``"review"``,
        | ``"submitted"``, ``"active"``, ``"accepted"``, ``"rejected"``, ``"expired"``,
        | ``"completed"``, ``"anomaly"``, ``"canceled"``, ``"error"``, ``"failed"``
      - ``str``
      - ``"completed"``
    * - ``submission_time``
      - UTC datetime of task submission
      - ``str``
      - ``"2020-02-12"``
    * - ``tasking_request_id``
      - tasking request id
      - ``str``
      - ``""34c78a57-2d68-4b4a-a7ba-c188f9e2645d""``
    * - ``user_id``
      - user id to list tasking requests for (requires elevated permissions)
      - ``str``
      - ``""34c78a57-2d68-4b4a-a7ba-c188f9e2645d""``
    * - ``window_open``
      - Earliest UTC datetime of collection
      - ``str``
      - ``"2020-02-12"``
    * - ``window_close``
      - Latest UTC datetime of collection
      - ``str``
      - ``"2020-02-12"``
    * - ``page_size``
      - page size, default: 250, needs to be between 250 and 500
      - ``int``
      - ``250``
