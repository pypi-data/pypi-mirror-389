# (C) Copyright 2025 Hewlett Packard Enterprise Development LP.
# MIT License

versions = ["v1alpha1", "v1"]
latest = "v1alpha1"
glp_latest = "v1"

CATEGORIES = {
    "configuration": {
        "value": "network-config",
        "type": "configuration",
        "latest": "v1alpha1",
    },
    "monitoring": {
        "value": "network-monitoring",
        "type": "monitoring",
        "latest": "v1alpha1",
    },
    "troubleshooting": {
        "value": "network-troubleshooting",
        "type": "troubleshooting",
        "latest": "v1alpha1",
    },
    "subscriptions": {"value": "subscriptions", "type": "glp", "latest": "v1"},
    "user_management": {"value": "identity", "type": "glp", "latest": "v1"},
    "devices": {"value": "devices", "type": "glp", "latest": "v1"},
    "service_catalog": {
        "value": "service-catalog",
        "type": "glp",
        "latest": "v1",
    },
}


def get_prefix(category="configuration", version="latest"):
    if category not in CATEGORIES:
        raise ValueError(
            f"Invalid category: {category}, Supported categories: {list(CATEGORIES.keys())}"
        )
    category_value = CATEGORIES[category]["value"]
    if version == "latest":
        version = (
            latest
            if not (CATEGORIES[category]["type"] == "glp")
            else glp_latest
        )
    else:
        if version not in versions:
            raise ValueError(
                f"Invalid version: {version}. Allowed versions: {versions}"
            )
    return f"{category_value}/{version}/"


def generate_url(api_endpoint, category="configuration", version="latest"):
    if category not in CATEGORIES:
        raise ValueError(
            f"Invalid category: {category}, Supported categories: {list(CATEGORIES.keys())}"
        )
    if api_endpoint is not None and not isinstance(api_endpoint, str):
        raise TypeError(
            f"Invalid type: {type(api_endpoint)} for api_endpoint, expected str"
        )
    category_value = CATEGORIES[category]["value"]
    if version == "latest":
        version = (
            latest
            if not (CATEGORIES[category]["type"] == "glp")
            else glp_latest
        )
    else:
        if version not in versions:
            raise ValueError(
                f"Invalid version: {version}. Allowed versions: {versions}"
            )
    return f"{category_value}/{version}/{api_endpoint}"
