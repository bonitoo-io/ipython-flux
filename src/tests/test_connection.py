import os

from IPython.testing.globalipapp import get_ipython

ip = get_ipython()

influx_url = "http://localhost:8086"


def test_env_properties():
    os.environ["INFLUXDB_V2_URL"] = influx_url
    os.environ["INFLUXDB_V2_TOKEN"] = "my-token"
    os.environ["INFLUXDB_V2_ORG"] = "my-org"
    ip.cleanup()

    ip.run_line_magic("load_ext", "flux")
    query = 'from(bucket:"{0}") |> range(start: 1970-01-01T00:00:00.000000001Z)'.format("test-bucket-ipython")
    magic = ip.run_line_magic("flux", query)
    print(magic)


def test_token_argument():
    ip.cleanup()
    ip.run_line_magic("load_ext", "flux")
    ip.run_line_magic("flux", influx_url + " --token \"my-token\" --org my-org")

    query = 'from(bucket:"{0}") |> range(start: 1970-01-01T00:00:00.000000001Z)'.format("test-bucket-ipython")
    magic = ip.run_line_magic("flux", query)
    print(magic)


def test_env_missing_url():
    os.environ["INFLUXDB_V2_URL"] = influx_url
    ip.cleanup()
    ip.run_line_magic("load_ext", "flux")
    query = 'from(bucket:"{0}") |> range(start: 1970-01-01T00:00:00.000000001Z)'.format("test-bucket-ipython")
    magic = ip.run_line_magic("flux", query)
    assert not magic


def test_timeout_argument():
    os.environ["INFLUXDB_V2_URL"] = influx_url
    os.environ["INFLUXDB_V2_TOKEN"] = "my-token"

    ip.cleanup()
    ip.run_line_magic("load_ext", "flux")
    ip.run_line_magic("flux", influx_url + " --timeout 20_000 --org my-org")

    query = 'from(bucket:"{0}") |> range(start: 1970-01-01T00:00:00.000000001Z) |> last()'.format("my-bucket")
    magic = ip.run_line_magic("flux", query)
    print(magic)
