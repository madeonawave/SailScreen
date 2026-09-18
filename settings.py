import json

_DEFAULTS = {
    "show_chart": True,  # show the avg-speed chart on the main screen
    "chart_range": 6,  # top of the chart y-axis in knots (6 or 12)
}
_CONFIG_PATH = "/config.json"


def load():
    cfg = {}
    try:
        with open(_CONFIG_PATH) as f:
            cfg = json.load(f)
    except (OSError, ValueError):
        cfg = {}
    if not isinstance(cfg, dict):
        cfg = {}
    out = dict(_DEFAULTS)
    for key in _DEFAULTS:
        if key in cfg and type(cfg[key]) == type(_DEFAULTS[key]):
            out[key] = cfg[key]
    return out


def save(cfg):
    data = dict(_DEFAULTS)
    data.update(cfg or {})
    tmp = _CONFIG_PATH + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    import os

    try:
        os.remove(_CONFIG_PATH)
    except OSError:
        pass
    os.rename(tmp, _CONFIG_PATH)


def defaults():
    return dict(_DEFAULTS)
