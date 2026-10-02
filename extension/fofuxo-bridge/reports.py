"""Bounded reports for conversations; complete reports remain available on request."""

from copy import deepcopy

from . import rounds

MAX_ITEMS = 20


def finish(kind, report, verbose=False):
    result = deepcopy(report)
    if not verbose:
        omitted = {}
        for key in ("moved", "deltas", "blender_edits", "blender_deltas", "annotations", "ops"):
            values = result.get(key)
            if isinstance(values, list) and len(values) > MAX_ITEMS:
                omitted[key] = len(values) - MAX_ITEMS
                result[key] = values[:MAX_ITEMS]
        if "ops" in result:
            result["ops"] = [line.split(";", 1)[0] if isinstance(line, str) else line for line in result["ops"]]
        if omitted:
            result["omitted"] = omitted
        result["detail_hint"] = "verbose=True returns the complete report"
    rounds.record_report(kind, report, result)
    return result
