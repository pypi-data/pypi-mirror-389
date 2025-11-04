from ..utils.monitoring_utils import execute_get
from ..exceptions import ParameterError

MONITOR_TYPE = "devices"
DEVICE_LIMIT = 100


class MonitoringDevices:
    @staticmethod
    def get_all_devices(central_conn, filter_str=None, sort=None):
        """
        Retrieves a list of all devices and their details.

        :param central_conn: Central connection object
        :param filter_str: Optional filter string to filter devices
        :param sort: Optional sort parameter to sort devices
        :return: List response from the API
        """
        devices = []
        total_devices = None
        limit = DEVICE_LIMIT
        next = 1
        while True:
            response = MonitoringDevices.get_devices(
                central_conn, filter_str=filter_str, limit=limit, next=next
            )
            if total_devices is None:
                total_devices = response.get("total", 0)
            devices.extend(response.get("items", []))
            if len(devices) >= total_devices:
                break
            next += 1

        return devices

    @staticmethod
    def get_devices(
        central_conn, filter_str=None, sort=None, limit=DEVICE_LIMIT, next=1
    ):
        """
        Retrieves a list of devices and their details, with optional filtering and sorting.

        :param central_conn: Central connection object
        :param filter_str: Optional filter string to filter devices
        :param sort: Optional sort parameter to sort devices
        :param limit: Number of entries to return (default is 100)
        :param next: Pagination parameter for next page (default is 1)
        :return: List response from the API
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
    def get_device_inventory(
        central_conn,
        filter_str=None,
        sort=None,
        search=None,
        site_assigned=None,
        limit=DEVICE_LIMIT,
        next=1,
    ):
        """
        Retrieves a list of sites with the number of poor, fair, and good
        performing devices for each site.

        :param central_conn: Central connection object
        :param limit: Number of entries to return (default is 100)
        :param offset: Number of entries to skip for pagination (default is 0)
        :return: List response from the API
        """
        params = {
            "limit": limit,
            "next": next,
            "filter": filter_str,
            "sort": sort,
            "search": search,
            "site-assigned": site_assigned,
        }
        path = "device-inventory"
        return execute_get(central_conn, endpoint=path, params=params)

    @staticmethod
    def delete_device(central_conn, serial_number):
        """
        Deletes a device from Central Monitoring, device must be OFFLINE to be deleted.

        :param central_conn: Central connection object
        :param limit: Number of entries to return (default is 100)
        :param offset: Number of entries to skip for pagination (default is 0)
        :return: Tuple boolean indicating success, and response from API
        """
        if not serial_number or not isinstance(serial_number, str):
            raise ParameterError(
                "serial_number is required and must be a string"
            )

        path = f"{MONITOR_TYPE}/{serial_number}"

        resp = central_conn.command("DELETE", path)

        if resp["code"] != 200:
            # return False, resp
            # Should we raise exception instead?
            raise Exception(
                f"Error deleting device from {path}: {resp['code']} - {resp['msg']}"
            )

        return True, resp
