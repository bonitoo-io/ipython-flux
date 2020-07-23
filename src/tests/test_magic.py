import time

import pytest
from IPython.testing.globalipapp import get_ipython
from influxdb_client import InfluxDBClient, Organization
from pandas import DataFrame

ip = get_ipython()

test_bucket = "test-bucket-ipython"


@pytest.fixture(scope="session", autouse=True)
def setup(request):
    # prepare something ahead of all tests
    print("Load testing data")

    client = InfluxDBClient(url="http://localhost:9999", token="my-token", org="my-org", debug=True)

    write_api = client.write_api()
    buckets_api = client.buckets_api()
    query_api = client.query_api()

    org = find_my_org(client, "my-org")

    bucket = buckets_api.find_bucket_by_name(bucket_name=test_bucket)
    if bucket is not None:
        buckets_api.delete_bucket(bucket=bucket)

    _point1 = {"measurement": "h2o_feet", "tags": {"location": "coyote_creek"},
               "time": "2009-11-10T22:00:00Z", "fields": {"water_level": 1.0}}
    _point2 = {"measurement": "h2o_feet", "tags": {"location": "coyote_creek"},
               "time": "2009-11-10T23:00:00Z", "fields": {"water_level": 2.0}}
    _point_list = [_point1, _point2]

    bucket = buckets_api.create_bucket(bucket_name=test_bucket, org_id=org.id)
    write_api.write(bucket=bucket.name, record=_point_list)
    time.sleep(1)

    query = 'from(bucket:"{0}") |> range(start: 1970-01-01T00:00:00.000000001Z)'.format(test_bucket)

    flux_result = query_api.query(query)
    assert len(flux_result) == 1

    records = flux_result[0].records
    assert len(records) == 2
    request.addfinalizer(cleanup)


def cleanup():
    print("Run finalizer")


def test_dataframe():
    magic = ip.run_line_magic("load_ext", "flux")
    print(magic)
    magic = ip.run_line_magic("flux", "http://localhost:9999 --token my-token --org my-org")
    print(magic)

    command = """
        from(bucket: "{0}")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "h2o_feet")
    """.format(test_bucket)

    result = ip.run_line_magic("flux", command)
    assert isinstance(result, DataFrame)


def find_my_org(client: InfluxDBClient, org_name: str) -> Organization:
    orgs = client.organizations_api().find_organizations()
    for org in orgs:
        if org.name == org_name:
            return org
