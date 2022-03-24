from datetime import datetime, timedelta

import pytest
from IPython.testing.globalipapp import get_ipython
from influxdb_client import InfluxDBClient, Organization, Point
from influxdb_client.client.write_api import SYNCHRONOUS
from pandas import DataFrame

ip = get_ipython()

influx_url = "http://localhost:8086"
token = "my-token"
my_org = "my-org"
test_bucket = "test_bucket_ipython"


@pytest.fixture(scope="session", autouse=True)
def setup(request):
    print("Load testing data")

    with InfluxDBClient(url=influx_url, token=token, org=my_org, debug=False) as client:
        with client.write_api(write_options=SYNCHRONOUS) as write_api:
            buckets_api = client.buckets_api()
            query_api = client.query_api()
            bucket = buckets_api.find_bucket_by_name(bucket_name=test_bucket)
            if bucket is not None:
                buckets_api.delete_bucket(bucket=bucket)

            bucket = buckets_api.create_bucket(bucket_name=test_bucket, org=my_org)

            num_records = 10
            num_series = 10

            today = datetime.utcnow()
            print("*** Write test series ***")
            for loc in range(num_series):
                for i in range(num_records):
                    time_ = today - timedelta(hours=i + 1)
                    point = Point(measurement_name="h2o_feet") \
                        .time(time_) \
                        .field("water_level", float(i)) \
                        .tag("location", "location_" + str(loc)) \
                        .tag("country", "country_" + str(loc))
                    write_api.write(bucket=bucket.name,
                                    record=point)

        query = 'from(bucket:"{0}") |> range(start: 1970-01-01T00:00:00.000000001Z)'.format(test_bucket)

        flux_result = query_api.query(query)

        assert len(flux_result) == num_series
        records = flux_result[0].records
        assert len(records) == num_records

        ip.run_line_magic("load_ext", "flux")
        ip.run_line_magic("flux", influx_url + " --token my-token --org my-org")
        request.addfinalizer(cleanup)


def cleanup():
    print("Run finalizer")


def test_dataframe():
    command = """
        from(bucket: "{0}")
        |> range(start: 1)
        |> filter(fn: (r) => r["_measurement"] == "h2o_feet")
        |> drop(columns: ["_start", "result", "_stop", "table", "_field","_measurement"])
    """.format(test_bucket)

    result = ip.run_line_magic("flux", command)

    print(result)
    assert isinstance(result, DataFrame)


def test_stocks():
    query = "from(bucket: \"" + test_bucket + """\")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "h2o_feet")
        |> filter(fn: (r) => r["_field"] == "water_level")
        |> filter(fn: (r) => r.location == "location_0")
        |> filter(fn: (r) => r._field == "water_level")
        |> drop(columns: ["_start", "_stop", "table", "_field", "_measurement"])
        |> rename(columns: {_value: "water_level"})
    """

    result = ip.run_line_magic("flux", query)

    print(result)
    assert isinstance(result, DataFrame)


def test_persist_stocks():
    query = """my_dataset << from(bucket: "test_bucket_ipython")
        |> range(start: 0, stop: now())
        |> filter(fn: (r) => r["_measurement"] == "h2o_feet")
        |> filter(fn: (r) => r["_field"] == "water_level")
        |> filter(fn: (r) => r.location == "location_0")
        |> filter(fn: (r) => r._field == "water_level")
        |> drop(columns: ["_start", "_stop", "table", "_field", "_measurement"])
        |> rename(columns: {_value: "water_level"})    
        """
    result = ip.run_line_magic("flux", query)

    assert result is None
    # store in local variable
    result = ip.ns_table['user_local']['my_dataset']

    result = result.drop(columns=['table', 'result'])

    ip.ns_table['user_local']['my_dataset'] = result

    assert isinstance(result, DataFrame)
    magic = ip.run_line_magic("flux",
                              "--persist my_dataset --bucket test_bucket_ipython --measurement new_measurement_name --tags location,country")

    print(magic)


def find_my_org(client: InfluxDBClient, org_name: str) -> Organization:
    orgs = client.organizations_api().find_organizations()
    for org in orgs:
        if org.name == org_name:
            return org
