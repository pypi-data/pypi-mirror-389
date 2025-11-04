IO and Protocol API
===================

All communication with the PLC is managed by a `PlcIO` instance, which uses one
of the various `Protocol` subclasses for different communication methods.

`PlcIO` also features a cache layer, which automatically polls a registered
range of addresses with a fixed interval, and read accesses from a higher level
(e.g. a device object) go to the cache first.

.. TODO
