============
ipython-flux
============
.. image:: https://circleci.com/gh/bonitoo-io/ipython-flux.svg?style=svg
    :target: https://circleci.com/gh/bonitoo-io/ipython-flux

:Author: Robert Hajek, Bonitoo.io

Introduces a %flux (or %%flux) magic.

Connect to a InfluxDB and run Flux commands within IPython or IPython Notebook.

.. image:: https://raw.github.com/bonitoo-io/ipython-flux/master/examples/example.png
   :width: 600px
   :alt: screenshot of ipython-flux in the Notebook

Examples
--------

.. code-block:: python

    In [1]: %load_ext flux

    In [2]: %%flux http://localhost:9999 --token "my-token" --org my-org
       ...: from(bucket: "apm_metricset")
       ...:   |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
       ...:   |> filter(fn: (r) => r["_measurement"] == "apm_metricset")
       ...:   |> filter(fn: (r) => r["_field"] == "samples_system.process.cpu.total.norm.pct")
       ...:
    Out[2]: ...

After the first connection, connect info can be omitted::

    In [3]: %flux
       ...: from(bucket: "apm_metricset")
       ...:   |> range(start: v.timeRangeStart, stop: v.timeRangeStop)
       ...:   |> filter(fn: (r) => r["_measurement"] == "apm_metricset")
       ...:   |> filter(fn: (r) => r["_field"] == "samples_system.process.cpu.total.norm.pct")

    Out[8]: ...


If no connect string is supplied, ``%flux`` will use environment variables ``INFLUXDB_V2_URL``,
``INFLUXDB_V2_ORG``, ``INFLUXDB_V2_TOKEN`` to create connection into InfluxDB.


Assignment
----------

Ordinary IPython assignment works for single-line ``%flux`` queries:

.. code-block:: python

    In [12]: result = %flux from(bucket: "apm_metricset")  |> range(start: 0)

The ``<<`` operator captures query results in a local variable, and
can be used in multi-line ``%%flux``:

.. code-block:: python

    In [19]: %%flux works << %flux from(bucket: "apm_metricset")
        ...: |> range(start: 0)
        ...:

Pandas
------

result is automatically converted into pandas dataframe

.. code-block:: python

    In [3]: result =  %flux from(bucket: "apm_metricset")  |> range(start: 0)

The ``--persist`` argument, with the name of a DataFrame object in memory will create a measurement
in the database from the named DataFrame.  

.. code-block:: python

    In [1]: %flux --persist <data_frame_variable_name> --bucket my-bucket --measurement <new measurement name> --tags tag_column1,tag_column2

.. _Pandas: http://pandas.pydata.org/

Options
-------

``-l`` / ``--connections``
    List all active connections

``-t`` / ``--token``
    InfluxDB token


``-o`` / ``--org``
    InfluxDB org

``-f`` / ``--file <path>``
    Run Flux from file at this path

``-x`` / ``--close <session-name>`` 
    Close named connection 

Persist options
---------------

``-p`` / ``--persist``
    Create a measurement in the database from the named DataFrame

``-b`` / ``--bucket``
    target bucket name

``-T`` / ``--tags``
    comma separated list of columns that will be stored as tags, rest of columns will be stored as fields

``-m`` / ``--measurement``
    optional, target measurement name, if not specified measurement is taken from dataframe name

Installing
----------

Install the lastest release with::

    pip install ipython-flux

or download from https://github.com/bonitoo-io/ipython-flux and::

    cd ipython-flux
    sudo python setup.py install

Enable IPython flux magic extension in Jupyter notebook using

.. code-block:: python

    In [1]: %load_ext flux

Development
-----------

https://github.com/bonitoo-io/ipython-flux
