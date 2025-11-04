# (C) Copyright 2025 Hewlett Packard Enterprise Development LP.
# MIT License

from pycentral.exceptions import ParameterError


def validate_local(local):
    required_keys = {"scope_id": int, "persona": str}
    local_attributes = dict()
    if local:
        if not isinstance(local, dict):
            raise ParameterError(
                "Invalid local profile attributes. Please provide a valid dictionary."
            )
        for key, expected_type in required_keys.items():
            if key not in local or not isinstance(local[key], expected_type):
                raise ParameterError(
                    f"Invalid local profile attributes. Key '{key}' must be of type {expected_type.__name__}."
                )
        local_attributes = {"object_type": "LOCAL"}
        local_attributes.update(local)
    return local_attributes
