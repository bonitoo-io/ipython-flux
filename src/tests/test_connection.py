import os

from IPython.testing.globalipapp import get_ipython

ip = get_ipython()


def test_env_properties():

    os.environ["INFLUXDB_V2_URL"] = "https://localhost:9999"
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

    ip.run_line_magic("flux", "https://localhost:9999 --token \"my-token\" --org my-org")

    query = 'from(bucket:"{0}") |> range(start: 1970-01-01T00:00:00.000000001Z)'.format("test-bucket-ipython")
    magic = ip.run_line_magic("flux", query)
    print(magic)

def test_env_missing_url():
    os.environ["INFLUXDB_V2_URL"] = "https://localhost:9999"
    ip.cleanup()
    ip.run_line_magic("load_ext", "flux")
    query = 'from(bucket:"{0}") |> range(start: 1970-01-01T00:00:00.000000001Z)'.format("test-bucket-ipython")
    magic = ip.run_line_magic("flux", query)
    assert not magic


