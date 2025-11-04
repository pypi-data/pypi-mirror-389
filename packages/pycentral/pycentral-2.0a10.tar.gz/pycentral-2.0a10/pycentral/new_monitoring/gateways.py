from ..utils.monitoring_utils import (
    execute_get,
    generate_timestamp_str,
    clean_raw_trend_data,
    merged_dict_to_sorted_list,
)
from ..exceptions import ParameterError
from concurrent.futures import ThreadPoolExecutor, as_completed

GATEWAY_LIMIT = 100
MONITOR_TYPE = "gateways"


class MonitoringGateways:
    @staticmethod
    def get_all_gateways(central_conn, filter_str=None, sort=None):
        """
        Retrieves a list of all Gateways, with optional filtering and sorting.

        :param central_conn: Central connection object
        :param filter_str: Optional filter string to filter devices
        :param sort: Optional sort parameter to sort devices
        :return: List response from the API
        """
        gateways = []
        total_gateways = None
        limit = GATEWAY_LIMIT
        next = 1
        # Loop to get all gateways with pagination
        while True:
            response = MonitoringGateways.get_gateways(
                central_conn, limit=limit, next=next
            )
            if total_gateways is None:
                total_gateways = response.get("total", 0)
            gateways.extend(response.get("items", []))
            if len(gateways) >= total_gateways:
                break
            next += 1

        return gateways

    @staticmethod
    def get_gateways(
        central_conn, filter_str=None, sort=None, limit=GATEWAY_LIMIT, next=1
    ):
        """
        Retrieves a list of Gateways, details include serial number, name,
        MAC address, siteId, status and more

        :param central_conn: Central connection object
        :param filter_str: Optional filter string to filter devices
        :param sort: Optional sort parameter to sort devices
        :param limit: Number of entries to return (default is 100)
        :param next: Pagination parameter for next page (default is 1)
        """
        params = {
            "limit": limit,
            "next": next,
            "filter": filter_str,
            "sort": sort,
        }

        path = MONITOR_TYPE
        return execute_get(central_conn, endpoint=path, params=params)

    @staticmethod
    def get_cluster_leader_details(central_conn, cluster_name):
        """
        Retrieves a details of the specified Gateway, details include serial
        number, name, MAC address, siteId, status and more

        :param central_conn: Central connection object
        :param cluster_name: Name of the cluster
        :return: Dict response from the API
        """
        if not cluster_name or not isinstance(cluster_name, str):
            raise ParameterError(
                "cluster_name is required and must be a string"
            )
        path = f"{MONITOR_TYPE}/{cluster_name}/leader"

        return execute_get(central_conn, endpoint=path)

    @staticmethod
    def get_gateway_details(central_conn, serial_number):
        """
        Retrieves a details of the specified Gateway, details include serial
        number, name, MAC address, siteId, status and more

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )
        path = f"{MONITOR_TYPE}/{serial_number}"
        return execute_get(central_conn, endpoint=path)

    @staticmethod
    def get_gateway_interfaces(
        central_conn,
        serial_number,
        filter_str=None,
        sort=None,
        limit=GATEWAY_LIMIT,
        next=1,
    ):
        """
        Retrieves the details of ports/interfaces for the specified Gateway,
        details include interface name, status, speed, mtu and more

        :param central_conn: Central connection object
        :param filter_str: Optional filter string supported fields are portType,
        vlanMode, speed, duplex, status, uplink and vlan.
        :param sort: Optional sort parameter supported fields are mtu,
        vlanMode, speed, duplex, status and vlan.
        :param limit: Number of entries to return (default is 100)
        :param next: Pagination parameter for next page (default is 1)
        """
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )
        params = {
            "limit": limit,
            "next": next,
            "filter": filter_str,
            "sort": sort,
        }
        path = f"{MONITOR_TYPE}/{serial_number}/ports"
        return execute_get(central_conn, endpoint=path, params=params)

    @staticmethod
    def get_gateway_lan_tunnels(
        central_conn,
        serial_number,
        filter_str=None,
        sort=None,
        limit=GATEWAY_LIMIT,
        next=1,
    ):
        """
        Retrieves the details of ports/interfaces for the specified Gateway,
        details include interface name, status, speed, mtu and more

        :param central_conn: Central connection object
        :param filter_str: Optional filter string supported fields are tunnelName,
        health, encapsulation, mode, and status.
        :param sort: Optional sort parameter supported fields are tunnelName,
        encapsulation, destinationIpAddress, sourceIpAddress, mode, uptime and vni.
        :param limit: Number of entries to return (default is 100)
        :param next: Pagination parameter for next page (default is 1)
        """
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )
        params = {
            "limit": limit,
            "next": next,
            "filter": filter_str,
            "sort": sort,
        }
        path = f"{MONITOR_TYPE}/{serial_number}/lan-tunnels"
        return execute_get(central_conn, endpoint=path, params=params)

    @staticmethod
    def get_gateway_stats(
        central_conn,
        serial_number,
        start_time=None,
        end_time=None,
        duration=None,
        return_raw_response=False,
    ):
        """
        Retrieves the details of multiple statistics for the specified Gateway,
        stats will be gathered from an optional timerange default is 5 minutes.
        CPU utilization, Memory utilization, Wan availability stats are gathered.

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        # API implementation of network-monitoring/v1alpha1/gateways/serial_number/cpu, wan-availability memory(Parallel loop of individual endpoints)
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )

        # dispatch the three metric calls in parallel; helper methods handle timestamp logic
        funcs = [
            MonitoringGateways.get_gateway_cpu_utilization,
            MonitoringGateways.get_gateway_memory_utilization,
            MonitoringGateways.get_gateway_wan_availability,
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
                    if isinstance(resp, list) is True and len(resp) == 1:
                        resp = resp[0]
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

    def get_latest_gateway_stats(
        central_conn,
        serial_number,
    ):
        """
        Retrieves the details of multiple statistics for the specified Gateway,
        from the last 5 minutes.
        CPU utilization, Memory utilization, Wan availability stats are gathered.

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )
        stats = MonitoringGateways.get_gateway_stats(
            central_conn, serial_number, duration="5m"
        )
        if stats and isinstance(stats, list) and len(stats) > 0:
            return stats[-1]
        else:
            return {}

    @staticmethod
    def get_gateway_cpu_utilization(
        central_conn,
        serial_number,
        start_time=None,
        end_time=None,
        duration=None,
    ):
        """
        Retrieves the details of CPU utilization for the specified Gateway,
        stats will be gathered from an optional timerange default is 5 minutes.

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )
        if start_time is None and end_time is None and duration is None:
            return execute_get(
                central_conn,
                endpoint=f"{MONITOR_TYPE}/{serial_number}/cpu-utilization-trends",
            )

        return execute_get(
            central_conn,
            endpoint=f"{MONITOR_TYPE}/{serial_number}/cpu-utilization-trends",
            params={
                "filter": generate_timestamp_str(
                    start_time=start_time, end_time=end_time, duration=duration
                )
            },
        )

    @staticmethod
    def get_gateway_memory_utilization(
        central_conn,
        serial_number,
        start_time=None,
        end_time=None,
        duration=None,
    ):
        """
        Retrieves the details of memory utilization for the specified Gateway,
        stats will be gathered from an optional timerange default is 5 minutes.

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )
        if start_time is None and end_time is None and duration is None:
            return execute_get(
                central_conn,
                endpoint=f"{MONITOR_TYPE}/{serial_number}/memory-utilization-trends",
            )

        return execute_get(
            central_conn,
            endpoint=f"{MONITOR_TYPE}/{serial_number}/memory-utilization-trends",
            params={
                "filter": generate_timestamp_str(
                    start_time=start_time, end_time=end_time, duration=duration
                )
            },
        )

    @staticmethod
    def get_gateway_wan_availability(
        central_conn,
        serial_number,
        start_time=None,
        end_time=None,
        duration=None,
    ):
        """
        Retrieves the details of wan availability for the specified Gateway,
        stats will be gathered from an optional timerange default is 5 minutes.

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )
        if start_time is None and end_time is None and duration is None:
            return execute_get(
                central_conn,
                endpoint=f"{MONITOR_TYPE}/{serial_number}/wan-availability-trends",
            )

        return execute_get(
            central_conn,
            endpoint=f"{MONITOR_TYPE}/{serial_number}/wan-availability-trends",
            params={
                "filter": generate_timestamp_str(
                    start_time=start_time, end_time=end_time, duration=duration
                )
            },
        )

    @staticmethod
    def get_tunnel_health_summary(central_conn, serial_number):
        """
        Retrieves health summary of LAN tunnels present in the specified gateway.

        :param central_conn: Central connection object
        :param serial_number: Serial number of the device
        :return: List response from the API
        """
        MonitoringGateways._validate_central_conn_and_serial(
            central_conn, serial_number
        )
        path = f"{MONITOR_TYPE}/{serial_number}/lan-tunnels-health-summary"
        return execute_get(central_conn, endpoint=path)

    def _validate_central_conn_and_serial(central_conn, serial_number):
        """
        Utility to validate central_conn and serial_number.
        Raises ParameterError if validation fails.
        """
        if central_conn is None:
            raise ParameterError("central_conn is required")
        # Optionally, check for expected type of central_conn here if needed
        if not isinstance(serial_number, str) or not serial_number:
            raise ParameterError(
                "serial_number is required and must be a string"
            )
