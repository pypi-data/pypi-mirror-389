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
#
# *****************************************************************************

import logging
import struct
from os import path
from pathlib import Path

import pytest

from zapf import CommError
from zapf.device import TYPECODE_MAP, typecode_description
from zapf.io import PlcIO
from zapf.proto.sim import SimProtocol
from zapf.scan import Scanner

# ruff: noqa: SLF001


def prettify(data):
    if len(data) == 2:
        val = struct.unpack('H', data)[0]
        return f'{val} {val:#x}'
    if len(data) == 4:
        val_i = struct.unpack('I', data)[0]
        val_f = struct.unpack('f', data)[0]
        return f'{val_i} {val_i:#x} {val_f}'
    if len(data) == 8:
        val_i = struct.unpack('Q', data)[0]
        val_f = struct.unpack('d', data)[0]
        return f'{val_i} {val_i:#x} {val_f}'
    return ''


class TestProtocol(SimProtocol):
    OFFSETS = (0, 0x10000)  # allow trying a failing offset

    def read(self, addr, length):
        try:
            data = super().read(addr, length)
        except Exception as err:
            self.log.warning(f'R {addr:#x} {length} !! {err}')
            raise CommError(f'read failed: {err}') from err
        else:
            self.log.debug(f'R {addr:#x} {length} -> {data} {prettify(data)}')
            return data

    def write(self, addr, data):
        try:
            super().write(addr, data)
        except Exception as err:
            self.log.warning(f'W {addr:#x} {data} {prettify(data)} !! {err}')
            raise CommError(f'write failed: {err}') from err
        else:
            self.log.debug(f'W {addr:#x} {data} {prettify(data)} ok')


PLCIO_CACHE = {}


@pytest.fixture(scope='module', params=['2015_02', '2021_09'])
def plc_io(request):
    if request.param not in PLCIO_CACHE:
        full = Path(__file__).parent / f'testplc_{request.param}.py'
        proto = TestProtocol(f'sim://{full}', logging.getLogger(request.param))
        proto.connect()
        PLCIO_CACHE[request.param] = PlcIO(proto, logging.root)
    return PLCIO_CACHE[request.param]


# Since scope=module does not work properly with the parametrized plc_io,
# we cache ourselves and tear down the running simulators afterwards here.
@pytest.fixture(scope='module', autouse=True)
def plc_io_teardown():
    yield

    for plcio in PLCIO_CACHE.values():
        plcio.proto.disconnect()
    PLCIO_CACHE.clear()


# preselect implemented typecodes from BIG TABLE
tcm = [(t, dinfo) for (t, dinfo) in TYPECODE_MAP.items()
       if dinfo.num_values in [0, 1, 2, 16]
       if dinfo.num_params in [0, 1, 16]
       if dinfo.value_fmt[-1] != 's']

# slice defined typcodes into smaller sets for the specific tests
# These slices are tied to the corresponding tests in test_device
# we split into:
# * readable devices (single value) (contains devices with target too),
# * devices with a target (single value)
# * devices with flat parameters
# * devices with param interface
# * vector devices
TC_READABLE_DEVICES = [t for (t, dinfo) in tcm if dinfo.num_values == 1]
TC_TARGET_DEVICES = [t for (t, dinfo) in tcm if dinfo.num_values == 1
                     if (dinfo.has_target or (t >> 8) in [0x14, 0x15])]
TC_FLAT_DEVICES = [t for (t, dinfo) in tcm if dinfo.num_values == 1
                   if dinfo.num_params >= 1 if not dinfo.has_pctrl]
TC_PARAM_DEVICES = [t for (t, dinfo) in tcm if dinfo.num_params >= 1
                    if dinfo.has_pctrl]
TC_VECTOR_DEVICES = [t for (t, dinfo) in tcm if dinfo.num_values >= 2]
TC_MSGIO_DEVICES = [0x050c]


# pylint: disable=redefined-outer-name, protected-access
def filter_tc(plc_io, tc):
    """Find a zapf-device with the requested typecode.

    Also caches the device list after scanning once.
    """
    if not hasattr(plc_io, '_cached_devlist'):
        try:
            Scanner.IGNORE_BAD_DEVICES = False
            plc_io._cached_devlist = \
                {d.typecode: d for d in Scanner(plc_io, plc_io.log).get_devices()}
        except Exception:
            # make the remaining tests skip instead of making all of them fail
            # with the exact same failure
            plc_io._cached_devlist = {}
            raise
    # find the dev with typecode
    if tc not in plc_io._cached_devlist:
        pytest.skip(f'typecode {tc:#06x} not implemented in '
                    f'{path.basename(plc_io.proto.url)}')  # noqa: PTH119
    return plc_io._cached_devlist[tc], TYPECODE_MAP[tc]


@pytest.fixture(scope='module', params=TC_READABLE_DEVICES,
                ids=typecode_description)
# pylint: disable=redefined-outer-name
def plc_readable_device(plc_io, request):
    return filter_tc(plc_io, request.param)


@pytest.fixture(scope='module', params=TC_TARGET_DEVICES,
                ids=typecode_description)
# pylint: disable=redefined-outer-name
def plc_target_device(plc_io, request):
    return filter_tc(plc_io, request.param)


@pytest.fixture(scope='module', params=TC_FLAT_DEVICES,
                ids=typecode_description)
# pylint: disable=redefined-outer-name
def plc_flat_device(plc_io, request):
    return filter_tc(plc_io, request.param)


@pytest.fixture(scope='module', params=TC_PARAM_DEVICES,
                ids=typecode_description)
# pylint: disable=redefined-outer-name
def plc_param_device(plc_io, request):
    return filter_tc(plc_io, request.param)


@pytest.fixture(scope='module', params=TC_VECTOR_DEVICES,
                ids=typecode_description)
# pylint: disable=redefined-outer-name
def plc_vector_device(plc_io, request):
    return filter_tc(plc_io, request.param)


@pytest.fixture(scope='module', params=TC_MSGIO_DEVICES,
                ids=typecode_description)
# pylint: disable=redefined-outer-name
def plc_msgio_device(plc_io, request):
    return filter_tc(plc_io, request.param)


@pytest.fixture(autouse=True)
def log_fixture(caplog):
    caplog.set_level(logging.INFO)
