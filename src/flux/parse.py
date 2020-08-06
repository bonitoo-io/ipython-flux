from os.path import expandvars


def _connection_string(s):
    s = expandvars(s)  # for environment variables
    if "://" in s:
        return s
    return ""


def parse(cell, config):
    """Extract connection url and result variable"""

    result = {"connection": "", "flux": "", "result_var": None}

    pieces = cell.split(None, 3)
    if not pieces:
        return result
    result["connection"] = _connection_string(pieces[0])
    if result["connection"]:
        pieces.pop(0)
    if len(pieces) > 1 and pieces[1] == "<<":
        result["result_var"] = pieces.pop(0)
        pieces.pop(0)  # discard << operator
    result["flux"] = (" ".join(pieces)).strip()
    return result
