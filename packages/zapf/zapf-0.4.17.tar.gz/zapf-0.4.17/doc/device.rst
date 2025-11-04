.. _device:

The device API
==============

Since PILS structures the PLC functionality into devices as the basic unit,
Zapf provides a wrapper object for each such device.

The concrete class depends on the typecode, but all device classes share the
same interface.


.. currentmodule:: zapf.device

.. autoclass:: Device
   :members:


.. autoclass:: DiscreteDevice
.. autoclass:: SimpleDiscreteIn
.. autoclass:: SimpleDiscreteOut
.. autoclass:: DiscreteIn
.. autoclass:: DiscreteOut
.. autoclass:: Keyword
.. autoclass:: AnalogDevice
.. autoclass:: SimpleAnalogIn
.. autoclass:: SimpleAnalogOut
.. autoclass:: AnalogIn
.. autoclass:: AnalogOut
.. autoclass:: RealValue
.. autoclass:: FlatIn
.. autoclass:: FlatOut
.. autoclass:: ParamIn
.. autoclass:: ParamOut
.. autoclass:: VectorDevice
.. autoclass:: VectorIn
.. autoclass:: VectorOut
.. autoclass:: MessageIO
   :members:


.. attribute:: TYPECODE_MAP

    Maps the PILS :ref:`type code <pils:type-codes>` to a namedtuple with the
    following items:

    * ``devcls``: The concrete `Device` subclass to use
    * ``value_fmt``: The basic Python `struct` format for the device values
    * ``num_values``: The number of main values of the device
    * ``has_target``: If the device has one or more "target" fields
    * ``readonly``: If the device can only be read, not written to.
    * ``status_size``: The size, in bytes, of the device's status fields
    * ``num_params``: The number of parameter fields
    * ``has_pctrl``: Whether this device uses the :ref:`pils:param-ctrl` field

    Most of this information is used by the `Device` classes to determine their
    internal layout.


The spec module
---------------

``zapf.spec`` contains several helpers, enums, and constants that implement
aspects of the PILS specification.

.. currentmodule:: zapf.spec


.. data:: DevStatus

   A mapping-like enumeration of the possible PLC states, see
   :ref:`pils:status-word`.

   * ``DevStatus.RESET`` - device is initializing or command to reset
   * ``DevStatus.IDLE`` - device is idle and fully functional
   * ``DevStatus.DISABLED`` - device is disabled (switched off)
   * ``DevStatus.WARN`` - device is idle and possibly not fully functional
   * ``DevStatus.START`` - command from client to change value
   * ``DevStatus.BUSY`` - device is changing its value
   * ``DevStatus.STOP`` - command from client to stop value change
   * ``DevStatus.ERROR`` - device is unusable due to error
   * ``DevStatus.DIAGNOSTIC_ERROR``

   Apart from ``DevStatus.IDLE`` to get the numeric value, you can also
   get the numeric value using indexing (``DevStatus['IDLE']``), and the
   string value by indexing with the numeric value (``DevStatus[1]``).


.. data:: ReasonMap

   A list of text equivalent strings for the 4-bit "reason" code, see
   :ref:`the spec <pils:reason-bits>`, inside a status word.


.. data:: ParamControl

   A "bit field accessor" like `StatusStruct` for the parameter control field.
   Its subfields are:

   * ``CMD`` - the command as `ParamCMDs`
   * ``SUBINDEX`` - the device subindex for the parameter
   * ``IDX`` - the parameter index


.. data:: ParamCMDs

   This is a mapping-like enumeration of the possible return values of a
   device's :ref:`parameter state machine <pils:param-ctrl>`:

   * ``ParamCMDs.INIT`` - parameter value is invalid, awaiting command
   * ``ParamCMDs.DO_READ`` - command from client to read a value
   * ``ParamCMDs.DO_WRITE`` - command from client to write a value
   * ``ParamCMDs.BUSY`` - request is being processed
   * ``ParamCMDs.DONE`` - request was processed, value field contains
     current value (or return value for special functions)
   * ``ParamCMDs.ERR_NO_IDX`` - parameter does not exist
   * ``ParamCMDs.ERR_RO`` - parameter is read-only
   * ``ParamCMDs.ERR_RETRY`` - parameter can *temporarily* not be changed

   Apart from ``ParamCMDs.DO_READ`` to get the numeric value, you can also
   get the numeric value using indexing (``ParamCMDs['DO_READ']``), and the
   string value by indexing with the numeric value (``ParamCMDs[1]``).


.. data:: Parameters

   The mapping of known parameters and special functions.

   It can be indexed by name (``Parameters['Speed'] == 60``) and by number
   (``Parameters[60] == 'Speed'``).

   Parameters not defined by the spec are given a generic name like
   ``'Param80'``.


.. function:: is_function(index)

   Return true if the given parameter number is a special function.
