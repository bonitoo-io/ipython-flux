import re

from flux.connection import Connection

_cell_with_spaces_pattern = re.compile(r"(<td>)( {2,})")


def interpret_rowcount(rowcount):
    if rowcount < 0:
        result = "Done."
    else:
        result = "%d rows affected." % rowcount
    return result


def run_flux(conn: Connection, flux, config, user_namespace):
    if flux.strip():
        result = conn.session.query_api().query_data_frame(query=flux)
        if result.empty and config.feedback:
            print(interpret_rowcount(result.rowcount))

        return result
    else:
        return "Connected: %s" % conn.name
