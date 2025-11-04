from ..utils.monitoring_utils import (
    execute_get,
    generate_timestamp_str,
    clean_raw_trend_data,
    merged_dict_to_sorted_list,
)
from ..exceptions import ParameterError
from concurrent.futures import ThreadPoolExecutor, as_completed

AP_LIMIT = 100
MONITOR_TYPE = "aps"


class MonitoringAPs:
    # Wrapper for network-monitoring/v1alpha1/aps to loop and get all devices
    @staticmethod
    def get_all_aps(central_conn, filter_str=None, sort=None):
        aps = []
        total_aps = None
        next_page = 1
        while True:
            resp = MonitoringAPs.get_aps(
                central_conn,
                filter_str=filter_str,
                sort=sort,
                limit=AP_LIMIT,
                next_page=next_page,
            )
            if total_aps is None:
                total_aps = resp.get("total", 0)

            aps.extend(resp["items"])

            if len(aps) == total_aps:
                break

            next_page = resp.get("next")
            if not next_page:
                break

            next_page = int(next_page)
        return aps

    # API implementation of network-monitoring/v1alpha1/aps
    @staticmethod
    def get_aps(
        central_conn, filter_str=None, sort=None, limit=AP_LIMIT, next_page=1
    ):
        path = MONITOR_TYPE
        if limit > AP_LIMIT:
            raise ParameterError(f"limit cannot exceed {AP_LIMIT}")
        if next_page < 1:
            raise ParameterError("next_page must be 1 or greater")
        params = {
            "filter": filter_str,
            "sort": sort,
            "limit": limit,
            "next": next_page,
        }
        return execute_get(central_conn, endpoint=path, params=params)

    @staticmethod
    def get_ap_details(central_conn, serial_number):
        """
        Retrieves a details of the specified Access Point (AP), details include serial
        number, name, MAC address, siteId, status and more

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        MonitoringAPs._validate_device_serial(serial_number=serial_number)
        path = f"{MONITOR_TYPE}/{serial_number}"
        return execute_get(central_conn, endpoint=path)

    @staticmethod
    def get_ap_stats(
        central_conn,
        serial_number,
        start_time=None,
        end_time=None,
        duration=None,
        return_raw_response=False,
    ):
        """
        Retrieves a details of the specified Access Point (AP), details include serial
        number, name, MAC address, siteId, status and more

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        MonitoringAPs._validate_device_serial(serial_number)

        # dispatch the three metric calls in parallel; helper methods handle timestamp logic
        funcs = [
            MonitoringAPs.get_ap_cpu_utilization,
            MonitoringAPs.get_ap_memory_utilization,
            MonitoringAPs.get_ap_poe_utilization,
        ]

        raw_results = []
        with ThreadPoolExecutor(max_workers=3) as executor:
            future_map = {
                executor.submit(
                    func,
                    central_conn,
                    serial_number,
                    start_time,
                    end_time,
                    duration,
                ): func
                for func in funcs
            }
            for fut in as_completed(future_map):
                func = future_map[fut]
                try:
                    resp = fut.result()
                    raw_results.append(resp)
                except Exception as e:
                    # propagate the error for the caller to handle, but include which call failed
                    raise RuntimeError(
                        f"{func.__name__} metrics request failed: {e}"
                    ) from e

        if return_raw_response:
            return raw_results

        data = {}
        for resp in raw_results:
            if not isinstance(resp, dict):
                continue
            data = clean_raw_trend_data(resp, data=data)
        data = merged_dict_to_sorted_list(data)
        return data

    def get_latest_ap_stats(
        central_conn,
        serial_number,
    ):
        MonitoringAPs._validate_device_serial(serial_number)
        stats = MonitoringAPs.get_ap_stats(
            central_conn, serial_number, duration="5m"
        )
        if stats and isinstance(stats, list) and len(stats) > 0:
            return stats[-1]
        else:
            return {}

    @staticmethod
    def get_ap_cpu_utilization(
        central_conn,
        serial_number,
        start_time=None,
        end_time=None,
        duration=None,
    ):
        MonitoringAPs._validate_device_serial(serial_number)
        path = f"{MONITOR_TYPE}/{serial_number}/cpu-utilization-trends"
        if start_time is None and end_time is None and duration is None:
            return execute_get(central_conn, endpoint=path)

        return execute_get(
            central_conn,
            endpoint=path,
            params={
                "filter": generate_timestamp_str(
                    start_time=start_time, end_time=end_time, duration=duration
                )
            },
        )

    @staticmethod
    def get_ap_memory_utilization(
        central_conn,
        serial_number,
        start_time=None,
        end_time=None,
        duration=None,
    ):
        MonitoringAPs._validate_device_serial(serial_number)
        path = f"{MONITOR_TYPE}/{serial_number}/memory-utilization-trends"
        if start_time is None and end_time is None and duration is None:
            return execute_get(
                central_conn,
                endpoint=path,
            )

        return execute_get(
            central_conn,
            endpoint=path,
            params={
                "filter": generate_timestamp_str(
                    start_time=start_time, end_time=end_time, duration=duration
                )
            },
        )

    @staticmethod
    def get_ap_poe_utilization(
        central_conn,
        serial_number,
        start_time=None,
        end_time=None,
        duration=None,
    ):
        MonitoringAPs._validate_device_serial(serial_number)
        path = f"{MONITOR_TYPE}/{serial_number}/power-consumption-trends"
        if start_time is None and end_time is None and duration is None:
            return execute_get(
                central_conn,
                endpoint=path,
            )

        return execute_get(
            central_conn,
            endpoint=path,
            params={
                "filter": generate_timestamp_str(
                    start_time=start_time, end_time=end_time, duration=duration
                )
            },
        )

    def _validate_device_serial(serial_number):
        """
        Utility to validate device serial_number.
        Raises ParameterError if validation fails.
        """
        if not isinstance(serial_number, str) or not serial_number:
            raise ParameterError(
                "serial_number is required and must be a string"
            )
