from datetime import datetime, timedelta, timezone

from pycentral.utils.url_utils import generate_url

from ..exceptions import ParameterError


def build_timestamp_filter(
    start_time=None,
    end_time=None,
    duration=None,
    fmt="rfc3339",
):
    """
    Returns a formatted filter string:
        "timestamp gt <start> and timestamp lt <end>"

    Behavior:
      - If start_time and end_time are given → passes through directly.
      - If duration is given → computes timestamps relative to now.
      - If nothing is given → defaults to last 3 hours.
      - Max supported duration = 3 months.

    Args:
        start_time: RFC3339 or Unix timestamp for start.
        end_time: RFC3339 or Unix timestamp for end.
        duration: String like '3h', '2d', '1w', '1m'.
        fmt: 'rfc3339' or 'unix' for output format.
        default_duration: Used when nothing is provided.

    Returns:
        start_time and end_time
    """
    now = datetime.now(timezone.utc)

    # --- Validation ---
    if (start_time or end_time) and duration:
        raise ValueError(
            "Cannot specify start/end timestamps together with duration."
        )
    if (start_time and not end_time) or (end_time and not start_time):
        raise ValueError(
            "Both start_time and end_time must be provided together."
        )
    if not duration and not (start_time and end_time):
        raise ValueError(
            "Provide either both start_time and end_time or a duration."
        )

    # --- Case 1: Start + End (pass-through) ---
    if start_time and end_time:
        return f"timestamp gt {start_time} and timestamp lt {end_time}"

    # --- Case 2: Duration only ---
    unit = duration[-1].lower()
    value = int(duration[:-1])

    if unit not in {"w", "h", "d", "m"}:
        raise ValueError(
            "Duration must end with w, h, d, or m (weeks, hours, days, mins)."
        )
    if unit == "w":
        delta = timedelta(weeks=value)
    elif unit == "d":
        delta = timedelta(days=value)
    elif unit == "h":
        delta = timedelta(hours=value)
    else:
        delta = timedelta(minutes=value)

    max_period = timedelta(days=90)
    if delta > max_period:
        raise ValueError("Maximum supported duration is 3 months (90 days).")

    start_dt = now - delta
    end_dt = now

    if fmt == "unix":
        start_val = str(int(start_dt.timestamp() * 1000))
        end_val = str(int(end_dt.timestamp() * 1000))
    else:
        start_val = start_dt.isoformat().replace("+00:00", "Z")
        end_val = end_dt.isoformat().replace("+00:00", "Z")
    return start_val, end_val


def generate_timestamp_str(start_time, end_time, duration):
    start_time, end_time = build_timestamp_filter(
        start_time=start_time, end_time=end_time, duration=duration
    )
    return f"timestamp gt {start_time} and timestamp lt {end_time}"


def execute_get(central_conn, endpoint, params={}):
    if not central_conn:
        raise ParameterError("central_conn(Central connection) is required")

    if not endpoint or not isinstance(endpoint, str) and len(endpoint) == 0:
        raise ParameterError("endpoint is required and must be a string")

    if endpoint.startswith("/"):
        # remove leading slash if present
        endpoint = endpoint.lstrip("/")

    path = generate_url(endpoint, "monitoring")
    resp = central_conn.command("GET", path, api_params=params)

    if resp["code"] != 200:
        raise Exception(
            f"Error retrieving data from {path}: {resp['code']} - {resp['msg']}"
        )
    return resp["msg"]


def simplified_site_resp(site):
    site["health"] = _groups_to_dict(site.get("health", {}).get("groups", []))
    site["devices"] = {
        "count": site.get("devices", {}).get("count", 0),
        "health": _groups_to_dict(
            site.get("devices", {}).get("health", {}).get("groups", [])
        ),
    }
    site["clients"] = {
        "count": site.get("clients", {}).get("count", 0),
        "health": _groups_to_dict(
            site.get("clients", {}).get("health", {}).get("groups", [])
        ),
    }
    site["alerts"] = {
        "critical": site.get("alerts", {})
        .get("groups", [{}])[0]
        .get("count", 0)
        if site.get("alerts", {}).get("groups")
        else 0,
        "total": site.get("alerts", {}).get("totalCount", 0),
    }
    site.pop("type", None)
    return site


def _groups_to_dict(groups_list):
    result = {"Poor": 0, "Fair": 0, "Good": 0}
    if isinstance(groups_list, list):
        for group in groups_list:
            if (
                isinstance(group, dict)
                and "name" in group
                and "value" in group
            ):
                result[group["name"]] = group["value"]
    return result


def clean_raw_trend_data(raw_results, data=None):
    if data is None:
        data = {}
    graph = raw_results.get("graph", {}) or {}
    keys = graph.get("keys", []) or []
    samples = graph.get("samples", []) or []

    for s in samples:
        ts = s.get("timestamp")
        if not ts:
            continue
        vals = s.get("data")
        if isinstance(vals, (list, tuple)):
            for k, v in zip(keys, vals):
                data.setdefault(ts, {})[k] = v
        else:
            target_key = keys[0] if keys else None
            if target_key:
                data.setdefault(ts, {})[target_key] = vals
            else:
                # fallback to a generic key if none provided
                data.setdefault(ts, {})["value"] = vals
    return data


def merged_dict_to_sorted_list(merged):
    # try strict RFC3339 parsing (Z -> +00:00), fallback to lexicographic
    try:
        keys = sorted(
            merged.keys(),
            key=lambda t: datetime.fromisoformat(t.replace("Z", "+00:00")),
        )
    except Exception:
        keys = sorted(merged.keys())
    return [{"timestamp": ts, **merged[ts]} for ts in keys]
