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
#   Enrico Faulhaber <enrico.faulhaber@frm2.tum.de>
#
# *****************************************************************************

"""Basic test suite for the devices in the testplc."""

# pylint: disable=protected-access
# ruff: noqa: SLF001

import time

import pytest

from zapf import ApiError, CommError
from zapf.device import typecode_description
from zapf.spec import DevStatus, ParamCMDs, decode_bitfield


def test_readable_device(plc_readable_device):
    """Test value/status."""
    # zapf-device, TYPCODE_MAP entry
    dev, _tcme = plc_readable_device

    state, reason, aux, err_id = dev.read_status()
    decode_bitfield(aux, dev.aux_spec)
    decode_bitfield(err_id, dev.errid_spec)

    assert state in [
        DevStatus.IDLE,
        DevStatus.DISABLED,
        DevStatus.WARN,
        DevStatus.START,
        DevStatus.BUSY,
        DevStatus.STOP,
        DevStatus.ERROR,
    ]
    assert typecode_description(dev.typecode).startswith(dev.name)
    assert reason in [0, 1, 2, 4, 8]
    assert err_id == 0

    value = dev.read_value_raw()
    limits = dev.value_info.min_value, dev.value_info.max_value
    assert limits[0] <= value <= limits[1]

    if not dev.target_addr:
        with pytest.raises(ApiError):
            dev.read_target_raw()
        with pytest.raises(ApiError):
            dev.change_target_raw(0)

    if dev.tables:
        # name is specific to testplc...
        assert 'table1' in dev.tables
        assert 'table1' in dev.list_tables()
        for tbl in dev.tables.values():
            nrows, ncols = tbl.get_size()
            collist = tbl.list_columns()
            assert ncols == len(collist)
            # test tables are square (10x10)
            for i, c in enumerate(collist):
                tbl.get_column_valueinfo(c)
                tbl.get_cell(i, c)
                tbl.get_cell(nrows - 1 - i, c)
            assert tbl.list_columns()[3] == 'WarnMax'
            with tbl as t:
                assert t._last_row is None
                t.set_cell(3, 'WarnMax', 98.0)
                assert t._last_row is not None
                assert t.get_cell(3, 3) == 98.0
                tbl.set_cell(3, 3, 87.0)
            assert t._last_row is None

            assert tbl.get_cell(3, 'WarnMax') == 87.0
            with pytest.raises(ApiError):
                tbl.get_cell(33, 3)  # row too big
            with pytest.raises(ApiError):
                tbl.get_cell(-3, 3)  # row negative
            with pytest.raises(ApiError):
                tbl.get_cell(3, 33)  # col too big
            with pytest.raises(ApiError):
                tbl.get_cell(3, -3)  # col negative
            with pytest.raises(ApiError):
                tbl.get_cell(3, 'no such column')  # no such column

            with pytest.raises(ApiError):
                tbl.set_cell(33, 3, 3)  # row too big
            with pytest.raises(ApiError):
                tbl.set_cell(-3, 3, 3)  # row negative
            with pytest.raises(ApiError):
                tbl.set_cell(3, 33, 3)  # col too big
            with pytest.raises(ApiError):
                tbl.set_cell(3, -3, 3)  # col negative
            with pytest.raises(ApiError):
                tbl.set_cell(3, 'no such column', 3)  # no such column
            with pytest.raises(ApiError):
                tbl.set_cell(3, 3, 'bad value type')  # bad value type

    for pn in dev.list_params():
        info = dev.get_param_valueinfo(pn)
        assert info.readonly in (True, False)


def test_target_device(plc_target_device):
    """Test target, moving around."""
    # zapf-device, TYPCODE_MAP entry
    dev, _tcme = plc_target_device

    state, _, _, _ = dev.read_status()

    target = dev.read_target_raw()
    limits = dev.value_info.min_value, dev.value_info.max_value
    assert limits[0] <= target <= limits[1]

    # check precondition before starting a movement
    assert state not in [DevStatus.START, DevStatus.BUSY, DevStatus.STOP]
    assert state in [DevStatus.IDLE, DevStatus.WARN]

    value = dev.read_value_raw()
    target = value + 1
    dev.change_target_raw(target)
    assert dev.read_target_raw() == target

    timesout = time.time() + 1
    # now check for end of movement
    while True:
        state, _, _, _ = dev.read_status()
        value = dev.read_value_raw()
        target = dev.read_target_raw()
        assert state in [
            DevStatus.START,
            DevStatus.BUSY,
            DevStatus.IDLE,
            DevStatus.WARN,
        ]
        if value != target:
            assert state == DevStatus.BUSY
        if state != DevStatus.BUSY:
            assert value == target
            return
        assert time.time() < timesout

    # check enum translation
    if dev.value_info.enum_r:
        val = isinstance(dev.read_value(), str)
        tgt = isinstance(dev.read_target(), str)
        assert val == tgt
        dev.change_target(dev.read_target())


def test_vector_devices(plc_vector_device):
    """Test vector value/status/target/moving around."""
    # zapf-device, TYPCODE_MAP entry
    dev, tcme = plc_vector_device

    has_target, num_values = tcme.has_target, tcme.num_values

    state, _, _, _ = dev.read_status()

    value = dev.read_value_raw()
    assert len(value) == num_values

    limits = dev.value_info.min_value, dev.value_info.max_value
    for v in value:
        assert limits[0] <= v <= limits[1]

    if not has_target:
        with pytest.raises(ApiError):
            dev.read_target_raw()
        with pytest.raises(ApiError):
            dev.change_target_raw(value)
        return

    target = dev.read_target_raw()
    for t in target:
        assert limits[0] <= t <= limits[1]
    if target == value:
        assert state in [DevStatus.IDLE, DevStatus.DISABLED, DevStatus.WARN]
    else:
        assert state in [
            DevStatus.DISABLED,
            DevStatus.START,
            DevStatus.BUSY,
            DevStatus.STOP,
            DevStatus.ERROR,
        ]
    dev.change_target_raw([t+1 for t in target])


def test_flat_device(plc_flat_device):
    """Test flat parameter access."""
    # zapf-device, TYPCODE_MAP entry
    dev, tcme = plc_flat_device

    assert tcme.num_params == len(dev.list_params())

    # check param access of all params
    for p in dev.list_params():
        if p in ['Setpoint', 'Offset']:
            continue
        min_value = dev.get_param_valueinfo(p).min_value
        v = dev.get_param(p)
        if min_value > -1e10:
            dev.set_param(p, min_value + 1)
            assert pytest.approx(min_value + 1) == dev.get_param(p)
        else:
            dev.set_param(p, v + 1)
            assert pytest.approx(v + 1) == dev.get_param(p)

        dev.set_param_raw(p, v)
        assert v == dev.get_param_raw(p)[1]

        if min_value > -1e10:  # doesn't work for default limits
            with pytest.raises(ApiError):
                dev.set_param(p, min_value - 1)

    # check that Setpoint is readable, but not writable
    if 'Setpoint' in dev.list_params():
        dev.get_param('Setpoint')
        assert dev.set_param_raw('Setpoint', 12)[0] == ParamCMDs.ERR_RO


def test_paramif(plc_param_device):
    """Test paramif access + funcs."""
    # zapf-device, TYPCODE_MAP entry
    dev, _tcme = plc_param_device

    # testplc implements a few parameters:
    # readable: 1-3, 32-38, 40, 43, 44, 51-53, 55-65, 68-70
    # writeable: 32-37, 40, 51-53, 56, 57, 60, 61, 69, 70
    # executable: 128, 133, 137, 142
    # 128 and 133 almost instantly go from BUSY to DONE, rest is ERR_RETRY

    # check state
    dev.wait_sm_available(cached=True)
    assert dev.param_sm.CMD != 0

    # basic lowlevel tests

    # set a known paramvalue != 0 first
    fmt = dev.get_param_valueinfo(1).fmt
    # initiate reading parameter 1 (should result in value 0)
    dev.set_pctrl(ParamCMDs.DO_READ, 1, 42, fmt)
    assert dev.wait_sm_available(fmt)
    assert dev.param_sm.CMD == ParamCMDs.DONE
    assert dev.param_value not in (1, None)

    # try to read param 127 (should fail with NO_IDX)
    assert dev.wait_sm_available()
    dev.set_pctrl(ParamCMDs.DO_READ, 127)
    assert dev.wait_sm_available()
    assert dev.param_sm.CMD == ParamCMDs.ERR_NO_IDX

    # try to write param 15 (should fail with RO or NO_IDX, depending on magic)
    assert dev.wait_sm_available()
    dev.set_pctrl(ParamCMDs.DO_WRITE, 18, 42,
                                'I' if dev.value_size == 4 else 'Q')
    assert dev.wait_sm_available()
    assert dev.param_sm.CMD in [ParamCMDs.ERR_NO_IDX, ParamCMDs.ERR_RO]

    # try to exec func 142 (should fail with RETRY)
    assert dev.wait_sm_available()
    dev.set_pctrl(ParamCMDs.DO_WRITE, 142)
    assert dev.wait_sm_available()
    assert dev.param_sm.CMD == ParamCMDs.ERR_RETRY

    # try to 'BUSY' param 1 (should succeed with DONE)
    assert dev.wait_sm_available()
    dev.set_pctrl(ParamCMDs.BUSY, 1, 42, fmt)
    assert dev.wait_sm_available(fmt)
    assert dev.param_sm.CMD == ParamCMDs.DONE
    assert dev.param_value not in (42, None)

    # no fmt -> param_value should be None
    assert dev.wait_sm_available()
    assert dev.param_value is None

    # higher level tests
    if 'UserMax' in dev.list_params():
        v = dev.get_param('UserMax')
        dev.set_param('UserMax', v - 1)
        assert dev.get_param('UserMax') == v - 1

        assert dev.get_param_index('UserMax')
        info = dev.get_param_valueinfo('UserMax')
        assert info.basetype == 'float'
        assert info.fmt in ('f', 'd')
        assert info.unit == dev.info['unit']
        if dev.io.indexer.magicstr == '2021_09':
            assert info.description
            assert info.min_value == 0
            assert info.max_value == 100

    if 'microsteps' in dev.list_params():
        info = dev.get_param_valueinfo('microsteps')
        assert 1 in info.enum_r
        assert info.enum_w['4 steps'] == 2
        dev.set_param('microsteps', '4 steps')
        assert dev.get_param_raw('microsteps')[1] == 2

    if dev.list_funcs():
        dev.exec_func(dev.list_funcs()[0])


def test_msgio_device(plc_msgio_device):
    """Test for msgio."""
    # zapf-device, TYPCODE_MAP entry
    dev, _tcme = plc_msgio_device

    assert dev.communicate(b'Uryyb Jbeyq!') == b'Hello World!'
    s = b'"rot13" is soo much fun, how can one livE without it???!'
    assert dev.communicate(dev.communicate(s)) == s

    # request too long -> error
    with pytest.raises(CommError):
        dev.communicate(s + s)

    # check state (should still be Error)
    assert dev.read_status()[0] == DevStatus.ERROR
    # try to reset + check state afterwards
    dev.reset()
    for i in range(2):
        if dev.read_status()[0] != DevStatus.RESET:
            break
        time.sleep(i * 0.001)
    assert dev.read_status()[0] == DevStatus.IDLE

    # now test read_value/change_target
    with pytest.raises(ApiError):
        dev.change_target_raw(b'X')
    with pytest.raises(ApiError):
        dev.read_target_raw()
    with pytest.raises(ApiError):
        dev.read_value_raw()

    assert dev.communicate([b'Uryyb', b' ', b'Jbeyq!']) == [b'Hello World!']
    with pytest.raises(ApiError):
        dev.communicate([s])
    assert dev.communicate([b'YYYYYYYYYYYYYYYYYYYYZZ', b'YY']) == \
        [b'LLLLLLLLLLLLLLLLLLLLMM', b'LL']
