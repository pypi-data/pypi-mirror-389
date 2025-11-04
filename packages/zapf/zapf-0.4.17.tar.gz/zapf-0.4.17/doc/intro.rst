Introduction
============

What is it?
-----------

Zapf is a client library to access PLCs (Programmable logic controllers) that
offer an interface conforming to the **PILS** specification.  The specification
is hosted here:

https://forge.frm2.tum.de/public/doc/plc/master/html/

Zapf provides APIs for:

* Connecting to a PLC via a variety of protocols
* Querying the PLC for its metadata and the available devices
* Creating a client object for each device, according to its :ref:`device type
  <pils:device-types>`
* Fully interacting with the PLC using the device objects

The library abstracts over the different communication protocols and PILS
specification versions.


Example
-------

.. include:: ../README.rst
   :start-line: 6


Installation
------------

Zapf can be installed from PyPI with the usual methods.

Its only (optional) non-standard-library dependency is ``PyTango``, which is
required to communicate using the `Tango <https://tango-controls.org>`_
framework.
