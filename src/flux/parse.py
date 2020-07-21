import itertools
from os.path import expandvars

import six
from six.moves import configparser as CP


def _connection_string(s):
    s = expandvars(s)  # for environment variables
    if "@" in s or "://" in s:
        return s
    return ""


def parse(cell, config):
    """Extract connection info and result variable from SQL
    
    Please don't add any more syntax requiring 
    special parsing.  
    Instead, add @arguments to SqlMagic.execute.
    
    We're grandfathering the 
    connection string and `<<` operator in.
    """

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


def _option_strings_from_parser(parser):
    """Extracts the expected option strings (-a, --append, etc) from argparse parser 

    Thanks Martijn Pieters
    https://stackoverflow.com/questions/28881456/how-can-i-list-all-registered-arguments-from-an-argumentparser-instance

    :param parser: [description]
    :type parser: IPython.core.magic_arguments.MagicArgumentParser 
    """
    opts = [a.option_strings for a in parser._actions]
    return list(itertools.chain.from_iterable(opts))
