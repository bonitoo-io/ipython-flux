import os

from influxdb_client import InfluxDBClient


class ConnectionError(Exception):
    pass


def rough_dict_get(dct, sought, default=None):
    """
    Like dct.get(sought), but any key containing sought will do.

    If there is a `@` in sought, seek each piece separately.
    This lets `me@server` match `me:***@myserver/db`
    """

    sought = sought.split("@")
    for (key, val) in dct.items():
        if not any(s.lower() not in key.lower() for s in sought):
            return val
    return default


class Connection(object):
    current = None
    connections = {}

    @classmethod
    def tell_format(cls):
        return """Connection info needed in format, example:
               http://localhost:9999/ --token my-token --org my-org
               or an existing connection: %s""" % str(
            cls.connections.keys()
        )

    def __init__(self, connect_str=None, token=None, org=None):
        self.name = "%s@%s" % (connect_str or "", org)

        if token is None:
            token = os.getenv('INFLUXDB_V2_TOKEN')

        if token is None:
            raise ConnectionError(
                "Environment variable $INFLUXDB_V2_TOKEN not set, and no token given."
            )

        if org is None:
            token = os.getenv('INFLUXDB_V2_ORG')

        if org is None:
            raise ConnectionError(
                "Environment variable $INFLUXDB_V2_ORG not set, and no org given."
            )

        if connect_str:
            self.session = InfluxDBClient(url=connect_str, token=token, org=org)
        else:
            self.session = InfluxDBClient.from_env_properties()

        self.session.health()
        self.connections[repr(connect_str)] = self
        Connection.current = self

    @classmethod
    def set(cls, url, token, org, displaycon):
        "Sets the current database connection"

        if url:
            if isinstance(url, Connection):
                cls.current = url
            else:
                existing = rough_dict_get(cls.connections, url)

            cls.current = existing or Connection(url, token, org)
        else:
            if cls.connections:
                if displaycon:
                    print(cls.connection_list())
            else:
                if os.getenv("INFLUXDB_V2_URL"):
                    cls.current = Connection(
                        os.getenv("INFLUXDB_V2_URL"),os.getenv("INFLUXDB_V2_TOKEN"),os.getenv("")
                    )
                else:
                    raise ConnectionError(
                        "Environment variable $INFLUXDB_V2_URL not set, and no connect string given."
                    )
        return cls.current

    @classmethod
    def connection_list(cls):
        result = []
        for key in sorted(cls.connections):
            if cls.connections[key] == cls.current:
                template = "* {}"
            else:
                template = "  {}"
            result.append(template.format(key.__repr__()))
        return "\n".join(result)

    def _close(cls, descriptor):
        if isinstance(descriptor, Connection):
            conn = descriptor
        else:
            conn = cls.connections.get(descriptor) or cls.connections.get(
                descriptor.lower()
            )
        if not conn:
            raise Exception(
                "Could not close connection because it was not found amongst these: %s"
                % str(cls.connections.keys())
            )
        cls.connections.pop(conn.name)
        conn.session.close()

    def close(self):
        self.__class__._close(self)
