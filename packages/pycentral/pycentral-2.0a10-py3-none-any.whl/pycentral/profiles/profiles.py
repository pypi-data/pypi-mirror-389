# (C) Copyright 2025 Hewlett Packard Enterprise Development LP.
# MIT License

from pycentral.exceptions import ParameterError, VerificationError
from pycentral.utils import profile_utils, url_utils
from pycentral import NewCentralBase
from copy import deepcopy
import re


class Profiles:
    def __init__(
        self,
        name=None,
        central_conn=None,
        config_dict=dict(),
        local=None,
    ):
        """
        instantiate a configuration Profile object

        :param name: profiles require an identifier key/value pair, typically
         "name" or "id" or another key is used, this value will be mapped
         accordingly
        :type name: str, optional
        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, optional
        :param config_dict: dictionary containing API keys & values used to
        configure the configuration profile, defaults to {}
        :type config_dict: dict, optional
        :param local: dictionary containing required local keys & values used
        to assign the profile, ex) {"scope_id": 12345, "persona": "CAMPUS_AP"}
        :type local: dict, optional
        """
        # Initialize attrs that will be later defined by child
        self.config_dict = config_dict
        self.object_data = dict()

        if name and isinstance(name, str):
            self.name = name
        elif name and not isinstance(name, str):
            raise ParameterError(
                f"name must be a valid string found {type(name)}"
            )

        self.__modified = False
        self.materialized = False

        if central_conn:
            self.central_conn = central_conn
        else:
            logger = NewCentralBase.set_logger(NewCentralBase, "INFO")
            logger.warning(
                "No Central connection provided - set central_conn before making API calls"
            )

        if local and profile_utils.validate_local(local):
            # Sample Local Data {"scope_id": 12345, "persona": "CAMPUS_AP"}
            self.local = profile_utils.validate_local(local)
        else:
            self.local = None

    def get_resource_str(self):
        """
        Returns the resource string for the profile, used in profile assignment
        to scopes

        :return: resource string for the profile, ex) "layer2-vlan/StaffVlan"
        """
        if not self.object_data["resource"]:
            err_str = "Missing self.object_data['resource'] attribute"
            raise VerificationError(err_str, " get_resource_str() failed")
        elif not self.name:
            err_str = "Missing self.name attribute"
            raise VerificationError(err_str, " get_resource_str() failed")
        return f"{self.object_data['resource']}/{self.name}"

    def set_resource(self, resource):
        """
        Set the resource for the profile, the resource is used for assigning local
        profiles and is typically the same as last value (not including name/id)
        of the API path ex) "layer2-vlan" for VLAN profiles, "policies" for Policy profiles, etc.

        :param resource: Resource for the profile, ex) "layer2-vlan"
        :type resource: str
        """
        if not resource or not isinstance(resource, str):
            raise ParameterError(
                "Resource not provided or not a valid string. Please provide a valid resource."
            )
        self.object_data["resource"] = resource

    def set_name(self, name):
        """
        Set the name for the profile

        :param name: name for the profile, ex) "StaffVlan"
        :type name: str
        """
        if not name or not isinstance(name, str):
            raise ParameterError(
                "Name not provided or not a valid string. Please provide a valid name."
            )
        self.name = name

    def set_bulk_key(self, bulk_key):
        """
        Set the bulk key for the profile

        :param bulk_key: bulk key for the profile, ex) "profile"
        :type bulk_key: str
        """
        if not bulk_key or not isinstance(bulk_key, str):
            raise ParameterError(
                "Bulk key not provided or not a valid string. Please provide a valid bulk key."
            )
        self.object_data["bulk_key"] = bulk_key

    def get_bulk_key(self):
        """
        Returns the bulk key for the profile
        """
        if "bulk_key" in self.object_data:
            return self.object_data["bulk_key"]
        return None

    def set_path(self, path):
        """
        Set the URL path (self.object_data['path']) for the profile, does NOT
        include base_url (https://<base_url>.com/) or configuration
        prefix ("network-config/v1alpha1/")

        :param path: URL path for the profile, ex) "layer2-vlan"
        :type path: str
        """
        # Remove any URL prefix matching https://.*\.com
        if path:
            path = re.sub(r"https://.*?\.com", "", path)
            if path.startswith("/"):
                path = path[1:]
            # Include NETWORKING_PREFIX if present
            prefix = url_utils.get_prefix()
            if prefix not in path:
                path = prefix + path
            # path = re.sub(prefix, "", path)
            self.object_data["path"] = path
        else:
            raise ParameterError(
                "URL path for the profile not provided. Please provide a valid"
                "URL path excluding the https://base_url.com"
            )

    def get_path(self):
        """
        Returns the URL path for the profile, excluding base_url
        """
        if "path" in self.object_data:
            return self.object_data["path"]
        return None

    def set_central_conn(self, central_conn):
        """
        Set the central connection object for the profile

        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, required
        """

        if not central_conn:
            raise ParameterError(
                "Central connection object not provided. Please provide a valid Central connection object"
            )

        self.central_conn = central_conn

    def get_central_conn(self):
        """
        Retrieve the Central connection object associated with the profile, if set.

        :return: The Central connection object if set, otherwise `None`.
        :rtype: NewCentralBase or None
        """

        if not hasattr(self, "central_conn") or not self.central_conn:
            self.central_conn.logger.warning(
                "No Central connection provided - set central_conn before making API calls"
            )
            return None

        return self.central_conn

    def set_config_dict(self, config_dict):
        """
        Sets self.config_dict as a copy of the provided dictionary

        :param config_dict: dictionary containing the configuration properties for a Profile
        :type config_dict: dict
        """
        if not config_dict or not isinstance(config_dict, dict):
            raise ParameterError("config_dict must be a valid dictionary")
        self.config_dict = config_dict.copy()

    def set_config(self, config_key, config_value):
        """
        Updates self.config_dict[config_key] with the provided config_value and
        sets the attribute of the object to match the same config_value

        :param config_key: _description_
        :type config_key: _type_
        :param config_value: _description_
        :type config_value: _type_
        """
        if not config_key and isinstance(config_key) is not str:
            raise ParameterError(
                "config_key must be a valid string containing the key to update"
            )
        self.config_dict[config_key] = config_value
        self.__dict__[config_key] = config_value

    def set_local_parameters(self, local):
        """
        Sets the local profile parameters for the object. Dict provided must
        have the keys scope_id type int and persona type str

        :param local: A dictionary containing keys scope_id type int and persona type str
        :type local: dict
        """
        self.local = profile_utils.validate_local(local)

    def get_local_parameters(self):
        """
        Returns a dictionary of required keys/values to be used in API calls
        for local profiles. If local profile is not set, returns None.

        :return: local_attributes dictionary if self.local is set, else None
        :rtype: dict
        """
        if self.local:
            return profile_utils.validate_local(self.local)
        return None

    def _getattrsdict(self, config_attrs):
        """
        Utility function to dynamically retrieve attributes of an object based on
        the provided dictionary.

        :param config_attrs: dict whose keys will be the attributes to retrieve
            from the provided object with the value set to the value found in
            self, else the value in dict if not present in self.
        :type config_attrs: dict
        """
        attr_data_dict = dict()
        for key, value in config_attrs.items():
            key_underscored = key.replace("-", "_")
            if hasattr(self, key):
                attr_data_dict[key] = getattr(self, key)
            elif hasattr(self, key_underscored):
                attr_data_dict[key] = getattr(self, key_underscored)
            else:
                attr_data_dict[key] = value

        return attr_data_dict

    def _createattrs(obj, data_dictionary):
        """
        Given a dictionary object creates class attributes. The methods
            implements setattr() which sets the value of the specified
            attribute of the specified object. If the attribute is already
            created within the object. It's state changes only if the current
            value is not None. Otherwise it keeps the previous value.
        :param obj: Object instance to create/set attributes
        :type obj: PYCENTRAL object
        :param data_dictionary: dictionary containing keys that will be attrs
        :type data_dictionary: dict
        """

        # Used to create a deep copy of the dictionary
        dictionary_var = deepcopy(data_dictionary)

        # K is the argument and V is the value of the given argument
        for k, v in dictionary_var.items():
            # In case a key has '-' inside it's name.
            k = k.replace("-", "_")

            obj.__dict__[k] = v

    def apply(self):
        """
        Main method used to update or create a Profile.
            Checks whether the Profile exists in Central. Calls
            self.update() if Profile is being updated.
            Calls self.create() if a Profile is being created.
        :return: var modified - True if object was created or modified.
        :rtype: bool
        """
        modified = False
        if self.materialized:
            modified = self.update()
        else:
            modified = self.create()
        # Set internal attribute
        self.__modified = modified
        return modified

    def create(self):
        """
        Create configuration profile in Central through a POST request. This
        function assumes that required attributes such as central_conn, path,
        and config_dict are set. Use Profiles.set_path(), Profiles.set_central_conn(),
        and Profiles.set_config_dict() to ensure all required attributes are set
        if not provided at initialization.

        :return: Tuple including bool (True/False) if profile was
        successfully created, and the result of the API call.
        :rtype: tuple (bool, dict)
        """
        result = False
        body = dict()

        params = self.get_local_parameters()

        if (
            not hasattr(self, "central_conn")
            or not self.central_conn
            or "path" not in self.object_data.keys()
            or not self.object_data["path"]
        ):
            raise VerificationError(
                "Create failed - Required attributes missing in Profile. "
                "Use Profiles.set_path() and Profiles.set_central_conn() to"
                " ensure central_conn and path are set."
            )

        path = self.object_data["path"]

        if not hasattr(self, "central_conn") or not self.central_conn:
            raise VerificationError(
                "Create failed - Central connection required but missing in Profile. "
                "Use Profiles.set_central_conn() to ensure central_conn and path are set."
            )

        if isinstance(self.config_dict, dict):
            body = self.config_dict.copy()

        # Logic for handling bulk profile configuration
        # Use bulk API endpoint if bulk_key is set and name or identifier is
        # not provided in the path (single operation)
        if (
            "bulk_key" in self.object_data
            and self.name not in self.get_path()
            and isinstance(self.config_dict, dict)
        ):
            # Bulk API expects a list of dictionaries therefor if config_dict
            # is a dictionary it's wrapped in a list to be sent
            body = {self.object_data["bulk_key"]: [self.config_dict.copy()]}
        elif (
            "bulk_key" in self.object_data
            and self.name not in self.get_path()
            and isinstance(self.config_dict, list)
        ):
            # Bulk API expects a list of dictionaries therefore if config_dict
            # is a list it's left alone
            body = {self.object_data["bulk_key"]: self.config_dict}

        resp = self.central_conn.command(
            "POST", path, api_data=body, api_params=params
        )
        if resp["code"] == 200:
            self.materialized = True
            result = True
            self.central_conn.logger.info("profile successfully created!")
        # If profile exists API call will return 400 with duplicate message
        elif resp["code"] == 400 and "duplicate" in resp["msg"]["message"]:
            error = resp["msg"]
            err_str = f"Duplicate-message -> {error}"
            self.central_conn.logger.warning(
                f"Failed to create {self.object_data['path']} profiles - {err_str}"
            )
        else:
            error = resp["msg"]
            err_str = f"Error-message -> {error}"
            self.central_conn.logger.error(
                f"Failed to create profile. {err_str}"
            )
        response = resp
        return (result, response)

    def get(self):
        """
        Get configuration profile in Central through a GET request. This
        function assumes that required attributes such as central_conn and path
        are set. Use Profiles.set_path() and Profiles.set_central_conn() to
        ensure all required attributes are set if not provided at initialization.

        :return: Tuple including bool (True/False) if profile was
        successfully retrieved, and the result of the API call.
        :rtype: tuple (bool, dict)
        """
        result = False
        response = None
        if (
            not hasattr(self, "central_conn")
            or not self.central_conn
            or "path" not in self.object_data.keys()
            or not self.object_data["path"]
        ):
            raise VerificationError(
                "Get failed - Required attributes missing in Profile. "
                "Please ensure central_conn and object_data['path'] are set."
            )
        # Name / id may need to be appended to path before calling GET
        path = self.object_data["path"]
        params = self.get_local_parameters()

        # Need to include `view_type` for GET requests
        if params:
            params.update({"view_type": "LOCAL"})

        if not hasattr(self, "central_conn") or not self.central_conn:
            raise VerificationError(
                "Get failed - Central connection required but missing in Profile. "
                "Please provide a valid Central connection object"
            )

        resp = self.central_conn.command("GET", path, api_params=params)
        if resp["code"] == 200 and "msg" in resp.keys():
            self.materialized = True
            result = True
            response = resp["msg"].copy()
            # Remove metadata if present
            if "metadata" in response.keys():
                # If metadata is present, remove it from the response
                response.pop("metadata")
            # Handle Bulk Requests only if bulk_key is set
            if self.get_bulk_key() and self.get_bulk_key() in response.keys():
                return result, response[self.get_bulk_key()]
            return result, response
        # URL was invalid and GET was unsuccessful
        elif resp["code"] == 400:
            response = resp
            return result, response
        else:
            self.materialized = False
            return result, response

    def compare_objects(self, obj1, obj2):
        """
        Recursively compare two objects (dicts or lists) and report differences.
        Prioritizes contents of obj1 and ignores extra attributes in obj2.

        :param obj1: First object (reference object)
        :type obj1: dict or list
        :param obj2: Second object (comparison object)
        :type obj2: dict or list
        :return: List of dictionaries containing differences found
        :rtype: list
        """
        diff_dict_list = []

        # Both objects are dictionaries
        if isinstance(obj1, dict) and isinstance(obj2, dict):
            for key, value1 in obj1.items():
                # Check if key exists in obj2
                if key not in obj2:
                    diff_dict_list.append(
                        {
                            "key": key,
                            "new_value": value1,
                            "old_value": None,
                        }
                    )
                    continue

                # Get value from obj2
                value2 = obj2[key]

                # If nested object (dict or list), recurse
                if isinstance(value1, (dict, list)) and isinstance(
                    value2, (dict, list)
                ):
                    if self.compare_objects(value1, value2):
                        diff_dict_list.append(
                            {
                                "key": key,
                                "new_value": value1,
                                "old_value": value2,
                            }
                        )
                # Otherwise compare values directly
                elif value1 != value2:
                    diff_dict_list.append(
                        {
                            "key": key,
                            "new_value": value1,
                            "old_value": value2,
                        }
                    )

        # Both objects are lists
        elif isinstance(obj1, list) and isinstance(obj2, list):
            # Compare items that exist in both lists
            for i, (item1, item2) in enumerate(zip(obj1, obj2)):
                # If nested object (dict or list), recurse
                if isinstance(item1, (dict, list)) and isinstance(
                    item2, (dict, list)
                ):
                    if self.compare_objects(item1, item2):
                        diff_dict_list.append(
                            {
                                "key": None,
                                "new_value": item1,
                                "old_value": item2,
                            }
                        )
                # Otherwise compare values directly
                elif item1 != item2:
                    diff_dict_list.append(
                        {
                            "key": None,
                            "new_value": item1,
                            "old_value": item2,
                        }
                    )

            # Check for additional items in obj1 that aren't in obj2
            if len(obj1) > len(obj2):
                diff_dict_list.append(
                    {
                        "key": None,
                        "new_value": obj1,
                        "old_value": obj2,
                    }
                )

        # Objects are of different types
        elif type(obj1) is not type(obj2):
            diff_dict_list.append(
                {
                    "key": None,
                    "new_value": obj1,
                    "old_value": obj2,
                }
            )

        # Objects are of same type but not dicts or lists (direct comparison)
        elif obj1 != obj2:
            diff_dict_list.append(
                {
                    "key": None,
                    "new_value": obj1,
                    "old_value": obj2,
                }
            )

        return diff_dict_list

    def update(self, compare_dict=None, update_data=None):
        """
        Updates the configuration profile in Central with values from
        self.config_dict OR update_data if provided.
        If no compare_dict provided the function will execute a GET to retrieve
        data for the Central profile. If a diff is found, self.config_dict will
        be pushed to Central. Invalid configurations in self.config_dict or
        update_data results in a failed update. This function assumes that
        required attributes such as central_conn, path, and config_dict are set.
        Use Profiles.set_path(), Profiles.set_central_conn(), and
        Profiles.set_config_dict() to ensure all required attributes are set if
        not provided at initialization.

        :param compare_dict: optional dict to compare against, if provided no GET
         request will be executed
        :type compare_dict: dict, optional
        :param update_data: values for updating existing profile
        :type update_data: dict, optional
        :return: Tuple including bool (True/False) if profile was
        successfully updated, and the result of the API call.
        :rtype: tuple (bool, dict)
        """
        result = False
        response = dict()
        params = None
        body = None
        # Dictionary to contain differences found for reporting
        diff_dict_list = []
        path = self.object_data["path"]
        new_config = self.config_dict.copy()

        # If update_data provided, merge into new_config taken from self.config_dict
        if update_data:
            new_config.update(update_data)

        # central_conn should be validated in previous self.get() but just in case
        if not hasattr(self, "central_conn") or not self.central_conn:
            raise VerificationError(
                "Update failed - Central connection required but missing in Profile. "
                "Please provide a valid Central connection object"
            )

        # Check for Central profile
        central_obj = None
        get_success = False
        if compare_dict and isinstance(compare_dict, dict):
            central_obj = compare_dict.copy()
        elif compare_dict and not isinstance(compare_dict, dict):
            raise ParameterError(
                "compare_dict must be a valid dictionary if provided."
            )
        else:
            get_success, central_obj = self.get()

        if not get_success and not compare_dict:
            # No profile found in Central
            self.materialized = False
            self.central_conn.logger.error(
                "Profile not materialized. "
                "Please create profile before updating"
            )
            return result, central_obj

        # Check for local/central config diff
        diff_dict_list = self.compare_objects(new_config, central_obj)

        # Update profile if diff found or if not pulling data for comparison
        if diff_dict_list:
            self.central_conn.logger.info(
                "Difference found between local profile and "
                "profile found in Central. Updating profile..."
            )
            params = self.get_local_parameters()
            if isinstance(new_config, list) and self.get_bulk_key():
                # If new_config is a list, wrap it in a dict with bulk_key
                body = {self.get_bulk_key(): new_config}
            elif (
                isinstance(new_config, dict)
                and self.get_bulk_key()
                and self.name not in self.get_path()
            ):
                # If new_config is a dict, wrap it in a dict with bulk_key
                body = {self.get_bulk_key(): [new_config]}
            else:
                # If no bulk_key, use new_config directly
                body = new_config

            resp = self.central_conn.command(
                "PATCH", path, api_data=body, api_params=params
            )
            response = resp
            if resp["code"] == 200:
                self.central_conn.logger.info("Successfully updated profile!")
                self._modified = True
                result = True
            else:
                result = False
                error = resp["msg"]
                err_str = f"Error-message -> {error}"
                self.central_conn.logger.error(
                    f"Failed to update profile. {err_str}!"
                )
            response["diff"] = diff_dict_list
        else:
            self.central_conn.logger.info(
                "No difference found between local profile and "
                "profile found in Central. No action required."
            )
        return result, response

    def delete(self):
        """
        Delete profile from Central.

        :return result: result of profile delete attempt
        :rtype: bool
        """
        path = self.object_data["path"]
        params = self.get_local_parameters()

        resp = self.central_conn.command(
            "DELETE", path, api_params=params, headers={"Accept": "*/*"}
        )
        if resp["code"] == 200:
            self.central_conn.logger.info("profile successfully deleted!")
            return (True, resp)
        else:
            self.central_conn.logger.error("Failed to delete profile!")
            return (False, resp)

    @staticmethod
    def create_profile(
        path, config_dict, central_conn, bulk_key=None, local=None
    ):
        """
        Create a configuration profile using a POST request - it's recommended
        to use the helper function pycentral.utils.url_utils.generate_url()
        to provide the path parameter.

        :param path: The API endpoint for request, omitting base_url - it's recommended
        to use the helper function pycentral.utils.url_utils.generate_url()
        :type path: str
        :param config_dict: dictionary containing API keys & values used to
        create the configuration profile
        :type config_dict: dict
        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, optional
        :param local: dictionary containing local keys & values used to assign
            the profile, defaults to {}
        :type local: dict, optional
        :return: Tuple including bool (True/False) if profile was
        successfully created, and the result of the API call.
        :rtype: tuple (bool, dict)
        """

        if not isinstance(config_dict, dict) or not config_dict:
            err_str = "config_dict should be a valid dictionary containing API\
                 keys & values"
            raise ParameterError(err_str)

        body = dict()
        if bulk_key is None:
            body = config_dict
        else:
            body[bulk_key] = [config_dict]

        result = False

        # defaults to None if local is not provided
        params = profile_utils.validate_local(local)

        resp = central_conn.command(
            "POST", path, api_data=body, api_params=params
        )
        if resp["code"] == 200:
            result = True
            central_conn.logger.info(
                f"{bulk_key} profile successfully created!"
            )
        # If profile exists API call will return 400 with duplicate message
        elif resp["code"] == 400 and "duplicate" in resp["msg"]["message"]:
            error = resp["msg"]
            err_str = f"Duplicate-message -> {error}"
            central_conn.logger.warning(
                f"Failed to create {bulk_key} profiles - {err_str}"
            )
        else:
            error = resp["msg"]
            err_str = f"Error-message -> {error}"
            central_conn.logger.error(
                f"Failed to create {bulk_key} profile - {err_str}"
            )

        return (result, resp)

    @staticmethod
    def get_profile(path, central_conn, local=None):
        """
        Get existing Profile from Central - it's recommended
        to use the helper function pycentral.utils.url_utils.generate_url()
        to provide the path parameter. If the path does not include the profile name/id,
        the API will return all profiles for that type.

        :param path: The API endpoint for request, omitting base_url - it's recommended
        to use the helper function pycentral.utils.url_utils.generate_url()
        :type path: str
        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, optional
        :param local: dictionary containing local keys & values used to assign
            the profile, defaults to {}
        :type local: dict, optional
        :return: Tuple including bool (True/False) if profile was
        successfully retrieved, and the result of the API call.
        :rtype: tuple (bool, dict)
        """
        # defaults to None if local is not provided
        params = profile_utils.validate_local(local)

        # Need to include `view_type` for GET requests
        if params:
            params.update({"view_type": "LOCAL"})

        resp = central_conn.command("GET", path, api_params=params)

        if resp["code"] == 200 and "msg" in resp.keys():
            result = True
            response = resp["msg"].copy()
            # Remove metadata if present
            if "metadata" in response.keys():
                # If metadata is present, remove it from the response
                response.pop("metadata")
            return result, response
        # URL was invalid and GET was unsuccessful
        else:
            response = resp
            return (result, response)

    @staticmethod
    def update_profile(
        path, config_dict, central_conn, bulk_key=None, local=None
    ):
        """
        Update a configuration profile using a PATCH request


        :param path: The API path for request - valid values found in
            pycentral.utils.url_utils.NewCentralURLs
        :type path: str
        :param config_dict: dictionary containing API keys & values used to
        update the configuration profile
        :type config_dict: dict
        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, optional
        :param bulk_key: The key required to wrap the configurations for
        multiple profiles for the bulk API - refer to the API reference for valid values
        ex) "profile" for DNS, "layer2-vlan" for VLANs, etc.
        :type bulk_key: str
        :param local: dictionary containing local keys & values used to assign
            the profile, defaults to {}
        :type local: dict, optional
        :raises ParameterError: If neither list_dict nor list_obj is provided.
        :return: Tuple including bool (True/False) if profile was
        successfully updated, and the result of the API call.
        :rtype: tuple (bool, dict)
        """

        if not isinstance(config_dict, dict) or not config_dict:
            err_str = "config_dict should be a valid dictionary containing API\
                 keys & values"
            raise ParameterError(err_str)

        body = dict()
        if bulk_key is None:
            body = config_dict
        else:
            body[bulk_key] = [config_dict]

        result = False

        # defaults to None if local is not provided
        params = params = profile_utils.validate_local(local)

        resp = central_conn.command(
            "PATCH", path, api_data=body, api_params=params
        )
        if resp["code"] == 200:
            result = True
            central_conn.logger.info(
                f"{bulk_key} profile successfully updated!"
            )
        else:
            error = resp["msg"]
            err_str = f"Error-message -> {error}"
            central_conn.logger.error(
                f"Failed to update {bulk_key} profile - {err_str}"
            )

        return (result, resp)

    @staticmethod
    def delete_profile(path, central_conn, local=None):
        """
        Delete a configuration profile using a DELETE request

        :param path: The API endpoint for request, omitting base_url - it's recommended
        to use the helper function pycentral.utils.url_utils.generate_url()
        :type path: str
        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, optional
        :param local: dictionary containing local keys & values used to assign
            the profile, defaults to {}
        :type local: dict, optional
        :return: Tuple including bool (True/False) if profile was
        successfully deleted, and the result of the API call.
        :rtype: tuple (bool, dict)
        """

        if not isinstance(path, str):
            err_str = "path should be a valid string containing API URL"
            raise ParameterError(err_str)

        result = False

        # defaults to None if local is not provided
        params = profile_utils.validate_local(local)

        path_split = path.split("/")
        resource = path_split[len(path_split) - 2]

        resp = central_conn.command(
            "DELETE", path, api_params=params, headers={"Accept": "*/*"}
        )

        if resp["code"] == 200:
            result = True
            central_conn.logger.info(
                f"{resource} profile successfully deleted!"
            )
        else:
            error = resp["msg"]
            err_str = f"Error-message -> {error}"
            central_conn.logger.error(err_str)

        return (result, resp)

    @staticmethod
    def create_profiles(
        bulk_key, path, central_conn, list_dict=None, list_obj=None, local=None
    ):
        """
        Create configuration profiles using a POST request to a bulk API endpoint-
        it's recommended to use the helper function pycentral.utils.url_utils.generate_url()
        to provide the path parameter.

        :param bulk_key: The key required to wrap the configurations for
        multiple profiles for the bulk API - refer to the API reference for valid values
        ex) "profile" for DNS, "layer2-vlan" for VLANs, etc.
        :type bulk_key: str
        :param path: The API endpoint for request, omitting base_url - it's recommended
        to use the helper function pycentral.utils.url_utils.generate_url()
        :type path: str
        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, optional
        :param list_dict: List of profile configuration dictionaries, defaults to None.
        :type list_dict: list, required if list_obj is not provided
        :param list_obj: List of Profiles objects containing the config_dict attribute, defaults to None.
        :type list_obj: list, optional required if list_dict is not provided
        :raises ParameterError: If neither list_dict nor list_obj is provided.
        :param local: Dictionary containing local keys & values used to assign the profile, defaults to None.
        :type local: dict, optional
        :return: Tuple including bool (True/False) if profiles were
        successfully created, and the result of the API call.
        :rtype: tuple (bool, dict)
        """

        if not list_dict and not list_obj:
            err_str = "either list_dict or list_obj must be provided"
            raise ParameterError(err_str)

        body = dict()

        # Process lists and create body for bulk profile create
        if list_obj and isinstance(list_obj, list):
            body[bulk_key] = [obj.config_dict for obj in list_obj]
        elif list_dict and isinstance(list_dict, list):
            body[bulk_key] = list_dict
        else:
            err_str = "either list_dict or list_obj is invalid"
            raise ParameterError(err_str)

        result = False

        # defaults to None if local is not provided
        params = profile_utils.validate_local(local)

        resp = central_conn.command(
            "POST", path, api_data=body, api_params=params
        )
        if resp["code"] == 200:
            result = True
            central_conn.logger.info(
                f"{bulk_key} profiles successfully created!"
            )
        # If profile exists API call will return 400 with duplicate message
        elif resp["code"] == 400 and "duplicate" in resp["msg"]["message"]:
            error = resp["msg"]
            err_str = f"Duplicate-message -> {error}"
            central_conn.logger.warning(
                f"Failed to create {bulk_key} profiles - {err_str}"
            )
        else:
            error = resp["msg"]
            err_str = f"Error-message -> {error}"
            central_conn.logger.error(
                f"Failed to create {bulk_key} profiles - {err_str}"
            )

        return (result, resp)

    @staticmethod
    def update_profiles(
        bulk_key, path, central_conn, list_dict=None, list_obj=None, local=None
    ):
        """
        Update multiple configuration profiles in a single API call using a PATCH
        request.

        :param bulk_key: bulk key for profiles - valid values found in
            pycentral.utils.profile_utils.ProfilesUtils
        :type bulk_key: str
        :param path: API path for request.
        :type path: str
        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, optional
        :param list_dict: List of profile configuration dictionaries, defaults to None.
        :type list_dict: list, required if list_obj is not provided
        :param list_obj: List of Profiles objects containing the config_dict attribute, defaults to None.
        :type list_obj: list, optional required if list_dict is not provided
        :raises ParameterError: If neither list_dict nor list_obj is provided.
        :param local: dictionary containing required local keys & values used
        to assign the profile, ex) {"scope_id": 12345, "persona": "CAMPUS_AP"}
        :type local: dict, optional
        :return: Tuple including bool (True/False) if profiles were
        successfully updated, and the result of the API call.
        :rtype: tuple (bool, dict)
        """

        if not list_dict and not list_obj:
            err_str = "either list_dict or list_obj must be provided"
            raise ParameterError(err_str)

        body = dict()

        # Process lists and create body for bulk create
        if list_obj:
            body[bulk_key] = [obj.config_dict for obj in list_obj]
        elif list_dict:
            body[bulk_key] = list_dict

        result = False

        # defaults to None if local is not provided
        params = profile_utils.validate_local(local)

        resp = central_conn.command(
            "PATCH", path, api_data=body, api_params=params
        )
        if resp["code"] == 200:
            result = True
            central_conn.logger.info(
                f"{bulk_key} profiles successfully updated!"
            )
        else:
            error = resp["msg"]
            err_str = f"Error-message -> {error}"
            central_conn.logger.error(
                f"Failed to update {bulk_key} . {err_str}"
            )

        return (result, resp)

    @staticmethod
    def delete_profiles(
        path_list, central_conn, local=None, error_on_fail=True
    ):
        """
        Delete multiple configuration profiles through multiple API calls using
        a DELETE request.

        :param path_list: list of API paths as type string for requests.
        :type path_list: list, required
        :param central_conn: established Central connection object
        :type central_conn: class:`NewCentralBase`, optional
        :raises ParameterError: If neither list_dict nor list_obj is provided.
        :param local: dictionary containing required local keys & values used
        to assign the profile, ex) {"scope_id": 12345, "persona": "CAMPUS_AP"}
        :type local: dict, optional
        :param error_on_fail: list of API paths as type string for requests.
        :type error_on_fail: bool, optional
        :return: Empty if profiles were successfully deleted, populated otherwise.
        :rtype: list
        """
        if not isinstance(path_list, list) or not path_list:
            err_str = "path_list should be a valid list containing config\
                  profile URLs to be deleted"
            raise ParameterError(err_str)

        failures = []

        # defaults to None if local is not provided
        params = profile_utils.validate_local(local)

        for path in path_list:
            path_split = path.split("/")
            resource = path_split[len(path_split) - 2]
            resp = central_conn.command(
                "DELETE", path, api_params=params, headers={"Accept": "*/*"}
            )
            if resp["code"] == 200:
                central_conn.logger.info(f"{resource} successfully deleted!")
            elif error_on_fail:
                error = resp["msg"]
                err_str = f"Error-message -> {error}"
                central_conn.logger.error(
                    f"Failed to delete {resource} . {err_str}"
                )
            else:
                failures.append(path)

        return failures
