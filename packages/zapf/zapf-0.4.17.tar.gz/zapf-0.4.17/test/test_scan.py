# *****************************************************************************
# PILS PLC client library
# Copyright (c) 2019-2021 by the authors, see LICENSE
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
# Module authors:
#   Georg Brandl <g.brandl@fz-juelich.de>
#   Enrico Faulhaber <enrico.faulhaber@frm2.tum.de>
#
# *****************************************************************************

"""Basic test suite for the scanner."""

from zapf.device import typecode_description
from zapf.scan import Scanner
from zapf.spec import v_2021_09


def test_scan(plc_io):
    scanner = Scanner(plc_io, plc_io.log)

    plc_data = scanner.get_plc_data()
    if plc_data.magicstr == '2015_02':
        assert plc_data.indexer_addr == 64
        assert plc_data.indexer_num_slots == 1
        assert plc_data.indexer_slot_size == 34
        assert plc_data.indexer_data_size == 34
        assert plc_data.indexer_size == 36
        assert plc_data.plc_name == 'lazy test plc'
        assert plc_data.plc_version == '0.0.1-alpha'
    else:
        assert plc_data.magicstr == '2021_09'
        assert plc_data.indexer_addr == 6
        assert (plc_data.indexer_num_slots,
                plc_data.indexer_slot_size) in ((3,64), (4,48))
        assert plc_data.indexer_data_size == \
            plc_data.indexer_num_slots * plc_data.indexer_slot_size
        assert plc_data.indexer_size == 194
        assert plc_data.plc_name == 'testplc_2021_09.py'
        assert plc_data.plc_version == \
            'https://forge.frm2.tum.de/review/mlz/pils/zapf:v2.1-alpha'
        assert plc_data.plc_description == 'simulation for testing zapf'
        assert isinstance(plc_data.query_descriptor(32767), v_2021_09.DebugDescriptor)
        assert plc_data.query_descriptor(32767).text == \
            'PLC_Problem 42, please call 137'
    assert plc_data.plc_author == 'anonymous\nauthor'

    for devinfo in scanner.scan_devices():
        # the test devices have the same name as the typecode description
        max_devname_len = plc_data.indexer_slot_size-21 \
            if plc_data.magicstr == '2021_09' else plc_data.indexer_data_size
        assert typecode_description(devinfo.typecode)[:max_devname_len] == devinfo.name
        # make sure get_info has all required keys in the info dict
        for key in ('description', 'aux', 'params', 'funcs', 'tables',
                    'flags', 'absmin', 'absmax', 'unit'):
            assert key in devinfo.info
