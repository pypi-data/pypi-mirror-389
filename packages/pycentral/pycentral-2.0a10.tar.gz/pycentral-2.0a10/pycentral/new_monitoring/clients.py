from ..utils.monitoring_utils import (
    execute_get,
    build_timestamp_filter,
)
from ..exceptions import ParameterError

CLIENT_LIMIT = 100


class Clients:
    @staticmethod
    def get_all_site_clients(
        central_conn,
        site_id,
        serial_number=None,
        filter_str=None,
        sort=None,
        duration=None,
        start_time=None,
        end_time=None,
    ):
        """
        Return all clients for a site, handling pagination.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        :param serial_number: Device serial number to filter clients (optional).
        :type serial_number: str or None
        :param filter_str: Optional filter expression applied to results.
        :type filter_str: str or None
        :param sort: Optional sort expression.
        :type sort: str or None
        :param duration: Optional duration (in seconds) for a relative time window.
        :type duration: int or None
        :param start_time: Optional start time (epoch seconds).
        :type start_time: int or None
        :param end_time: Optional end time (epoch seconds).
        :type end_time: int or None
        :returns: Flattened list of client records across all pages.
        :rtype: list[dict]

        :notes: This method repeatedly calls :meth:`get_site_clients` and combines pages until all clients of the site are retrieved.
        """
        Clients._validate_site_id(site_id)
        clients = []
        total_clients = None
        next_page = 1
        while True:
            resp = Clients.get_site_clients(
                central_conn=central_conn,
                site_id=site_id,
                serial_number=serial_number,
                filter_str=filter_str,
                sort=sort,
                next_page=next_page,
                limit=CLIENT_LIMIT,
                duration=duration,
                start_time=start_time,
                end_time=end_time,
            )
            if total_clients is None:
                total_clients = resp.get("total", 0)
            clients.extend(resp.get("items", []))
            if len(clients) == total_clients:
                break
            next_val = resp.get("next")
            if not next_val:
                break
            next_page = int(next_val)
        return clients

    @staticmethod
    def get_wireless_clients(
        central_conn,
        site_id,
        sort=None,
        duration=None,
        start_time=None,
        end_time=None,
    ):
        """
        Fetch all wireless clients for a site.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        :param group_by: Dimension to group results by (e.g., 'mac', 'ap').
        :type group_by: str or None
        :param serial_number: Device serial number to filter the trend data.
        :type serial_number: str or None
        :param start_time: Optional start time (epoch seconds).
        :type start_time: int or None
        :param end_time: Optional end time (epoch seconds).
        :type end_time: int or None
        :param duration: Optional duration (in seconds) for a relative time window.
        :type duration: int or None
        :param return_raw_response: If True, return the raw API payload.
        :type return_raw_response: bool
        :returns: Processed list of timestamped samples or raw response if requested.
        :rtype: list[dict] or dict
        :raises: :class:`~pycentral.exceptions.ParameterError` if ``site_id`` is not provided.
        """
        return Clients.get_all_site_clients(
            central_conn=central_conn,
            site_id=site_id,
            filter_str="type eq Wireless",
            sort=sort,
            duration=duration,
            start_time=start_time,
            end_time=end_time,
        )

    @staticmethod
    def get_wired_clients(
        central_conn,
        site_id,
        sort=None,
        duration=None,
        start_time=None,
        end_time=None,
    ):
        """
        Fetch all wired clients for a site.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        :param group_by: Dimension to group results by (e.g., 'mac', 'ap').
        :type group_by: str or None
        :param serial_number: Device serial number to filter the trend data.
        :type serial_number: str or None
        :param start_time: Optional start time (epoch seconds).
        :type start_time: int or None
        :param end_time: Optional end time (epoch seconds).
        :type end_time: int or None
        :param duration: Optional duration (in seconds) for a relative time window.
        :type duration: int or None
        :param return_raw_response: If True, return the raw API payload.
        :type return_raw_response: bool
        :returns: Processed list of timestamped samples or raw response if requested.
        :rtype: list[dict] or dict
        :raises: :class:`~pycentral.exceptions.ParameterError` if ``site_id`` is not provided.
        """
        return Clients.get_all_site_clients(
            central_conn=central_conn,
            site_id=site_id,
            filter_str="type eq Wired",
            sort=sort,
            duration=duration,
            start_time=start_time,
            end_time=end_time,
        )

    @staticmethod
    def get_clients_associated_device(
        central_conn,
        site_id,
        serial_number,
    ):
        """
        Retrieve clients associated with a specific device in a site.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        :param serial_number: Device serial number to filter clients (required).
        :type serial_number: str
        :returns: List of clients associated with the specified device.
        :rtype: list[dict]
        :raises: :class:`~pycentral.exceptions.ParameterError` if ``site_id`` or ``serial_number`` is not provided.
        """
        return Clients.get_all_site_clients(
            central_conn=central_conn,
            site_id=site_id,
            serial_number=serial_number,
        )

    @staticmethod
    def get_connected_clients(
        central_conn,
        site_id,
    ):
        """
        Retrieve connected clients to a site.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        """
        return Clients.get_all_site_clients(
            central_conn=central_conn,
            site_id=site_id,
            filter_str="status eq Connected",
        )

    @staticmethod
    def get_disconnected_clients(
        central_conn,
        site_id,
    ):
        """
        Retrieve disconnected clients from a site.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        :returns: List of disconnected clients.
        :rtype: list[dict]
        :raises: :class:`~pycentral.exceptions.ParameterError` if ``site_id`` or ``serial_number`` is not provided.
        """
        return Clients.get_all_site_clients(
            central_conn=central_conn,
            site_id=site_id,
            filter_str="status in (Disconnected, Failed)",
        )

    @staticmethod
    def get_site_clients(
        central_conn,
        site_id,
        serial_number=None,
        filter_str=None,
        sort=None,
        next_page=1,
        limit=CLIENT_LIMIT,
        duration=None,
        start_time=None,
        end_time=None,
    ):
        """
        Retrieve a single page of clients for a site.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        :param filter_str: Optional filter expression applied to results.
        :type filter_str: str or None
        :param sort: Optional sort expression.
        :type sort: str or None
        :param next_page: Page token/index for pagination.
        :type next_page: int
        :param limit: Maximum number of items to return in this call.
        :type limit: int
        :param duration: Optional duration (in seconds) for a relative time window.
        :type duration: int or None
        :param start_time: Optional start time (epoch seconds).
        :type start_time: int or None
        :param end_time: Optional end time (epoch seconds).
        :type end_time: int or None
        :returns: Raw API response (typically contains 'items', 'total', and 'next').
        :rtype: dict
        :raises: :class:`~pycentral.exceptions.ParameterError` if ``site_id`` is not provided.
        """
        path = "clients"

        Clients._validate_site_id(site_id)
        params = {
            "site-id": site_id,
            "serial-number": serial_number,
            "filter": filter_str,
            "sort": sort,
            "next": next_page,
            "limit": limit,
        }
        if start_time is None and end_time is None and duration is None:
            return execute_get(central_conn, endpoint=path, params=params)

        params = Clients._time_filter(
            params=params,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
        )

        return execute_get(central_conn, endpoint=path, params=params)

    @staticmethod
    def get_client_trends(
        central_conn,
        site_id,
        group_by=None,
        client_type=None,
        serial_number=None,
        start_time=None,
        end_time=None,
        duration=None,
        return_raw_response=False,
    ):
        """
        Fetch client trend data for a site.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        :param group_by: Dimension to group results by (e.g., 'mac', 'ap').
        :type group_by: str or None
        :param client_type: Trend type passed as ``type`` in the request.
        :type client_type: str or None
        :param serial_number: Device serial number to filter the trend data.
        :type serial_number: str or None
        :param start_time: Optional start time (epoch seconds).
        :type start_time: int or None
        :param end_time: Optional end time (epoch seconds).
        :type end_time: int or None
        :param duration: Optional duration (in seconds) for a relative time window.
        :type duration: int or None
        :param return_raw_response: If True, return the raw API payload.
        :type return_raw_response: bool
        :returns: Processed list of timestamped samples or raw response if requested.
        :rtype: list[dict] or dict
        :raises: :class:`~pycentral.exceptions.ParameterError` if ``site_id`` is not provided.
        """
        path = "clients/trends"

        Clients._validate_site_id(site_id)
        params = {
            "site-id": site_id,
            "group-by": group_by,
            "type": client_type,
            "serial-number": serial_number,
        }

        if start_time is None and end_time is None and duration is None:
            response = execute_get(central_conn, endpoint=path, params=params)
        else:
            params = Clients._time_filter(
                params=params,
                start_time=start_time,
                end_time=end_time,
                duration=duration,
            )

            response = execute_get(central_conn, endpoint=path, params=params)
        if return_raw_response:
            return response

        return Clients._process_client_trend_samples(response)

    @staticmethod
    def get_top_n_site_clients(
        central_conn,
        site_id,
        serial_number=None,
        count=None,
        start_time=None,
        end_time=None,
        duration=None,
    ):
        """
        Retrieve the top-N clients by usage for a specific site.

        :param central_conn: Central connection object
        :type central_conn: object
        :param site_id: Identifier of the site to query (required).
        :type site_id: str or int
        :param serial_number: Optional device serial number to scope the query.
        :type serial_number: str or None
        :param count: Number of top clients to return (must be between 1 and 100). If None, API default is used.
        :type count: int or None
        :param start_time: Optional start time for time filtering (epoch seconds).
        :type start_time: int or None
        :param end_time: Optional end time for time filtering (epoch seconds).
        :type end_time: int or None
        :param duration: Optional duration (in seconds) for a relative time window.
        :type duration: int or None
        :returns: Raw API response containing top-N usage data. The response typically includes a list of clients sorted by usage.
        :rtype: dict
        :raises ParameterError: If site_id is not provided.
        :raises ParameterError: If count is provided but not in the range 1..100.
        """
        path = "clients/usage/topn"
        Clients._validate_site_id(site_id)

        if count is not None and (count > 100 or count < 1):
            raise ParameterError("Count must be between 1 and 100")

        params = {
            "site-id": site_id,
            "serial-number": serial_number,
            "count": count,
        }

        if start_time is None and end_time is None and duration is None:
            return execute_get(central_conn, endpoint=path, params=params)

        params = Clients._time_filter(
            params=params,
            start_time=start_time,
            end_time=end_time,
            duration=duration,
        )

        return execute_get(central_conn, endpoint=path, params=params)

    def _time_filter(params, start_time, end_time, duration):
        start_unix, end_unix = build_timestamp_filter(
            start_time=start_time,
            end_time=end_time,
            duration=duration,
            fmt="unix",
        )
        params["start-query-time"] = start_unix
        params["end-query-time"] = end_unix
        return params

    def _process_client_trend_samples(payload):
        categories = payload.get("categories", [])
        samples = payload.get("samples", [])
        out = []
        for s in samples:
            row = {"timestamp": s.get("ts") or s.get("timestamp")}
            vals = s.get("data")
            if isinstance(vals, (list, tuple)):
                for cat, val in zip(categories, vals):
                    row[cat] = val
            else:
                if categories:
                    row[categories[0]] = vals
                else:
                    row["value"] = vals
            out.append(row)
        return out

    def _validate_site_id(site_id):
        """
        Utility to validate site_id.
        Raises ParameterError if validation fails.
        """
        if not isinstance(site_id, (str, int)) or not site_id:
            raise ParameterError(
                "site_id is required and must be a string or integer"
            )
