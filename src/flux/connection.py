import os

from influxdb_client import InfluxDBClient

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
        return """Connection info needed in format, 
        example: %flux http://localhost:9999/ --token my-token --org my-org"""

    def __init__(self, url=None, token=None, org=None, debug=False):

        if not url:
            url = os.getenv('INFLUXDB_V2_URL')
        if url is None:
            raise Exception("Environment variable $INFLUXDB_V2_URK not set, and no url given.")

        if not token:
            token = os.getenv('INFLUXDB_V2_TOKEN')
        if not token:
            raise Exception("Environment variable $INFLUXDB_V2_TOKEN not set, and no token given.")

        if not org:
            org = os.getenv('INFLUXDB_V2_ORG')
        if org is None:
            raise Exception("Environment variable $INFLUXDB_V2_ORG not set, and no org given.")

        self.name = "%s@%s" % (url or "", org)
        self.session = InfluxDBClient(url=url, token=token, org=org, debug=debug)

        self.session.health()
        self.connections[repr(url)] = self
        Connection.current = self

    @classmethod
    def set(cls, conn, token, org, displaycon, debug):
        "Sets the current database connection"
        if conn:
            if isinstance(conn, Connection):
                cls.current = conn
            else:
                existing = rough_dict_get(cls.connections, conn)

            cls.current = existing or Connection(conn, token, org)

        else:
            if cls.connections:
                if displaycon:
                    print(cls.connection_list())
            else:
                cls.current = Connection(conn, token, org, debug)

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
