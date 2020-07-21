import json
import re
from string import Formatter

from IPython.core.magic import (
    Magics,
    cell_magic,
    line_magic,
    magics_class,
    needs_local_scope,
)
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

import flux.connection
import flux.parse
import flux.run

try:
    from traitlets.config.configurable import Configurable
    from traitlets import Bool, Int, Unicode
except ImportError:
    from IPython.config.configurable import Configurable
    from IPython.utils.traitlets import Bool, Int, Unicode
try:
    from pandas.core.frame import DataFrame, Series
except ImportError:
    DataFrame = None
    Series = None


@magics_class
class FluxMagic(Magics, Configurable):
    """Runs Flux statement on a InfluxDB, specified by SQLAlchemy connect string.

    %%flux http://localhost:9999
    from(bucket: "my-bucket") |> range(start: -1h)

    Provides the %%flux magic."""

    displaycon = Bool(True, config=True, help="Show connection string after execute")

    short_errors = Bool(
        True,
        config=True,
        help="Don't display the full stacktrace of Flux call command",
    )
    column_local_vars = Bool(
        False, config=True, help="Return data into local variables from column names"
    )
    feedback = Bool(True, config=True, help="Print number of rows affected by DML")

    def __init__(self, shell):
        Configurable.__init__(self, config=shell.config)
        Magics.__init__(self, shell=shell)

        # Add ourself to the list of module configurable via %config
        self.shell.configurables.append(self)

    @needs_local_scope
    @line_magic("flux")
    @cell_magic("flux")
    @magic_arguments()
    @argument("line", default="", nargs="*", type=str, help="flux")
    @argument(
        "-l", "--connections", action="store_true", help="list active connections"
    )
    @argument("-x", "--close", type=str, help="close a session by name")
    @argument(
        "-p",
        "--persist",
        action="store_true",
        help="create a measurement in the bucket from the named DataFrame",
    )
    @argument(
        "-t",
        "--token",
        help="influxdb token",
    )
    @argument(
        "-o",
        "--org",
        help="influxdb org",
    )
    @argument(
        "--append",
        action="store_true",
        help="create, or append to, a table name in the database from the named DataFrame",
    )
    @argument(
        "-a",
        "--connection_arguments",
        type=str,
        help="specify dictionary of connection arguments to pass to SQL driver",
    )
    @argument("-f", "--file", type=str, help="Run SQL from file at this path")
    def execute(self, line="", cell="", local_ns={}):
        """Runs Flux statement against a database, specified by connect string.

        If no database connection has been established, first word
        should be a SQLAlchemy connection string, or the user@db name
        of an established connection.

        Examples::
          %%flux http://localhost:9999
          from(bucket: "my-bucket") |> range(start: -1h)

        """
        # Parse variables (words wrapped in {}) for %%flux magic (for %flux this is done automatically)
        cell_variables = [
            fn for _, fn, _, _ in Formatter().parse(cell) if fn is not None
        ]
        cell_params = {}
        for variable in cell_variables:
            if variable in local_ns:
                cell_params[variable] = local_ns[variable]
            else:
                raise NameError(variable)
        cell = cell.format(**cell_params)

        args = parse_argstring(self.execute, line)
        if args.connections:
            return flux.connection.Connection.connections
        elif args.close:
            return flux.connection.Connection._close(args.close)

        # save globals and locals so they can be referenced in bind vars
        user_ns = self.shell.user_ns.copy()
        user_ns.update(local_ns)

        command_text = " ".join(args.line) + "\n" + cell

        if args.file:
            with open(args.file, "r") as infile:
                command_text = infile.read() + "\n" + command_text

        parsed = flux.parse.parse(command_text, self)

        if args.connection_arguments:
            try:
                # check for string deliniators, we need to strip them for json parse
                raw_args = args.connection_arguments
                if len(raw_args) > 1:
                    targets = ['"', "'"]
                    head = raw_args[0]
                    tail = raw_args[-1]
                    if head in targets and head == tail:
                        raw_args = raw_args[1:-1]
                args.connection_arguments = json.loads(raw_args)
            except Exception as e:
                print(e)
                raise e
        else:
            args.connection_arguments = {}

        try:
            conn = flux.connection.Connection.set(
                url=parsed["connection"],
                token=args.token,
                org=args.org,
                displaycon=self.displaycon,
            )
        except Exception as e:
            print(e)
            print(flux.connection.Connection.tell_format())
            return None

        if args.persist:
            return self._persist_dataframe(parsed["flux"], conn, user_ns, append=False)

        if args.append:
            return self._persist_dataframe(parsed["flux"], conn, user_ns, append=True)

        if not parsed["flux"]:
            return

        try:
            result = flux.run.run_flux(conn, parsed["flux"], self, user_ns)
            if (
                    result is not None
                    and not isinstance(result, str)
                    and self.column_local_vars
            ):
                # Instead of returning values, set variables directly in the
                # users namespace. Variable names given by column names

                if self.autopandas:
                    keys = result.keys()
                else:
                    keys = result.keys
                    result = result.dict()

                if self.feedback:
                    print(
                        "Returning data to local variables [{}]".format(", ".join(keys))
                    )

                self.shell.user_ns.update(result)

                return None
            else:
                if parsed["result_var"]:
                    result_var = parsed["result_var"]
                    print("Returning data to local variable {}".format(result_var))
                    self.shell.user_ns.update({result_var: result})
                    return None
                # Return results into the default ipython _ variable
                return result

        except Exception as e:
            if self.short_errors:
                print(e)
            else:
                raise

    legal_sql_identifier = re.compile(r"^[A-Za-z0-9#_$]+")

    def _persist_dataframe(self, raw, conn: flux.connection.Connection, user_ns, append=False):

        if not DataFrame:
            raise ImportError("Must `pip install pandas` to use DataFrames")

        frame_name = raw.strip(";")

        # Get the DataFrame from the user namespace
        if not frame_name:
            raise SyntaxError("Syntax: %flux --persist <name_of_data_frame>")
        try:
            frame = eval(frame_name, user_ns)
        except SyntaxError:
            raise SyntaxError("Syntax: %flux --persist <name_of_data_frame>")
        if not isinstance(frame, DataFrame) and not isinstance(frame, Series):
            raise TypeError("%s is not a Pandas DataFrame or Series" % frame_name)

        # Make a suitable name for the resulting database table
        measurement_name = frame_name.lower()
        measurement_name = self.legal_sql_identifier.search(measurement_name).group(0)

        if_exists = "append" if append else "fail"

        write_api = conn.session.write_api()
        write_api.write(bucket="my-bucket", record=frame)

        return "Persisted %s" % measurement_name


def load_ipython_extension(ip):
    """Load the extension in IPython."""

    # this fails in both Firefox and Chrome for OS X.
    # I get the error: TypeError: IPython.CodeCell.config_defaults is undefined

    # js = "IPython.CodeCell.config_defaults.highlight_modes['magic_sql'] = {'reg':[/^%%flux/]};"
    # display_javascript(js, raw=True)
    ip.register_magics(FluxMagic)
