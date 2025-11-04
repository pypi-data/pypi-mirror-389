from ..utils.monitoring_utils import execute_get, simplified_site_resp
from ..exceptions import ParameterError

# Sites doesn't really abide by the same pattern as other monitor types
# Should we keep?
MONITOR_TYPE = "sites"
SITE_LIMIT = 100


class MonitoringSites:
    @staticmethod
    def get_all_sites(central_conn, return_raw_response=False):
        """
        Retrieves a list of all sites with their details.

        :param central_conn: Central connection object
        :return: List response from the API
        """
        sites = []
        total_sites = None
        limit = SITE_LIMIT
        offset = 0
        while True:
            response = MonitoringSites.get_sites(
                central_conn, limit=limit, offset=offset
            )
            if total_sites is None:
                total_sites = response.get("total", 0)
            sites.extend(response["items"])
            if len(sites) == total_sites:
                break
            offset += limit
        if not return_raw_response:
            sites = [simplified_site_resp(site) for site in sites]
        return sites

    # need to include logic to handle params/filters/sorting
    @staticmethod
    def get_sites(central_conn, limit=SITE_LIMIT, offset=0):
        """
        Retrieves a list of health information for each site, including
        devices, clients, critical alerts with count, along with their
        respective health and health reasons.

        :param central_conn: Central connection object
        :param limit: Number of entries to return (default is 100)
        :param offset: Number of entries to skip for pagination (default is 0)
        :return: List response from the API
        """
        params = {"limit": limit, "offset": offset}
        path = "sites-health"
        return execute_get(central_conn, endpoint=path, params=params)

    # need to include logic to handle params/filters/sorting
    @staticmethod
    def list_sites_device_health(central_conn, limit=100, offset=0):
        """
        Retrieves a list of sites with the number of poor, fair, and good
        performing devices for each site.

        :param central_conn: Central connection object
        :param limit: Number of entries to return (default is 100)
        :param offset: Number of entries to skip for pagination (default is 0)
        :return: List response from the API
        """
        params = {"limit": limit, "offset": offset}
        path = "sites-device-health"
        return execute_get(central_conn, endpoint=path, params=params)

    # need to include logic to handle params/filters/sorting
    @staticmethod
    def list_site_information(central_conn, site_id, limit=100, offset=0):
        """
        Retrieves a list of health information for each site, including
        devices, clients, critical alerts with count, along with their
        respective health and health reasons.

        :param central_conn: Central connection object
        :param limit: Number of entries to return (default is 100)
        :param offset: Number of entries to skip for pagination (default is 0)
        :return: List response from the API
        """
        if not site_id or not isinstance(site_id, int):
            raise ParameterError("site_id is required and must be an integer")
        params = {"limit": limit, "offset": offset}
        path = f"site-health/{site_id}"
        return execute_get(central_conn, endpoint=path, params=params)
