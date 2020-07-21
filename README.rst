============
ipython-flux
============

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

    In [2]: %%flux http://localhost:9999
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


If no connect string is supplied, ``%flux`` will provide a list of existing connections;
however, if no connections have yet been made and the environment variable ``INFLUXDB_V2_URL``
is available, that will be used.


Assignment
----------

Ordinary IPython assignment works for single-line `%flux` queries:

.. code-block:: python

    In [12]: result = %flux from(bucket: "apm_metricset")  |> range(start: 0)

The `<<` operator captures query results in a local variable, and
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

The ``--persist`` argument, with the name of a 
DataFrame object in memory, 
will create a measurement
in the database from the named DataFrame.  

.. code-block:: python

    In [5]: %flux --persist dataframe

    In [6]: %flux from(bucket: "apm_metricset")  | filter(fn: (r) => r["_measurement"] == "dataframe" |> range(start: 0)

.. _Pandas: http://pandas.pydata.org/

Options
-------

``-l`` / ``--connections``
    List all active connections

``-x`` / ``--close <session-name>`` 
    Close named connection 

``-p`` / ``--persist``
    Create a measurement in the database from the named DataFrame

``-a`` / ``--connection_arguments <"{connection arguments}">``
    Specify dictionary of connection arguments to pass to InfluxDB driver

``-f`` / ``--file <path>``
    Run Flux from file at this path

Installing
----------

Install the lastest release with::

    pip install ipython-flux

or download from https://github.com/bonitoo-io/ipython-flux and::

    cd ipython-flux
    sudo python setup.py install

Development
-----------

https://github.com/bonitoo-io/ipython-flux
