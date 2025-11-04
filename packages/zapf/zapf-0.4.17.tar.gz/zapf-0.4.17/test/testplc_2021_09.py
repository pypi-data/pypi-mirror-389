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

# pylint: disable=invalid-name, unused-argument, no-value-for-parameter
# ruff: noqa: N802, N815, E501

from zapf.device import typecode_description
from zapf.simulator.funcs import adr, memcpy, memset, sizeof
from zapf.simulator.runtime import (
    Globals,
    Struct,
    Var,
    array,
    boolean,
    byte,
    dword,
    lreal,
    lword,
    program,
    real,
    string,
    word,
)
from zapf.spec import FLOAT32_MAX
from zapf.spec.v_2021_09 import DEVICE_FLAGS, encode_unit

PILS_MAGIC = 2021.09
DESCRIPTOR_SLOT_SIZE = 48
DESCRIPTOR_SLOTS = 4
INDEXER_DATA_SIZE = DESCRIPTOR_SLOTS * DESCRIPTOR_SLOT_SIZE
INDEXER_SIZE = 2 + INDEXER_DATA_SIZE
INDEXER_OFFSET = 6
MSGIO_NDATA = 22
PARAM_DEFAULTS = [0, 100, 10, 90, 5, 500, 0, 10, 2, 0, 0.125, 0, 10, 1, 0, 0, 0, 0]


class DevicesLayout(Struct):
    # sdi64/sdo64/kv64
    sdx64_value = Var(lword, 0)
    sdx64_target = Var(lword, 0)

    # sai64/sao64/rv64
    sax64_value = Var(lreal, 0)
    sax64_target = Var(lreal, 0)

    # sdi32/sdo32/kv32
    sdx32_value = Var(dword, 0)
    sdx32_target = Var(dword, 0)

    # sai32/sao32/rv32
    sax32_value = Var(real, 0)
    sax32_target = Var(real, 0)

    # sdi16/sdo16/kv16
    sdx16_value = Var(word, 0)
    sdx16_target = Var(word, 0)

    # sw16/sw32
    estatus = Var(dword, 0x20000000)

    # 1e04 = discrete output with extended status
    dox_value = Var(word, 0)
    dox_target = Var(word, 0)
    dox_estatus = Var(dword, 0)

    # msgio (0x050c)
    msg_mbox = Var(word, 0)
    msg_data = Var(array(byte, 0, MSGIO_NDATA-1))

    # di64, do64 (re-using do64_target as di64_value)
    dx64_value = Var(lword, 0)
    dx64_target = Var(lword, 0)
    dx64_estatus = Var(dword, 0x10000000)
    dx64_nerrid = Var(word, 0)
    dx64_reserved = Var(word, 0)

    # di32, do32  (re-using do32_target as di32_value)
    dx32_value = Var(dword, 0)
    dx32_target = Var(dword, 0)
    dx32_estatus = Var(dword, 0x10000000)
    dx32_padding = Var(dword, 0)

    # di16, do16  (re-using do16_target as di16_value)
    dx16_value = Var(word, 0)
    dx16_target = Var(word, 0)
    dx16_status = Var(word, 0x1000)
    dx16_padding = Var(word, 0)

    # ai64, ao64  (re-using ao64_target as ai64_value)
    ax64_value = Var(lreal, 0)
    ax64_target = Var(lreal, 0)
    ax64_estatus = Var(dword, 0x10000000)
    ax64_nerrid = Var(word, 0)
    ax64_reserved = Var(word, 0)

    # ai32, ao32  (re-using ao32_target as ai32_value)
    ax32_value = Var(real, 0)
    ax32_target = Var(real, 0)
    ax32_estatus = Var(dword, 0x10001000)
    ax32_padding = Var(dword, 0)

    #  flatin/out64
    fax64_value = Var(lreal, 50)
    fax64_target = Var(lreal, 50)
    fax64_estatus = Var(dword, 0x10000000)
    fax64_nerrid = Var(word, 0)
    fax64_reserved = Var(word, 0)
    fax64_params = Var(array(lreal, 0, 17), PARAM_DEFAULTS)

    # flatin/out32
    fax32_value = Var(real, 50)
    fax32_target = Var(real, 50)
    fax32_estatus = Var(dword, 0x10001000)
    fax32_params = Var(array(real, 0, 17), PARAM_DEFAULTS)
    fax32_padding = Var(dword, 0)

    # pi/po64
    px64_value = Var(lreal, 50)
    px64_target = Var(lreal, 0)
    px64_estatus = Var(dword, 0x10000000)
    px64_nerrid = Var(word, 0)
    px64_pctl = Var(word, 0)
    px64_pvalue = Var(lreal, 0)

    # pi/po32
    px32_value = Var(real, 50)
    px32_target = Var(real, 0)
    px32_estatus = Var(dword, 0x10000000)
    px32_nerrid = Var(word, 0)
    px32_pctl = Var(word, 0)
    px32_pvalue = Var(real, 0)

    # legacy pi/po32
    lpx32_value = Var(real, 50)
    lpx32_target = Var(real, 0)
    lpx32_status = Var(word, 0x1000)
    lpx32_pctl = Var(word, 0)
    lpx32_pvalue = Var(real, 0)

    # v2i/v2o32
    v2x32_values = Var(array(real, 0, 1))
    v2x32_targets = Var(array(real, 0, 1))
    v2x32_estatus = Var(dword, 0x10000000)
    v2x32_nerrid = Var(word, 0)
    v2x32_pctl = Var(word, 0)
    v2x32_pvalue = Var(real, 0)

    # legacy v2i/v2o32
    lv2x32_values = Var(array(real, 0, 1))
    lv2x32_targets = Var(array(real, 0, 1))
    lv2x32_status = Var(word, 0x1000)
    lv2x32_pctl = Var(word, 0)
    lv2x32_pvalue = Var(real, 0)

    # v2i/v2o64
    v2x64_values = Var(array(lreal, 0, 1))
    v2x64_targets = Var(array(lreal, 0, 1))
    v2x64_estatus = Var(dword, 0x10000000)
    v2x64_nerrid = Var(word, 0)
    v2x64_pctl = Var(word, 0)
    v2x64_pvalue = Var(lreal, 0)

    # v16i/v16o64
    v16x64_values = Var(array(lreal, 0, 15))
    v16x64_targets = Var(array(lreal, 0, 15))
    v16x64_estatus = Var(dword, 0x10000000)
    v16x64_nerrid = Var(word, 0)
    v16x64_pctl = Var(word, 0)
    v16x64_pvalue = Var(lreal, 0)

    # v16i/v16o32
    v16x32_values = Var(array(real, 0, 15))
    v16x32_targets = Var(array(real, 0, 15))
    v16x32_estatus = Var(dword, 0x10000000)
    v16x32_nerrid = Var(word, 0)
    v16x32_pctl = Var(word, 0)
    v16x32_pvalue = Var(real, 0)

    # legacy v16i/v16o32
    lv16x32_values = Var(array(real, 0, 15))
    lv16x32_targets = Var(array(real, 0, 15))
    lv16x32_status = Var(word, 0x1000)
    lv16x32_pctl = Var(word, 0)
    lv16x32_pvalue = Var(real, 0)

    # table storage: 1d
    table64_act_row = Var(word, 0)
    table64_req_row = Var(word, 0)
    table64_line = Var(array(lreal, 0, 9))
    # table storage: 2d, direct mapped
    table64 = Var(array(lreal, 0, 99))

    # table storage: 1d
    table32_act_row = Var(word, 0)
    table32_req_row = Var(word, 0)
    table32_line = Var(array(real, 0, 9))
    # table storage: 2d, direct mapped
    table32 = Var(array(real, 0, 99))

    rv32 = Var(real, 0)
    rv64 = Var(lreal, 0)
    kw64 = Var(lword, 0)
    kw32 = Var(dword, 0)
    kw16 = Var(word, 0)
    padding = Var(word, 0)

    lax32_value = Var(real, 0)
    lax32_target = Var(real, 0)
    lax32_status = Var(word, 0x1000)
    lax32_padding = Var(word, 0)

    lfax32_value = Var(real, 50)
    lfax32_target = Var(real, 50)
    lfax32_status = Var(word, 0x1000)
    lfax32_padding = Var(word, 0)
    lfax32_params = Var(array(real, 0, 17), PARAM_DEFAULTS)


# ensure byte addresses above are accurate
assert DevicesLayout.sizeof() == 2600

alignment_ok = True
for _n, addr in DevicesLayout.OFFSET.items():
    o = getattr(DevicesLayout, _n)
    try:
        size = o.dtype.INNER.sizeof()
    except AttributeError:
        size = o.dtype.sizeof()
    if addr != (addr // size) * size:
        print(f'{_n} is not correctly aligned! (addr={addr}, size={size})')
        alignment_ok = False
assert alignment_ok


def addrof(n):
    return 200 + DevicesLayout.OFFSET[n]


class PLCDescriptor(Struct):
    dt = Var(word, 0x1010)
    devices = Var(word, 0)
    description = Var(word, 0)
    version = Var(word, 0)
    author = Var(word, 0)
    desc_slot_size = Var(word, DESCRIPTOR_SLOT_SIZE)
    num_devices = Var(word, 0)
    flags = Var(word, (DESCRIPTOR_SLOTS - 1) << 12)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 16 - 1), '')
    # flags, desc_slot_size == const, num_devices -> magic!
    keys = 'dt', 'devices', 'description', 'version', 'author', 'name'


class DeviceDescriptor(Struct):
    dt = Var(word, 0x2014)
    prev = Var(word, 0)
    description = Var(word, 0)
    value_param = Var(word, 0)
    aux = Var(word, 0)
    params = Var(word, 0)
    errid = Var(word, 0)
    typecode = Var(word, 0)
    address = Var(word, 0)
    flags = Var(word, 0)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 20 - 1), '')
    keys = 'dt', 'prev', 'description', 'value_param', 'aux', 'params', \
        'errid', 'typecode', 'address', 'flags', 'name'


class StringDescriptor(Struct):
    dt = Var(word, 0x3004)
    prev = Var(word, 0)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 4 - 1), '')
    keys = 'dt', 'prev', 'name'


class EnumDescriptor(Struct):
    dt = Var(word, 0x4006)
    prev = Var(word, 0)
    # don't name a field 'value' or 'addr' or the simulator may ignore writes to it...
    val = Var(word, 0)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 6 - 1), '')
    keys = 'dt', 'prev', 'val', 'name'


class BitfieldDescriptor(Struct):
    dt = Var(word, 0x5008)
    prev = Var(word, 0)
    enum_id = Var(word, 0)
    lsb = Var(byte, 0)
    width = Var(byte, 1)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 8 - 1), '')
    keys = 'dt', 'prev', 'enum_id', 'lsb', 'width', 'name'


class FlagDescriptor(Struct):
    dt = Var(word, 0x5105)
    prev = Var(word, 0)
    lsb = Var(byte, 0)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 5 - 1), '')
    keys = 'dt', 'prev', 'lsb', 'name'


class NumericParameterDescriptor(Struct):
    dt = Var(word, 0x6114)
    prev = Var(word, 0)
    description = Var(word, 0)
    paramidx = Var(word, 0)
    paramtype = Var(word, 0)
    unit = Var(word, 0)
    minval = Var(real, -FLOAT32_MAX)
    maxval = Var(real, FLOAT32_MAX)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 20 - 1), '')
    keys = 'dt', 'prev', 'description', 'paramidx', 'paramtype', 'unit', \
        'minval', 'maxval', 'name'


class EnumParameterDescriptor(Struct):
    dt = Var(word, 0x620E)
    prev = Var(word, 0)
    description = Var(word, 0)
    read_enum_id = Var(word, 0)
    write_enum_id = Var(word, 0)
    paramidx = Var(word, 0)
    paramtype = Var(word, 0)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 14 - 1), '')
    keys = 'dt', 'prev', 'description', 'read_enum_id', 'write_enum_id', \
        'paramidx', 'paramtype', 'name'


class SpecialFuncDescriptor(Struct):
    dt = Var(word, 0x680E)
    prev = Var(word, 0)
    description = Var(word, 0)
    arg_id = Var(word, 0)
    res_id = Var(word, 0)
    paramidx = Var(word, 0)
    paramtype = Var(word, 0)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 14 - 1), '')
    keys = 'dt', 'prev', 'description', 'arg_id', 'res_id', 'paramidx', \
        'paramtype', 'name'


class TableDescriptor(Struct):
    dt = Var(word, 0x6C10)
    prev = Var(word, 0)
    description = Var(word, 0)
    columns = Var(word, 0)
    base = Var(word, 0)
    flags = Var(word, 0)
    last_row = Var(word, 0)
    last_column = Var(word, 0)
    name = Var(string(DESCRIPTOR_SLOT_SIZE - 16 - 1), '')
    keys = 'dt', 'prev', 'description', 'columns', 'base', 'flags', \
        'last_row', 'last_column', 'name'


class DebugDescriptor(Struct):
    dt = Var(word, 0xFF06)
    cycle = Var(word, 0)
    indexer_size = Var(word, 0)
    text = Var(string(INDEXER_DATA_SIZE - 6 - 1), '')  # Yes: this is BIG
    keys = 'dt', 'cycle', 'text'


class ST_Indexer(Struct):  # noqa: N801
    Request = Var(word, 0)
    #    Data = Var(array(U_Descriptor, 0, DESCRIPTOR_SLOTS-1))
    Data = Var(array(array(byte, 0, DESCRIPTOR_SLOT_SIZE - 1), 0, DESCRIPTOR_SLOTS - 1))


# singletons


PLC_DESCRIPTOR = PLCDescriptor(name='testplc_2021_09.py').alloc_self()
DEBUG_DESCRIPTOR = DebugDescriptor(text='PLC_Problem 42, please call 137',
                                   indexer_size=INDEXER_DATA_SIZE).alloc_self()


# map descriptorid/descriptortuple to descriptor
DESCRIPTOR_ARRAY = [PLC_DESCRIPTOR]
descriptors = {}


def add_descr(t, descr):
    # pylint: disable=global-statement
    if t in descriptors:
        return descriptors[t]
    next_descriptor = len(DESCRIPTOR_ARRAY)
    kwds = dict(zip(descr.keys, t))
    d = descr(**kwds).alloc_self()
    descriptors[t] = next_descriptor
    DESCRIPTOR_ARRAY.append(d)
    return next_descriptor


def add_Device(name, typecode, address, description='', value_param=None,
               aux=0, params=0, errid=0, flags=0, unit=''):
    if value_param is None:
        # provide some sensible default for most devices
        if typecode in (0x1201, 0x1401, 0x1602, 0x1A02, 0x1E03, 0x1E04):
            value_param = add_IntParam(0, '', 'rw', 0, -32768, 32767)
        elif typecode in (0x1202, 0x1402, 0x1604, 0x1A04, 0x1E06):
            value_param = add_IntParam(0, '', 'rw', 0, -(2 ** 31), 2 ** 31 - 1)
        elif typecode in (0x1204, 0x1404, 0x1608, 0x1A08, 0x1E0C):
            value_param = add_IntParam(0, '', 'rw', 0, -(2 ** 63), 2 ** 63 - 1)
        elif typecode >> 8 != 5:  # not for MSGIO !
            value_param = add_FloatParam(0, '', 'rw', 0, -FLOAT32_MAX, FLOAT32_MAX,
                                         encode_unit(unit) if isinstance(unit, str) else unit)
        else:
            value_param = 0
    if isinstance(flags, str):
        flags = [flags]
    try:
        int(flags)
    except TypeError:
        f = 0
        for bit, fn in DEVICE_FLAGS.items():
            if fn in flags:
                f |= 1 << bit
        flags = f
    t = (
        0x2014,
        PLC_DESCRIPTOR.devices,
        add_String(description),
        value_param,
        aux,
        params,
        errid,
        typecode,
        address,
        flags,
        name,
    )
    PLC_DESCRIPTOR.devices = add_descr(t, DeviceDescriptor)
    PLC_DESCRIPTOR.num_devices += 1
    # no return....


def add_String(s):
    prev = 0
    while s:
        part, s = s[: DESCRIPTOR_SLOT_SIZE - 4 - 1], s[DESCRIPTOR_SLOT_SIZE - 4 - 1:]
        t = (0x3004, prev, part)
        prev = add_descr(t, StringDescriptor)
    return prev


def add_Enum(prev, val, name):
    t = (0x4006, prev, val, name)
    return add_descr(t, EnumDescriptor)


def add_Enums(prev, enumdict):
    # add all values of a dict to the given chain.
    # XXX: also remove duplicates aready in prev? How?
    for v, n in sorted(enumdict.items()):
        prev = add_Enum(prev, v, n)
    return prev


def add_Bitfield(prev, name, lsb, width, enum):
    if isinstance(enum, dict):
        enum = add_Enums(0, enum)
    t = (0x5008, prev, enum, lsb, width, name)
    return add_descr(t, BitfieldDescriptor)


def add_Flag(prev, lsb, name):
    t = (0x5105, prev, lsb, name)
    return add_descr(t, FlagDescriptor)


def add_BfFChain(prev, chain):
    # chain is an iterable of 2/4 tuples for flags/bitfields
    # flags: (bit, name)
    # bitfield: (name, lsb, width, enumdict)
    for e in chain:
        if len(e) == 2:
            prev = add_Flag(prev, *e)
        elif len(e) == 4:
            prev = add_Bitfield(prev, *e)
        else:
            raise RuntimeError(f'bad Element {e} in Bitfield/Flag Chain: {chain}')
    return prev


WRO_MAP = {'rw': 1, 'ro': 2, 'obs': 3}  # writeable, readonly, observable


def add_IntParam(prev, name, wro, idx, minval, maxval, unit=0, description=''):
    if isinstance(description, str):
        description = add_String(description)
    wro = WRO_MAP.get(wro, wro) & 3
    if isinstance(unit, str):
        unit = encode_unit(unit)
    t = (0x6114, prev, description, idx, (0xC + wro) << 12, unit, minval, maxval, name)
    return add_descr(t, NumericParameterDescriptor)


def add_FloatParam(prev, name, wro, idx, minval, maxval, unit='', description=''):
    if isinstance(description, str):
        description = add_String(description)
    wro = WRO_MAP.get(wro, wro) & 3
    if isinstance(unit, str):
        unit = encode_unit(unit)
    t = (0x6114, prev, description, idx, (0x4 + wro) << 12, unit, minval, maxval, name)
    return add_descr(t, NumericParameterDescriptor)


def add_EnumParam(prev, name, wro, idx, read_enum, write_enum=0, description=''):
    if isinstance(description, str):
        description = add_String(description)
    wro = WRO_MAP.get(wro, wro) & 3
    if read_enum == 0:
        read_enum = write_enum
    if isinstance(read_enum, dict):
        if isinstance(write_enum, dict):
            read_enum.update(write_enum)
        read_enum = add_Enums(0, read_enum)
    if isinstance(write_enum, dict):
        write_enum = add_Enums(0, write_enum)
    t = (0x620E, prev, description, read_enum, write_enum, idx, (0x8 + wro) << 12, name)
    return add_descr(t, EnumParameterDescriptor)


def add_SFunc(prev, name, idx, arg_id, res_id, description=''):
    if isinstance(description, str):
        description = add_String(description)
    t = (0x680E, prev, description, arg_id, res_id, idx, 0, name)
    return add_descr(t, SpecialFuncDescriptor)


def add_Table(prev, name, base, typ, columns, last_row, last_column, description=''):
    if isinstance(description, str):
        description = add_String(description)
    t = (0x6C10, prev, description, columns, base, (typ & 3) << 14, last_row, last_column, name)
    return add_descr(t, TableDescriptor)


# prepare some chains to be used later

AUX8 = add_BfFChain(0, [(d, f'AUX{d}') for d in range(6)] +
                    [('Minion', 6, 2, {1: 'Ape', 2: 'Banana', 3: 'Dragon'})])

AUX24 = add_BfFChain(AUX8, [(d, f'AUX{d}') for d in range(8, 20)] +
                     [('Minion', 6, 3, {4: 'Hamster', 2:''})] +
                     [(d, f'AUX{d}') for d in range(20, 24)] +
                     [('', 21, 1, {1:'aux22', 0:'nix'})]+
                     [('X', 18, 3, {})] +
                     [('', 22, 2, {0:'', 1:'Under voltage', 2:'Over voltage', 3:'no Power'})])

ERRID = add_BfFChain(
    0, [('lowerByte', 0, 8, 0), ('topmost 7 Bit', 9, 7, 0), (8, 'a Flag')],
)

PARS_1 = add_FloatParam(0, 'UserMin', 'rw', 0, 0, 100, '#', 'lower user settable limit')
PARS_2 = add_FloatParam(PARS_1, 'UserMax', 'rw', 1, 0, 100, '#', 'upper user settable limit')
PARS_3 = add_FloatParam(PARS_2, 'WarnMin', 'rw', 2, 0, 100, '#', 'lower warn limit')
PARS_4 = add_FloatParam(PARS_3, 'WarnMax', 'rw', 3, 0, 100, '#', 'upper warn limit')
PARS_5 = add_FloatParam(PARS_4, 'Timeout', 'rw', 4, 0, 900, 's', 'timeout for movement in s')
PARS_6 = add_FloatParam(PARS_5, 'MaxTravelDist', 'rw', 5, 0, 500, '#', 'maximum travel distance')
PARS_7 = add_FloatParam(PARS_6, 'Offset', 'ro', 6, 0, 100, '#', 'internal offset')
PARS_8 = add_FloatParam(PARS_7, 'P', 'rw', 7, 0, 100, '%/(#)', 'P constant for regulation')
PARS_9 = add_FloatParam(PARS_8, 'I', 'rw', 8, 0, 100, 's', 'I constant for regulation')
PARS_10 = add_FloatParam(PARS_9, 'D', 'rw', 9, 0, 100, '1/s', 'D constant for regulation')
PARS_11 = add_FloatParam(PARS_10, 'Hysteresis', 'rw', 10, 0, 100, '#', 'Hysteresis for regulation')
PARS_12 = add_FloatParam(PARS_11, 'Holdback', 'rw', 11, 0, 100, '#', 'max difference between actual temp and setpoint')
PARS_13 = add_FloatParam(PARS_12, 'Speed', 'rw', 12, 0.1, 100, '#/s', 'max speed of movement')
PARS_14 = add_FloatParam(PARS_13, 'Accel', 'rw', 13, 0, 100, '#/s^2', 'acceleration of movement')
PARS_15 = add_FloatParam(PARS_14, 'Home', 'rw', 14, 0, 100, '#', 'Home Position')
PARS_16 = add_FloatParam(PARS_15, 'Setpoint', 'obs', 15, 0, 100, '#', 'actual setpoint')
PARS_17 = add_EnumParam(PARS_16, 'microsteps', 'rw', 16, 0, {s:f'{2**s} steps' for s in range(9)}, 'microstepping selection')
PARS_18 = add_IntParam(PARS_17, 'numbits', 'rw', 17, 1, 32, 'bit', 'number of bits per ssi transfer')

TCOL_ = add_EnumParam(PARS_10, 'enable', 'rw', 0, {2:'enabled', 1:'updating', 0:'ignored'}, {2:'enabled', 0:'ignored'},
                      'en/disable this table row')
TCOL = add_EnumParam(TCOL_, 'microsteps', 'rw', 9, 0, {s:f'{2**s} steps' for s in range(9)}, 'microstepping selection')

SFUNC_1 = add_SFunc(PARS_18, 'reset_to_factory_default', 128,
                    add_IntParam(0, 'unlock_value', 'rw', 0, -2**31, 2**31-1, '', 'Unlock value'),
                    0,
                    'resets everything to factory defaults',
                    )
SFUNC_2 = add_SFunc(SFUNC_1, 'home', 133, 0, 0, 'starts a homing cycle')
SFUNC_3 = add_SFunc(SFUNC_2, 'SetPosition', 137, PARS_15, 0, 'sets a new current position')
SFUNC_4 = add_SFunc(SFUNC_3, 'ContMove', 142, PARS_13, 0, 'Starts a continuous movement')
SFUNC_5 = add_SFunc(SFUNC_4, 'SetBits', 240, PARS_18, PARS_18, 'set and read-back current number of bits')
SFUNC_6 = add_SFunc(SFUNC_5, 'GetBits', 241, 0, PARS_18, 'read-back current number of bits')

TABLE_2 = add_Table(SFUNC_6, 'table2', addrof('table32'), 2, TCOL, 9, 9,
                    '32 bit extra simple 10x10 table, direct mapped')
TABLE_1 = add_Table(TABLE_2, 'table1', addrof('table32_act_row'), 1, TCOL, 9, 9,
                    '32 bit extra simple 10x10 table, with line select')
TABLE32 = add_Table(TABLE_1, 'table0', 1000, 0, TCOL, 9, 9,
                    '32 bit extra simple 10x10 table, via paramctlif')

TABLE_3 = add_Table(SFUNC_6, 'table2', addrof('table64'), 2, TCOL, 9, 9,
                    '64 bit extra simple 10x10 table, direct mapped')
TABLE_4 = add_Table(TABLE_3, 'table1', addrof('table64_act_row'), 1, TCOL, 9, 9,
                    '64 bit extra simple 10x10 table, with line select')
TABLE64 = add_Table(TABLE_4, 'table0', 1000, 0, TCOL, 9, 9,
                    '64 bit extra simple 10x10 table, via paramctlif')

ENUM_1 = add_Enums(0, {0: 'On', 1: 'Off'})
ENUM_2 = add_Enum(ENUM_1, 2, 'Moving')

# vor valuetype
VT_ENUM = add_EnumParam(0, 'ignored pname', 'rw', -1, ENUM_2, ENUM_1, 'ignored description')
VT_SINT16 = add_IntParam(0, 'ignored pname', 'rw', -1, -32768, 32767, 'Ohm', 'signed 16 bit integer')
VT_UINT16 = add_IntParam(0, 'ignored pname', 'rw', -1, 0, 65535, 'bit', 'unsigned 16 bit integer')
VT_SINT32 = add_IntParam(0, 'ignored pname', 'rw', -1, -2**31, 2**31-1, 'counts', 'signed 32 bit integer')
VT_UINT32 = add_IntParam(0, 'ignored pname', 'rw', -1, 0, 2**32-1, '', 'unsigned 32 bit integer')
VT_SINT64 = add_IntParam(0, 'ignored pname', 'rw', -1, -2**63, 2**63-1, '', 'signed 64 bit integer')
VT_UINT64 = add_IntParam(0, 'ignored pname', 'rw', -1, 0, 2**64-1, '', 'unsigned 64 bit integer')
VT_FLOAT32 = add_FloatParam(0, 'ignored pname', 'rw', -1, -FLOAT32_MAX, FLOAT32_MAX, 'cm', '32 bit float')
VT_FLOAT64 = add_FloatParam(0, 'ignored pname', 'rw', -1, -FLOAT32_MAX, FLOAT32_MAX, 'km', '64 bit float')
VT_V2 = add_FloatParam(VT_FLOAT32, 'ignored channel2', 'rw', 42, 0, 137, '%', 'ignored description of second channel')
VT_V3 = add_FloatParam(VT_V2, 'ignored channel3', 'rw', 49, 0, 100, 'kH/min', 'ignored description of 3rd channel')
VT_V4 = add_FloatParam(VT_V3, 'ignored channel4', 'rw', 50, 0, FLOAT32_MAX, '#', 'ignored description of 4th channel')
VT_V5 = add_FloatParam(VT_V4, 'ignored channel5', 'rw', 51, 0, FLOAT32_MAX, 'm', 'ignored description of 5th channel')
VT_V6 = add_FloatParam(VT_V5, 'ignored channel6', 'rw', 52, 0, FLOAT32_MAX, 'm', 'ignored description of 6th channel')
VT_V7 = add_FloatParam(VT_V6, 'ignored channel7', 'rw', 53, 0, FLOAT32_MAX, 'm', 'ignored description of 7th channel')
VT_V8 = add_FloatParam(VT_V7, 'ignored channel8', 'rw', 54, 0, FLOAT32_MAX, 'm', 'ignored description of 8th channel')
VT_V16 = VT_V8
for j in range(9, 17):
    VT_V16 = add_FloatParam(VT_V16, f'ignored channel {j}', 'ro', 60 + j, 0, j * j * j * j * j * j - 1, j,
                            f'ignored description {j}')

# create devices
# note: Name fields will be overriden later in Init().
# here they are only a programming/ers hint.
add_Device('sdi16', 0x1201, addrof('sdx16_value'), value_param=VT_ENUM, description='simple discrete input, 16 bit')
add_Device('sdi32', 0x1202, addrof('sdx32_value'), value_param=VT_SINT32, description='simple discrete input, 32 bit',
           params=TABLE_1)
add_Device('sdi64', 0x1204, addrof('sdx64_value'), value_param=VT_SINT64, description='simple discrete input, 64 bit',
           params=TABLE_4)

add_Device('sai32', 0x1302, addrof('sax32_value'), value_param=VT_FLOAT32, description='simple analog input, 32 bit')
add_Device('sai64', 0x1304, addrof('sax64_value'), value_param=VT_FLOAT64, description='simple analog input, 64 bit')

add_Device('kw16', 0x1401, addrof('kw16'), value_param=VT_UINT16, description='key word, 16 bit')
add_Device('kw32', 0x1402, addrof('kw32'), value_param=VT_UINT32, description='key word, 32 bit')
add_Device('kw64', 0x1404, addrof('kw64'), value_param=VT_UINT64, description='key word, 64 bit')

add_Device('rv32', 0x1502, addrof('rv32'), value_param=VT_FLOAT32, description='real value, 32 bit')
add_Device('rv64', 0x1504, addrof('rv64'), value_param=VT_FLOAT64, description='real value, 64 bit')

add_Device('sdo16', 0x1602, addrof('sdx16_value'), value_param=VT_SINT16, description='simple discrete output, 16 bit')
add_Device('sdo32', 0x1604, addrof('sdx32_value'), value_param=VT_SINT32, description='simple discrete output, 32 bit')
add_Device('sdo64', 0x1608, addrof('sdx64_value'), value_param=VT_SINT64, description='simple discrete output, 64 bit')

add_Device('sao32', 0x1704, addrof('sax32_value'), value_param=VT_FLOAT32, description='simple analog output, 32 bit')
add_Device('sao64', 0x1708, addrof('sax64_value'), value_param=VT_FLOAT64, description='simple analog output, 64 bit')

add_Device('sw16', 0x1801, addrof('estatus')+2, value_param=VT_UINT16, description='status word, 16 bit',
           aux=AUX8)
add_Device('sw32', 0x1802, addrof('estatus'), value_param=VT_UINT32, description='''\
status word, 32 bit

This is a longer description which surely will use more than a single descriptor to store.
it is in 'git' format, i.e. a single line with short 'title', an empty line, followed by a longer
explanation. rst formatting may be used (suggested by Beckhoff).

The device is a special device, reflecting an extended statusword.
There is no functionality behind it (in this implementation).

Let's see how this really long description (with some special utf-8 chars)
is displayed on various clients....

;;; ⁂⁇
''', aux=AUX24)  # noqa: RUF001

add_Device('di16', 0x1a02, addrof('dx16_target'), value_param=VT_UINT16, description=None,
           aux=AUX8)
add_Device('di32', 0x1a04, addrof('dx32_target'), value_param=VT_UINT32, description='discrete input, 32 bit',
           aux=AUX24)
add_Device('di64', 0x1a08, addrof('dx64_target'), value_param=VT_UINT64, description='discrete input, 64 bit',
           aux=AUX24, errid=ERRID)

add_Device('lai32', 0x1b03, addrof('lax32_target'), value_param=VT_FLOAT32, description='legacy analog input, 32 bit',
           aux=AUX8)
add_Device('ai32', 0x1b04, addrof('ax32_target'), unit='kA', description='analog input, 32 bit',
           aux=AUX24)
add_Device('ai64', 0x1b08, addrof('ax64_target'), unit='Mcounts/d', description='analog input, 64 bit',
           aux=AUX24, errid=ERRID)

add_Device('ldo16', 0x1e03, addrof('dx16_value'), value_param=VT_ENUM, description='legacy discrete output, 16 bit',
           aux=AUX8)
add_Device('do16', 0x1e04, addrof('dox_value'), value_param=VT_SINT16, description='discrete output, 16 bit',
           aux=AUX24)
add_Device('do32', 0x1e06, addrof('dx32_value'), value_param=VT_SINT32, description='discrete output, 32 bit',
           aux=AUX24)
add_Device('do64', 0x1e0c, addrof('dx64_value'), value_param=VT_SINT64, description='discrete output, 64 bit',
           aux=AUX24, errid=ERRID)

add_Device('lao32', 0x1f05, addrof('lax32_value'), value_param=VT_FLOAT32, description='legacy analog output, 32 bit',
           aux=AUX8)
add_Device('ao32', 0x1f06, addrof('ax32_value'), unit='kA', description='analog output, 32 bit',
           aux=AUX24)
add_Device('ao64', 0x1f0c, addrof('ax64_value'), value_param=VT_FLOAT64, description='analog output, 64 bit',
           aux=AUX24, errid=ERRID)

add_Device('lfa32i1', 0x2006, addrof('lfax32_target'), unit='mm', description='legacy flat analog input, 32 bit, 1 param',
           aux=AUX8, params=PARS_1)
add_Device('lfa32i16', 0x2f24, addrof('lfax32_target'), unit='mm', description='legacy flat analog input, 32 bit, 16 params',
           aux=AUX8, params=PARS_16, errid=ERRID)

add_Device('fa32i1', 0x6006, addrof('fax32_target'), unit='mm', description='flat analog input, 32 bit, 1 param',
           aux=AUX8, params=PARS_1)
add_Device('fa32i16', 0x6f24, addrof('fax32_target'), unit='mm', description='flat analog input, 32 bit, 16 params',
           aux=AUX8, params=PARS_16, errid=ERRID)

add_Device('fa64i1', 0x200c, addrof('fax64_target'), unit='mm', description='flat analog input, 64 bit, 1 param',
           aux=AUX24, params=PARS_1)
add_Device('fa64i16', 0x2f48, addrof('fax64_target'), unit='mm', description='flat analog input, 64 bit, 16 params',
           aux=AUX24, params=PARS_16, errid=ERRID)

add_Device('lfa32o1', 0x3008, addrof('lfax32_value'), unit='mm', description='legacy flat analog output, 32 bit, 1 param',
           aux=AUX8, params=PARS_1)
add_Device('lfa32o16', 0x3f26, addrof('lfax32_value'), unit='mm', description='legacy flat analog output, 32 bit, 16 params',
           aux=AUX8, params=PARS_16, errid=ERRID)

add_Device('fa32o1', 0x7008, addrof('fax32_value'), unit='mm', description='flat analog output, 32 bit, 1 param',
           aux=AUX8, params=PARS_1)
add_Device('fa32o16', 0x7f26, addrof('fax32_value'), unit='mm', description='flat analog output, 32 bit, 16 params',
           aux=AUX8, params=PARS_16, errid=ERRID)

add_Device('fa64o1', 0x3010, addrof('fax64_value'), unit='mm', description='flat analog output, 64 bit, 1 param',
           aux=AUX24, params=PARS_1)
add_Device('fa64o16', 0x3f4c, addrof('fax64_value'), unit='mm', description='flat analog output, 64 bit, 16 params',
           aux=AUX24, params=PARS_16,errid=ERRID)

add_Device('lpi32', 0x4006, addrof('lpx32_target'), unit='%', description='legacy parameter input, 32 bit',
           aux=AUX8, params=SFUNC_6, errid=ERRID)
add_Device('pi32', 0x4008, addrof('px32_target'), unit='%', description='parameter output, 32 bit',
           aux=AUX24, params=TABLE32, errid=ERRID)
add_Device('lpo32', 0x5008, addrof('lpx32_value'), value_param=0, description='legacy parameter input, 32 bit',
           aux=AUX8, params=SFUNC_6, errid=ERRID)
add_Device('po32', 0x500a, addrof('px32_value'), unit='%', description='parameter output, 32 bit',
           aux=AUX24, errid=ERRID, params=TABLE32)

add_Device('pi64', 0x400c, addrof('px64_target'), unit='%', description='parameter input, 64 bit',
           aux=AUX24, params=TABLE64, errid=ERRID)
add_Device('po64', 0x5010, addrof('px64_value'), unit='%', description='parameter output, 64 bit',
           aux=AUX24, params=TABLE64, errid=ERRID)

add_Device('lv2i32', 0x4108, addrof('lv2x32_targets'), value_param=VT_V2, description='legacy vector 2 input, 32 bit',
           aux=AUX8, params=SFUNC_6)
add_Device('lv16i32', 0x4f24, addrof('lv16x32_targets'), value_param=VT_V16, description='legacy vector 16 input, 32 bit',
           aux=AUX8, params=SFUNC_6)

add_Device('v2i32', 0x410a, addrof('v2x32_targets'), value_param=VT_V2, description='vector 2 input, 32 bit',
           aux=AUX24, params=SFUNC_6)
add_Device('v16i32', 0x4f26, addrof('v16x32_targets'), value_param=VT_V16, description='vector 16 input, 32 bit',
           aux=AUX24, params=SFUNC_6)

add_Device('lv2o32', 0x510c, addrof('lv2x32_values'), value_param=VT_V2, description='legacy vector 2 output, 32 bit',
           aux=AUX8, params=SFUNC_6)
add_Device('lv16o32', 0x5f44, addrof('lv16x32_values'), value_param=VT_V16, description='legacy vector 16 output, 32 bit',
           aux=AUX8, params=SFUNC_6)

add_Device('v2o32', 0x510e, addrof('v2x32_values'), value_param=VT_V2, description='vector 2 output, 32 bit',
           aux=AUX24, params=SFUNC_6)
add_Device('v16o32', 0x5f46, addrof('v16x32_values'), value_param=VT_V16, description='vector 16 output, 32 bit',
           aux=AUX24, params=SFUNC_6)

add_Device('v2i64', 0x4110, addrof('v2x64_targets'), value_param=VT_V2, description='vector 2 input, 64 bit',
           aux=AUX24, params=SFUNC_6)
add_Device('v16i64', 0x4f48, addrof('v16x64_targets'), value_param=VT_V16, description='vector 16 input, 64 bit',
           aux=AUX24, params=SFUNC_6)

add_Device('v2o64', 0x5118, addrof('v2x64_values'), value_param=VT_V2, description='vector 2 output, 64 bit',
           aux=AUX24, params=SFUNC_6)
add_Device('v16o64', 0x5f88, addrof('v16x64_values'), value_param=VT_V16, description='vector 16 output, 64 bit',
           aux=AUX24, params=SFUNC_6)

add_Device('msg22', 0x0501 + MSGIO_NDATA//2, addrof('msg_mbox'), description='MessageIO with 22 bytes data area')


PLC_DESCRIPTOR.description = add_String('simulation for testing zapf')
PLC_DESCRIPTOR.version = add_String('https://forge.frm2.tum.de/review/mlz/pils/zapf:v2.1-alpha')
PLC_DESCRIPTOR.author = add_String('anonymous\nauthor')


class Global(Globals):
    fMagic = Var(real, PILS_MAGIC, at='%MB0')
    iOffset = Var(word, INDEXER_OFFSET, at='%MB4')

    stIndexer = Var(ST_Indexer, at=f'%MB{INDEXER_OFFSET}')

    data = Var(DevicesLayout, at='%MB200')

    iCycle = Var(word, 0)


g = Global()

@program(
    nDevices = Var(word),
    devnum = Var(word),
    infotype = Var(word),
    itemp = Var(byte),
    tempofs = Var(word),
)
def Indexer(_v):
    if g.fMagic != PILS_MAGIC:
        g.fMagic = PILS_MAGIC
    if g.iOffset != INDEXER_OFFSET:
        g.iOffset = INDEXER_OFFSET

    g.iCycle += 1

    req_num = g.stIndexer.Request & 0x7FFF

    data = g.stIndexer.Data

    memset(adr(data), 0, sizeof(data))

    if req_num == 32767:
        DEBUG_DESCRIPTOR.cycle = g.iCycle
        memcpy(adr(data), adr(DEBUG_DESCRIPTOR), sizeof(DEBUG_DESCRIPTOR))
    else:
        for i in range(DESCRIPTOR_SLOTS):
            if req_num + i < len(DESCRIPTOR_ARRAY):
                memcpy(adr(data) + i*DESCRIPTOR_SLOT_SIZE,
                       adr(DESCRIPTOR_ARRAY[req_num + i]),
                       DESCRIPTOR_SLOT_SIZE)

    g.stIndexer.Request[[15]] = 1


# helper
def advance32(value, target, status, usermin=0.0, usermax=100.0,
              warnmin=10.0, warnmax=90.0, speed=10.0):
    state = status >> 12
    reason = 0
    if state == 0:
        state = 1
    elif state in [1, 3, 7]:
        state = 1 if warnmin <= value <= warnmax else 3
    elif state == 5:
        state, reason = (6, 0) if usermin <= target <= usermax else (8, 1)
    elif state == 6:
        if value == target:
            state, reason = 1, 0
        value += max(min((target - value), speed / 20), -speed / 20)
    target = max(min(usermax, target), usermin)
    if value < warnmin:
        reason |= 4
    if value > warnmax:
        reason |= 8

    return value, target, (state << 12) | (reason << 8) | (1 << ((g.iCycle >> 9) & 7))


# same as above but for 32 bit status fields
def advance64(value, target, status, *args, **kwds):
    v, t, s = advance32(value, target, max(status >> 16, status & 0xFFFF), *args, **kwds)
    return v, t, s << 16 | s


# pylint: disable=too-many-return-statements
def handle_pctl(pctl, pvalue, valuestore, tablestore):
    pnum = pctl & 8191
    cmd = pctl >> 13
    if pctl & 0x8000:
        # nothing to do
        return pctl, pvalue
    if not cmd:
        return 0x2000, pvalue
    if pnum in [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16,
                17, 128, 133, 137, 142, 240, 241] or 1000 <= pnum <= 1099:
        # param exists, can at least be read
        if cmd == 1:  # DO_READ
            if 0 <= pnum <= 17:
                # return DONE and value
                return 0x8000 | pnum, valuestore[pnum]
            if pnum == 240:
                return 0x8000 | pnum, valuestore[17]
            if pnum == 241:
                return 0x8000 | pnum, valuestore[17]
            if 1000 <= pnum <= 1099:
                # table access
                # return DONE and value
                return 0x8000 | pnum, float(tablestore[pnum - 1000])
            # invent value and DONE
            return 0x8000 | pnum, 0
        if cmd == 2:  # DO_WRITE
            if 0 <= pnum <= 17:
                valuestore[pnum] = pvalue
                return 0x2000 | pnum, pvalue  # -> read
            if pnum == 240:
                valuestore[17] = pvalue
                return 0x8000 | pnum, valuestore[17]
            if pnum == 241:
                return 0x8000 | pnum, valuestore[17]
            if 128 <= pnum <= 239:
                # go to BUSY for some and ERR_RETRY for others
                if pnum in (128, 133):
                    return 0x6000 | pnum, pvalue
                return 0xE000 | pnum, pvalue  # ERR_RETRY
            if 1000 <= pnum <= 1099:
                tablestore[pnum - 1000] = float(pvalue)
                return 0x2000 | pnum, pvalue  # -> read
            # no function, no storage -> ERR_READ_ONLY
            return 0xC000 | pnum, pvalue
        if cmd == 3:  # BUSY
            return 0x2000 | pnum, pvalue
        raise RuntimeError(f'handle_pctl({pctl}, {pvalue}, {valuestore}): '
                           'This should never happen!')
    # non exisiting param -> ERR_NO_IDX
    return 0xA000 | pnum, pvalue


def handle_sxo(value, target, step):
    """Handle the simple a/d outputs."""
    if value < target:
        return min(value + step, target)
    if value > target:
        return max(value - step, target)
    return value


def handle_dx16(value, target, status):
    if status >> 12 == 5:
        return target, 0x6000
    return value, 0x1000


def handle_dx32(value, target, status):
    v, s = handle_dx16(value, target, max(status >> 16, status & 0xFFFF))
    return v, s << 16 | s


@program(msg=Var(array(byte, 0, 80)), msglen=Var(byte, 0))
def Implementation(v):
    d = g.data

    if g.iCycle & 0x3FF == 0:
        d.kw16 = 1 << (g.iCycle >> 12)
        d.kw32 = 1 << (g.iCycle >> 11)
        d.kw64 = 1 << (g.iCycle >> 10)

    d.sax64_value = handle_sxo(d.sax64_value, d.sax64_target, 0.12)
    d.sax32_value = handle_sxo(d.sax32_value, d.sax32_target, 0.12)

    d.sdx64_value = handle_sxo(d.sdx64_value, d.sdx64_target, 1)
    d.sdx32_value = handle_sxo(d.sdx32_value, d.sdx32_target, 1)
    d.sdx16_value = handle_sxo(d.sdx16_value, d.sdx16_target, 1)

    d.ax64_value, d.ax64_target, d.ax64_estatus = advance64(
        d.ax64_value, d.ax64_target, d.ax64_estatus,
    )
    d.ax64_nerrid = d.ax64_estatus >> 15 if d.ax64_estatus[[31]] else 0

    d.ax32_value, d.ax32_target, d.ax32_estatus = advance64(
        d.ax32_value, d.ax32_target, d.ax32_estatus,
    )
    d.lax32_value, d.lax32_target, d.lax32_status = advance32(
        d.lax32_value, d.lax32_target, d.lax32_status,
    )

    d.dx16_target &= 0x3FFF
    d.dx16_value, d.dx16_status = handle_dx16(
        d.dx16_value, d.dx16_target, d.dx16_status,
    )

    d.dx32_target &= 0xFFFFFF
    d.dx32_value, d.dx32_estatus = handle_dx32(
        d.dx32_value, d.dx32_target, d.dx32_estatus,
    )

    d.dx64_target &= 0xFFFFFFFF
    d.dx64_value, d.dx64_estatus = handle_dx32(
        d.dx64_value, d.dx64_target, d.dx64_estatus,
    )
    d.dx64_nerrid = d.dx16_value

    d.dox_value, d.dox_estatus = handle_dx32(d.dox_value, d.dox_target, d.dox_estatus)

    for i in range(16):
        d.fax64_params[i] = max(0, d.fax64_params[i])
    d.fax64_value, d.fax64_target, d.fax64_estatus = advance64(
        d.fax64_value, d.fax64_target, d.fax64_estatus,
        usermin=d.fax64_params[0], usermax=d.fax64_params[1],
        warnmin=d.fax64_params[2], warnmax=d.fax64_params[3],
        speed=d.fax64_params[12],
    )
    d.fax64_nerrid = d.fax64_estatus >> 15 if d.fax64_estatus[[31]] else 0

    for i in range(16):
        d.fax32_params[i] = max(0, d.fax32_params[i])
    d.fax32_value, d.fax32_target, d.fax32_estatus = advance64(
        d.fax32_value, d.fax32_target, d.fax32_estatus,
        usermin=d.fax32_params[0], usermax=d.fax32_params[1],
        warnmin=d.fax32_params[2], warnmax=d.fax32_params[3],
        speed=d.fax32_params[12],
    )

    for i in range(16):
        d.lfax32_params[i] = max(0, d.lfax32_params[i])
    d.lfax32_value, d.lfax32_target, d.lfax32_status = advance32(
        d.lfax32_value, d.lfax32_target, d.lfax32_status,
        usermin=d.lfax32_params[0], usermax=d.lfax32_params[1],
        warnmin=d.lfax32_params[2], warnmax=d.lfax32_params[3],
        speed=d.lfax32_params[12],
    )

    # pi/po share params with fax
    d.px64_value, d.px64_target, d.px64_estatus = advance64(
        d.px64_value, d.px64_target, d.px64_estatus,
        usermin = d.fax64_params[0], usermax = d.fax64_params[1],
        warnmin = d.fax64_params[2], warnmax = d.fax64_params[3],
        speed = d.fax64_params[12],
    )
    d.px64_nerrid = d.px64_estatus >> 15 if d.px64_estatus[[31]] else 0
    d.px64_pctl, d.px64_pvalue = handle_pctl(
        d.px64_pctl, d.px64_pvalue, d.fax64_params, d.table64,
    )

    d.px32_value, d.px32_target, d.px32_estatus = advance64(
        d.px32_value, d.px32_target, d.px32_estatus,
        usermin = d.fax32_params[0], usermax = d.fax32_params[1],
        warnmin = d.fax32_params[2], warnmax = d.fax32_params[3],
        speed = d.fax32_params[12],
    )
    d.px32_nerrid = d.px32_estatus >> 15 if d.px32_estatus[[31]] else 0
    d.px32_pctl, d.px32_pvalue = handle_pctl(
        d.px32_pctl, d.px32_pvalue, d.fax32_params, d.table32,
    )

    d.lpx32_value, d.lpx32_target, d.lpx32_status = advance32(
        d.lpx32_value, d.lpx32_target, d.lpx32_status,
        usermin = d.fax32_params[0], usermax = d.fax32_params[1],
        warnmin = d.fax32_params[2], warnmax = d.fax32_params[3],
        speed = d.fax32_params[12],
    )
    d.lpx32_pctl, d.lpx32_pvalue = handle_pctl(
        d.lpx32_pctl, d.lpx32_pvalue, d.fax32_params, d.table32,
    )

    # v*x devices are pain
    maxstat = 0
    for i in range(2):
        d.v2x64_values[i], d.v2x64_targets[i], stat = advance64(
            d.v2x64_values[i], d.v2x64_targets[i], d.v2x64_estatus,
            usermin=d.fax64_params[0], usermax=d.fax64_params[1],
            warnmin=d.fax64_params[2], warnmax=d.fax64_params[3],
            speed=d.fax64_params[12],
        )
        maxstat = max(maxstat, stat)
    d.v2x64_estatus = maxstat
    d.v2x64_nerrid = d.v2x64_estatus >> 15 if d.v2x64_estatus[[31]] else 0
    d.v2x64_pctl, d.v2x64_pvalue = handle_pctl(
        d.v2x64_pctl, d.v2x64_pvalue, d.fax64_params, d.table64,
    )

    maxstat = 0
    for i in range(16):
        d.v16x64_values[i], d.v16x64_targets[i], stat = advance64(
            d.v16x64_values[i], d.v16x64_targets[i], d.v16x64_estatus,
            usermin=d.fax64_params[0], usermax=d.fax64_params[1],
            warnmin=d.fax64_params[2], warnmax=d.fax64_params[3],
            speed=d.fax64_params[12],
        )
        maxstat = max(maxstat, stat)
    d.v16x64_estatus = maxstat
    d.v16x64_nerrid = d.v16x64_estatus >> 15 if d.v16x64_estatus[[31]] else 0
    d.v16x64_pctl, d.v16x64_pvalue = handle_pctl(
        d.v16x64_pctl, d.v16x64_pvalue, d.fax64_params, d.table64,
    )

    maxstat = 0
    for i in range(2):
        d.v2x32_values[i], d.v2x32_targets[i], stat = advance64(
            d.v2x32_values[i], d.v2x32_targets[i], d.v2x32_estatus,
            usermin=d.fax32_params[0], usermax=d.fax32_params[1],
            warnmin=d.fax32_params[2], warnmax=d.fax32_params[3],
            speed=d.fax32_params[12],
        )
        maxstat = max(maxstat, stat)
    d.v2x32_estatus = maxstat
    d.v2x32_nerrid = d.v2x32_estatus >> 15 if d.v2x32_estatus[[31]] else 0
    d.v2x32_pctl, d.v2x32_pvalue = handle_pctl(
        d.v2x32_pctl, d.v2x32_pvalue, d.fax32_params, d.table32,
    )

    maxstat = 0
    for i in range(16):
        d.v16x32_values[i], d.v16x32_targets[i], stat = advance64(
            d.v16x32_values[i], d.v16x32_targets[i], d.v16x32_estatus,
            usermin=d.fax32_params[0], usermax=d.fax32_params[1],
            warnmin=d.fax32_params[2], warnmax=d.fax32_params[3],
            speed=d.fax32_params[12],
        )
        maxstat = max(maxstat, stat)
    d.v16x32_estatus = maxstat
    d.v16x32_nerrid = d.v16x32_estatus >> 15 if d.v16x32_estatus[[31]] else 0
    d.v16x32_pctl, d.v16x32_pvalue = handle_pctl(
        d.v16x32_pctl, d.v16x32_pvalue, d.fax32_params, d.table32,
    )

    maxstat = 0
    for i in range(2):
        d.lv2x32_values[i], d.lv2x32_targets[i], stat = advance32(
            d.lv2x32_values[i], d.lv2x32_targets[i], d.lv2x32_status,
            usermin=d.fax32_params[0], usermax=d.fax32_params[1],
            warnmin=d.fax32_params[2], warnmax=d.fax32_params[3],
            speed=d.fax32_params[12],
        )
        maxstat = max(maxstat, stat)
    d.lv2x32_status = maxstat
    d.lv2x32_pctl, d.lv2x32_pvalue = handle_pctl(
        d.lv2x32_pctl, d.lv2x32_pvalue, d.fax32_params, d.table32,
    )

    maxstat = 0
    for i in range(16):
        d.lv16x32_values[i], d.lv16x32_targets[i], stat = advance32(
            d.lv16x32_values[i], d.lv16x32_targets[i], d.lv16x32_status,
            usermin=d.fax32_params[0], usermax=d.fax32_params[1],
            warnmin=d.fax32_params[2], warnmax=d.fax32_params[3],
            speed=d.fax32_params[12],
        )
        maxstat = max(maxstat, stat)
    d.lv16x32_status = maxstat
    d.lv16x32_pctl, d.lv16x32_pvalue = handle_pctl(
        d.lv16x32_pctl, d.lv16x32_pvalue, d.fax32_params, d.table32,
    )

    # handle msgio
    def rot13(c):
        if (65 <= c <= 77) or (97 <= c <= 109):
            return c + 13
        if (78 < c <= 90) or (110 <= c <= 122):
            return c - 13
        return c

    if d.msg_mbox >> 13 == 0:
        v.msglen = 0
        d.msg_mbox = 1 << 13
    elif d.msg_mbox >> 13 == 2:
        # partial request -> put to stack
        d.msg_mbox = 3 << 13
        for i in range(MSGIO_NDATA):
            c = d.msg_data[i]
            if c:
                if v.msglen >= 79:
                    # Error: request too long
                    d.msg_mbox = 7 << 13
                    break
                v.msg[v.msglen] = rot13(c)
                v.msglen = v.msglen + 1
            else:
                break
    elif d.msg_mbox >> 13 == 4:
        # final request part-> put to stack
        for i in range(MSGIO_NDATA):
            c = d.msg_data[i]
            if c:
                if v.msglen >= 79:
                    # Error: request too long
                    d.msg_mbox = 7 << 13
                    break
                v.msg[v.msglen] = rot13(c)
                v.msglen = v.msglen + 1
            else:
                break
    if d.msg_mbox >> 13 in (4, 6):
        if v.msglen > 0:
            # transfer size
            ts = min(MSGIO_NDATA, int(v.msglen))
            memcpy(adr(d.msg_data[0]), adr(v.msg[0]), ts)
            v.msglen = v.msglen - ts
            if v.msglen:
                memcpy(adr(v.msg[0]), adr(v.msg[MSGIO_NDATA]), v.msglen)
            d.msg_mbox = (5 << 13 if v.msglen else 1 << 13) + ts
        else:
            d.msg_mbox = 7 << 13

    # handle table lines
    if d.table32_req_row != d.table32_act_row:
        # write back
        memcpy(
            adr(d.table32) + 40 * d.table32_act_row,
            adr(d.table32_line),
            sizeof(d.table32_line),
        )
        # avoid illegal values for req_row
        if not 0 <= d.table32_req_row <= 9:
            d.table32_req_row = d.table32_act_row
        # read from table
        memcpy(
            adr(d.table32_line),
            adr(d.table32) + 40 * d.table32_req_row,
            sizeof(d.table32_line),
        )
        d.table32_act_row = d.table32_req_row

    if d.table64_req_row != d.table64_act_row:
        # write back
        memcpy(
            adr(d.table64) + 80 * d.table64_act_row,
            adr(d.table64_line),
            sizeof(d.table64_line),
        )
        # avoid illegal values for req_row
        if not 0 <= d.table64_req_row <= 9:
            d.table64_req_row = d.table64_act_row
        # read from table
        memcpy(
            adr(d.table64_line),
            adr(d.table64) + 80 * d.table64_req_row,
            sizeof(d.table64_line),
        )
        d.table64_act_row = d.table64_req_row


@program()
def Init(_v):
    i = PLC_DESCRIPTOR.devices
    while i:
        DESCRIPTOR_ARRAY[i].name = typecode_description(DESCRIPTOR_ARRAY[i].typecode)[:DESCRIPTOR_SLOT_SIZE - 21]
        i = DESCRIPTOR_ARRAY[i].prev


@program(is_initialized=Var(boolean, default=False))
def Main(v):
    if not v.is_initialized:
        Init()
        v.is_initialized = True
    Indexer()
    Implementation()
