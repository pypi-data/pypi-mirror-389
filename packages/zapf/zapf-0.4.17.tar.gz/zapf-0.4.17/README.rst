PILS? Zapf it!
==============

This is a client library for the PILS PLC interface specification,
found here: https://forge.frm2.tum.de/public/doc/plc/master/html/

A minimal example of usage::

    import logging
    import zapf.scan

    # Connection via different protocols is abstracted via URIs.
    # Here we connect via Modbus/TCP using slave number 0.
    URI = 'modbus://my.plc.host:502/0'

    # The Scanner allows reading the PLC's "indexer" which provides
    # all metadata about the PLC and its devices.
    scanner = zapf.scan.Scanner(URI, logging.root)
    plc_data = scanner.get_plc_data()
    print('connected to PLC:', plc_data.plc_name)

    # For each found device, this will create a client object and
    # read the most basic property - the current value.
    for dev in scanner.scan_devices():
        print('got a device:', dev)
        print('device value:', device.read_value())
