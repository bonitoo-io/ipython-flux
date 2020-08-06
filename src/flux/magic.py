from IPython.core.magic import (
    Magics,
    cell_magic,
    line_magic,
    magics_class,
    needs_local_scope,
)
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring
from influxdb_client.client.write_api import SYNCHRONOUS

import flux.parse
from flux.connection import Connection

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
    """Runs Flux statement on a InfluxDB

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
        "-a",
        "--connection_arguments",
        type=str,
        help="specify dictionary of connection arguments to pass to SQL driver",
    )
    @argument("-f", "--file", type=str, help="Run SQL from file at this path")
    @argument(
        "-p",
        "--persist",
        help="create a measurement in the bucket from the named DataFrame",
    )
    @argument(
        "-m",
        "--measurement",
        help="persist dataframe new measurement name",
    )
    @argument(
        "-T",
        "--tags",
        help="persist dataframe list of columns stored as tags",
    )
    @argument(
        "-n",
        "--bucket",
        help="persist dataframe target bucket",
    )
    @argument(
        "--debug",
        action="store_true",
        help="enable verbose mode for InfluxDB client library",
    )

    def execute(self, line="", cell="", local_ns={}):
        """Runs Flux statement against a database, specified by connect string.

        Examples::
          %%flux http://localhost:9999
        from(bucket: "my-bucket") |> range(start: -1h)

        """
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

        try:
            conn = flux.connection.Connection.set(
                conn=parsed["connection"],
                token=args.token,
                org=args.org,
                displaycon=self.displaycon,
                debug=args.debug,
            )
        except Exception as e:
            print(e)
            print(flux.connection.Connection.tell_format())
            return None

        if args.persist:
            return self._persist_dataframe(conn, data_frame=args.persist, measurement=args.measurement,
                                           bucket=args.bucket,
                                           tags=args.tags, user_ns=user_ns)

        if not parsed["flux"]:
            return

        try:
            result = self.run_flux(conn, parsed["flux"], self)
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

    @staticmethod
    def _persist_dataframe(conn: Connection, data_frame: str, measurement: str, tags: str, bucket: str, user_ns):
        tag_columns = None
        if tags is not None:
            tag_columns = tags.split(",")

        # Get the DataFrame from the user namespace
        persist_error = "Syntax: %flux --persist <data_frame_variable> --bucket <bucket_name> --measurement <measurement_name> --tags <tag_column1,tag_column2>"

        if not bucket:
            raise SyntaxError("--bucket parameter is required")

        if not data_frame:
            raise SyntaxError(persist_error)
        try:
            frame = eval(data_frame, user_ns)
        except SyntaxError:
            raise SyntaxError(
                persist_error)
        if not isinstance(frame, DataFrame) and not isinstance(frame, Series):
            raise TypeError("%s is not a Pandas DataFrame or Series" % data_frame)

        # Make a suitable name for the resulting database table
        if measurement is None:
            measurement = data_frame.lower()

        write_api = conn.session.write_api(write_options=SYNCHRONOUS)

        write_api.write(bucket=bucket, record=frame,
                        data_frame_measurement_name=measurement,
                        data_frame_tag_columns=tag_columns)

        write_api.__del__()

        return "Persisted %s" % data_frame

    @staticmethod
    def run_flux(conn: Connection, flux: str, config):
        if flux.strip():
            result = conn.session.query_api().query_data_frame(query=flux)
            if result.empty and config.feedback:
                print(result.rowcount)

            return result
        else:
            return "Connected: %s" % conn.name


def load_ipython_extension(ip):
    """Load the extension in IPython."""
    ip.register_magics(FluxMagic)
