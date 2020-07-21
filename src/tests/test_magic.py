from IPython.testing.globalipapp import get_ipython
from pandas import DataFrame

ip = get_ipython()


def test_dataframe():
    magic = ip.run_line_magic("load_ext", "flux")
    print(magic)
    magic = ip.run_line_magic("flux", "http://localhost:9999 --token my-token --org my-org")
    print(magic)

    command = """
        from(bucket: "_tasks")
        |> range(start: 0)
        |> filter(fn: (r) => r["_measurement"] == "runs")
    """
    result = ip.run_line_magic("flux", command)
    assert isinstance(result, DataFrame)
