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
# ruff: noqa: N802, N815

from itertools import count

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
from zapf.spec.v_2015_02 import is_function

PILS_MAGIC = 2015.02
INDEXER_DATA_SIZE = 34
INDEXER_SIZE = INDEXER_DATA_SIZE + 2
INDEXER_OFFSET = 64
REAL_MAX = 3.402823e38
MSGIO_NDATA = 22


class ST_Indexer(Struct):  # noqa: N801
    Request = Var(word, 0)
    Data = Var(array(word, 1, INDEXER_DATA_SIZE // 2))


class DevicesLayout(Struct):
    # note: with this mapping a sensible sim isn't possible
    # as we don't know which of the overlayed devs was started...

    # used for ai64, ao64, rv64  (re-using aox_target as aix_value, rv64)
    ax64_value = Var(lreal, 0)             # 0..7
    ax64_target = Var(lreal, 0)            # 8..15
    ax64_estatus = Var(dword, 0x10000000)  # 16..19
    ax64_nerrid = Var(word, 0)             # 20..21
    ax64_reserved = Var(word, 0)           # 22..23
    # used for ai32, ao32, sw32 (re-using aox_target as aix_value)
    ax32_value = Var(real, 0)              # 24..27
    ax32_target = Var(real, 0)             # 28..31
    ax32_estatus = Var(dword, 0x10000000)  # 32..35
    # used for legacy_ai32, _ao32, rv32, sw16  (re-using aox_target as aix_value, rv32)
    lax32_value = Var(real, 0)             # 36..39
    lax32_target = Var(real, 0)            # 40..43
    lax32_status = Var(word, 0x1000)       # 44..45
    # used for di16, do16, kv16, sw16 (re-using dox_target as dix_value)
    dx16_value = Var(word, 0)              # 46..47
    dx16_target = Var(word, 0)             # 48..49
    dx16_status = Var(word, 0x1000)        # 50..51
    # used for di32, do32, kv32, sw32  (re-using dox_target as dix_value)
    dx32_value = Var(dword, 0)             # 52..55
    dx32_target = Var(dword, 0)            # 56..59
    dx32_estatus = Var(dword, 0x10000000)  # 60..63
    # used for sdi64, sdo64, di64, do64, kv64 (re-using dox_target as dix_value)
    dx64_value = Var(lword, 0)             # 64..71
    dx64_target = Var(lword, 0)            # 72..79
    dx64_estatus = Var(dword, 0x10000000)  # 80..83
    dx64_nerrid = Var(word, 0)             # 84..85
    dx64_reserved = Var(word, 0)           # 86..87
    # used for all flatin/out in 64 bit (re-using fo_target as fi_value)
    fax64_value = Var(lreal, 50)           # 88..95
    fax64_target = Var(lreal, 50)          # 96..103
    fax64_estatus = Var(dword, 0x10000000) # 104..107
    fax64_nerrid = Var(word, 0)            # 108..109
    fax64_reserved = Var(word, 0)          # 110..111
    # 112..239
    fax64_params = Var(array(lreal, 0, 15),
                       [0, 100, 10, 90, 5, 500, 0, 10, 2, 0, 0.125, 0, 10, 1, 0, 0])

    # used for all pi/po/vectorin/out in 64 (re-using vo_target(s) as vi_value(s))
    # 240..495
    vx64_valuetargets = Var(array(lreal, 0, 31), [0] * 32)
    vx64_estatus = Var(dword, 0x10000000)  # 496..499
    vx64_nerrid = Var(word, 0)             # 500..501
    vx64_pctl = Var(word, 0)               # 502..503
    vx64_pvalue = Var(lreal, 0)            # 504..511
    # used for all pi/po/vectorin/out in 32 (re-using vo_target(s) as vi_value(s))
    # 512..639
    vx32_valuetargets = Var(array(real, 0, 31), [0] * 32)
    vx32_status = Var(word, 0x1000)        # 640..641
    vx32_pctl = Var(word, 0)               # 642..643
    vx32_pvalue = Var(real, 0)             # 644..647
    # used for all flatin/out in 32 bit (re-using fo_target as fi_value)
    fax32_value = Var(real, 50)            # 648..651
    fax32_target = Var(real, 50)           # 652..655
    fax32_status = Var(word, 0x1000)       # 656..657
    fax32_reserved = Var(word, 0)          # 658..659
    # 660..723
    fax32_params = Var(array(real, 0, 15),
                       [0, 100, 10, 90, 5, 500, 0, 10, 2, 0, 0.125, 0, 10, 1, 0, 0])
    # sai/sao in 32/64 sdi/sdo in 16/32/64
    sao64_value = Var(lreal, 0)            # 724..732
    sao64_target = Var(lreal, 0)           # 732..739
    sdo64_value = Var(lword, 0)            # 740..747
    sdo64_target = Var(lword, 0)           # 748..755
    sao32_value = Var(real, 0)             # 756..759
    sao32_target = Var(real, 0)            # 760..763
    sdo32_value = Var(dword, 0)            # 764..767
    sdo32_target = Var(dword, 0)           # 768..771
    sdo16_value = Var(word, 0)             # 772..773
    sdo16_target = Var(word, 0)            # 774..775
    # 1e04 = discrete output with extended status
    dox_value = Var(word, 0)               # 776..777
    dox_target = Var(word, 0)              # 778..779
    dox_estatus = Var(dword, 0)            # 780..783
    # msgio (0x050c)
    msg_mbox = Var(word, 0)                # 784..785
    msg_data = Var(array(byte, 0, MSGIO_NDATA-1))  # 786..807


# ensure byte addresses above are accurate
assert DevicesLayout.sizeof() == 808


class ST_DeviceInfo(Struct):  # noqa: N801
    TypCode = Var(word, 0)
    Size = Var(word, 0)
    Offset = Var(word, 0)
    Unit = Var(word, 0)
    Flags = Var(dword, 0)
    Params = Var(array(word, 1, 16), [0] * 16)
    Name = Var(string(34))
    Aux = Var(array(string(34), 0, 23))
    AbsMax = Var(real, REAL_MAX)
    AbsMin = Var(real, -REAL_MAX)


AUX8 = [f'AUX bit {i}/8' for i in range(8)]
AUX24 = [f'AUX bit {i}/24' for i in range(24)]
# for devices with flat params
PARS_1 = [0x20, 0]
PARS_8 = [0x2120, 0x2322, 0x2524, 0x3328, 0]
PARS_16 = [0x2120, 0x2322, 0x2524, 0x3328, 0x3534, 0x3938, 0x3D3C, 0x4645, 0]
# for devices with parameter interface
PARAM_BITMAP = [0xE, 0, 0x197F, 0xFFB8, 0x73, 0x0, 0x0, 0x0, 0x4221]
WRITEABLE_PARAMS = []
for p in PARS_16:
    WRITEABLE_PARAMS.append(p & 255)
    WRITEABLE_PARAMS.append(p // 256)


class Global(Globals):
    fMagic = Var(real, PILS_MAGIC, at='%MB0')
    iOffset = Var(word, INDEXER_OFFSET, at='%MB4')

    stIndexer = Var(ST_Indexer, at=f'%MB{INDEXER_OFFSET}')

    data = Var(DevicesLayout, at='%MB200')

    # note: Name fields will be overriden later in Init().
    # here they are only a programming/ers hint.
    Devices = Var(array(ST_DeviceInfo, 1, 59), [
        ST_DeviceInfo(TypCode=0x1201, Name='sdi16', Offset=200+772),
        ST_DeviceInfo(TypCode=0x1202, Name='sdi32', Offset=200+764),
        ST_DeviceInfo(TypCode=0x1204, Name='sdi64', Offset=200+740),
        ST_DeviceInfo(TypCode=0x1302, Name='sai32', Offset=200+756),
        ST_DeviceInfo(TypCode=0x1304, Name='sai64', Offset=200+724),
        ST_DeviceInfo(TypCode=0x1401, Name='kw16', Offset=200+48),
        ST_DeviceInfo(TypCode=0x1402, Name='kw32', Offset=200+56),
        ST_DeviceInfo(TypCode=0x1404, Name='kw64', Offset=200+72),
        ST_DeviceInfo(TypCode=0x1502, Name='rv32', Offset=200+40),
        ST_DeviceInfo(TypCode=0x1504, Name='rv64', Offset=200+8),
        ST_DeviceInfo(TypCode=0x1602, Name='sdo16', Offset=200+772),
        ST_DeviceInfo(TypCode=0x1604, Name='sdo32', Offset=200+764),
        ST_DeviceInfo(TypCode=0x1608, Name='sdo64', Offset=200+740),
        ST_DeviceInfo(TypCode=0x1704, Name='sao32', Offset=200+756),
        ST_DeviceInfo(TypCode=0x1708, Name='sao64', Offset=200+724),
        ST_DeviceInfo(TypCode=0x1801, Name='sw16', Offset=200+44, Aux=AUX8),
        ST_DeviceInfo(TypCode=0x1802, Name='sw32', Offset=200+32, Aux=AUX24),
        ST_DeviceInfo(TypCode=0x1a02, Name='di16', Offset=200+48, Aux=AUX8),
        ST_DeviceInfo(TypCode=0x1a04, Name='di32', Offset=200+56, Aux=AUX24),
        ST_DeviceInfo(TypCode=0x1a08, Name='di64', Offset=200+72, Aux=AUX24),
        ST_DeviceInfo(TypCode=0x1b03, Name='lai32', Offset=200+40, Aux=AUX8),
        ST_DeviceInfo(TypCode=0x1b04, Name='ai32', Offset=200+28, Aux=AUX24),
        ST_DeviceInfo(TypCode=0x1b08, Name='ai64', Offset=200+8, Aux=AUX24),
        ST_DeviceInfo(TypCode=0x1e03, Name='do16', Offset=200+46, Aux=AUX8),
        ST_DeviceInfo(TypCode=0x1e06, Name='do32', Offset=200+52, Aux=AUX24),
        ST_DeviceInfo(TypCode=0x1e0c, Name='do64', Offset=200+64, Aux=AUX24),
        ST_DeviceInfo(TypCode=0x1f05, Name='lao32', Offset=200+36, Aux=AUX8),
        ST_DeviceInfo(TypCode=0x1f06, Name='ao32', Offset=200+24, Aux=AUX24),
        ST_DeviceInfo(TypCode=0x1f0c, Name='ao64', Offset=200+0, Aux=AUX24),

        ST_DeviceInfo(TypCode=0x2006, Name='fa32i1', Offset=200+652,
                      Unit=0xfd04, Aux=AUX8, Params=PARS_1),
        ST_DeviceInfo(TypCode=0x2714, Name='fa32i8', Offset=200+652,
                      Unit=0xfd04, Aux=AUX8, Params=PARS_8),
        ST_DeviceInfo(TypCode=0x2f24, Name='fa32i16', Offset=200+652,
                      Unit=0xfd04, Aux=AUX8, Params=PARS_16),

        ST_DeviceInfo(TypCode=0x200c, Name='fa64i1', Offset=200+96,
                      Unit=0xfd04, Aux=AUX24, Params=PARS_1),
        ST_DeviceInfo(TypCode=0x2728, Name='fa64i8', Offset=200+96,
                      Unit=0xfd04, Aux=AUX24, Params=PARS_8),
        ST_DeviceInfo(TypCode=0x2f48, Name='fa64i16', Offset=200+96,
                      Unit=0xfd04, Aux=AUX24, Params=PARS_16),

        ST_DeviceInfo(TypCode=0x3008, Name='fa32o1', Offset=200+648,
                      Unit=0xfd04, Aux=AUX8, Params=PARS_1),
        ST_DeviceInfo(TypCode=0x3716, Name='fa32o8', Offset=200+648,
                      Unit=0xfd04, Aux=AUX8, Params=PARS_8),
        ST_DeviceInfo(TypCode=0x3f26, Name='fa32o16', Offset=200+648,
                      Unit=0xfd04, Aux=AUX8, Params=PARS_16),

        ST_DeviceInfo(TypCode=0x3010, Name='fa64o1', Offset=200+88,
                      Unit=0xfd04, Aux=AUX24, Params=PARS_1),
        ST_DeviceInfo(TypCode=0x372c, Name='fa64o8', Offset=200+88,
                      Unit=0xfd04, Aux=AUX24, Params=PARS_8),
        ST_DeviceInfo(TypCode=0x3f4c, Name='fa64o16', Offset=200+88,
                      Unit=0xfd04, Aux=AUX24, Params=PARS_16),

        ST_DeviceInfo(TypCode=0x4006, Name='pi32', Offset=200+636,
                      Unit=0xfe00, Aux=AUX8, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x5008, Name='po32', Offset=200+632,
                      Unit=0xfe00, Aux=AUX8, Params=PARAM_BITMAP),

        ST_DeviceInfo(TypCode=0x400c, Name='pi64', Offset=200+488,
                      Unit=0xfe00, Aux=AUX24, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x5010, Name='po64', Offset=200+480,
                      Unit=0xfe00, Aux=AUX24, Params=PARAM_BITMAP),

        ST_DeviceInfo(TypCode=0x4108, Name='v2i32', Offset=200+632,
                      Unit=0xfe00, Aux=AUX8, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x4714, Name='v8i32', Offset=200+608,
                      Unit=0xfe00, Aux=AUX8, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x4f24, Name='v16i32', Offset=200+576,
                      Unit=0xfe00, Aux=AUX8, Params=PARAM_BITMAP),

        ST_DeviceInfo(TypCode=0x510c, Name='v2o32', Offset=200+624,
                      Unit=0xfe00, Aux=AUX8, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x5724, Name='v8o32', Offset=200+576,
                      Unit=0xfe00, Aux=AUX8, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x5f44, Name='v16o32', Offset=200+512,
                      Unit=0xfe00, Aux=AUX8, Params=PARAM_BITMAP),

        ST_DeviceInfo(TypCode=0x4110, Name='v2i64', Offset=200+480,
                      Unit=0xfe00, Aux=AUX24, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x4728, Name='v8i64', Offset=200+432,
                      Unit=0xfe00, Aux=AUX24, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x4f48, Name='v16i64', Offset=200+368,
                      Unit=0xfe00, Aux=AUX24, Params=PARAM_BITMAP),

        ST_DeviceInfo(TypCode=0x5118, Name='v2o64', Offset=200+464,
                      Unit=0xfe00, Aux=AUX24, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x5748, Name='v8o64', Offset=200+368,
                      Unit=0xfe00, Aux=AUX24, Params=PARAM_BITMAP),
        ST_DeviceInfo(TypCode=0x5f88, Name='v16o64', Offset=200+240,
                      Unit=0xfe00, Aux=AUX24, Params=PARAM_BITMAP),

        ST_DeviceInfo(TypCode=0x1e04, Name='dox', Offset=200+776),

        ST_DeviceInfo(TypCode=0x0501 + MSGIO_NDATA//2,
                      Name='msg22', Offset=200 + 784),
    ])

    sPLCName = Var(string(34), 'lazy test plc')
    sPLCVersion = Var(string(34), '0.0.1-alpha')
    sPLCAuthor1 = Var(string(34), 'anonymous')
    sPLCAuthor2 = Var(string(34), 'author')
    iCycle = Var(word, 0)


g = Global()


@program(
    nDevices = Var(word),
    devnum = Var(word),
    infotype = Var(word),
    is_initialized = Var(boolean, default=False),
    itemp = Var(byte),
    tempofs = Var(word),
)
def Indexer(v):
    if not v.is_initialized:
        v.tempofs = g.iOffset + sizeof(g.stIndexer)
        v.nDevices = sizeof(g.Devices) // sizeof(g.Devices[1])
        v.itemp = 1
        while v.itemp <= v.nDevices:
            dev = g.Devices[v.itemp]
            for i in range(24):
                dev.Flags[[i]] = len(dev.Aux[i]) > 0
            dev.Size = max(dev.Size, (dev.TypCode & 0xFF) << 1)
            if dev.Offset == 0:
                dev.Offset = v.tempofs
            else:
                v.tempofs = dev.Offset
            v.tempofs += dev.Size
            v.itemp += 1
        v.is_initialized = True

    if g.fMagic != PILS_MAGIC:
        g.fMagic = PILS_MAGIC
    if g.iOffset != INDEXER_OFFSET:
        g.iOffset = INDEXER_OFFSET

    req_num = g.stIndexer.Request & 0x7FFF
    v.devnum = req_num & 0xFF
    v.infotype = req_num >> 8

    data = g.stIndexer.Data

    # short cut, if there is no request, do nothing.
    if g.stIndexer.Request[[15]] == 1:
        if v.infotype == 127:
            data[1] = g.iCycle

        g.iCycle += 1
        return

    memset(adr(data), 0, sizeof(data))

    if v.devnum == 0:
        if v.infotype == 0:
            data[1] = 0
            data[2] = sizeof(g.stIndexer)
            data[3] = g.iOffset
            data[4] = 0
            data[5] = v.nDevices
            data[6] = 0x8200
        elif v.infotype == 1:
            data[1] = sizeof(g.stIndexer)
        elif v.infotype == 4:
            memcpy(adr(data), adr(g.sPLCName), min(sizeof(g.sPLCName), sizeof(data)))
        elif v.infotype == 5:
            memcpy(
                adr(data), adr(g.sPLCVersion), min(sizeof(g.sPLCVersion), sizeof(data)),
            )
        elif v.infotype == 6:
            memcpy(
                adr(data), adr(g.sPLCAuthor1), min(sizeof(g.sPLCAuthor1), sizeof(data)),
            )
        elif v.infotype == 7:
            memcpy(
                adr(data), adr(g.sPLCAuthor2), min(sizeof(g.sPLCAuthor2), sizeof(data)),
            )
    elif v.devnum <= v.nDevices:
        dev = g.Devices[v.devnum]
        if v.infotype == 0:
            data[1] = dev.TypCode
            data[2] = dev.Size
            data[3] = dev.Offset
            data[4] = dev.Unit
            data[5] = dev.Flags
            data[6] = dev.Flags >> 16
            memcpy(adr(data[7]), adr(dev.AbsMin), sizeof(dev.AbsMin))
            memcpy(adr(data[9]), adr(dev.AbsMax), sizeof(dev.AbsMax))
            memcpy(
                adr(data[11]), adr(dev.Name), min(sizeof(dev.Name), sizeof(data) - 20),
            )
        elif v.infotype == 1:
            data[1] = dev.Size
        elif v.infotype == 2:
            data[1] = dev.Offset
        elif v.infotype == 3:
            data[1] = dev.Unit
        elif v.infotype == 4:
            memcpy(adr(data), adr(dev.Name), min(sizeof(dev.Name), sizeof(data)))
        elif v.infotype == 8:
            memcpy(adr(data), adr(dev.descr), sizeof(dev.descr))
        elif v.infotype == 15:
            memcpy(adr(data), adr(dev.Params), min(sizeof(dev.Params), sizeof(data)))
        elif v.infotype >= 0x10 and v.infotype <= 0x27:
            memcpy(
                adr(data),
                adr(dev.Aux[v.infotype - 0x10]),
                min(sizeof(dev.Aux[v.infotype - 0x10]), sizeof(data)),
            )

    if v.infotype == 127:
        data[1] = g.iCycle

    g.stIndexer.Request[[15]] = 1
    g.iCycle += 1


# helper
def advance32(value, target, status, usermin=0.0, usermax=100.0,
              warnmin=10.0, warnmax=90.0, speed=10.0):
    state = status >> 12
    reason = 0
    if state == 0:
        state = 1, 0
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

    return value, target, (state << 12) | (reason << 8)


# same as above but for 32 bit status fields
def advance64(value, target, status, *args, **kwds):
    v, t, s = advance32(value, target, status >> 16, *args, **kwds)
    return v, t, s << 16


# pylint: disable=too-many-return-statements
def handle_pctl(pctl, pvalue, valuestore):
    if pctl & 0x8000:
        # nothing to do
        return pctl, pvalue
    pnum = pctl & 8191
    if pnum > len(PARAM_BITMAP) * 16:
        # non exisiting param -> ERR_NO_IDX
        return 0xA000 | pnum, pvalue
    if (PARAM_BITMAP[pnum // 16] >> (pnum & 15)) & 1 == 0:
        # Param not in our declared param list -> ERR_NO_IDX
        return 0xA000 | pnum, pvalue
    # param exists, can at least be read
    cmd = pctl >> 13
    if cmd == 0:  # INIT
        return 0x8000, 0
    if cmd == 1:  # DO_READ
        if pnum in WRITEABLE_PARAMS:
            # return value and DONE
            return 0x8000 | pnum, valuestore[WRITEABLE_PARAMS.index(pnum)]
        # invent value and DONE
        # HACK: pnums <= 30 should be ints: fake this by returning 0
        return 0x8000 | pnum, 0 if pnum <= 30 else pnum ** 1.5
    if cmd == 2:  # DO_WRITE
        if pnum in WRITEABLE_PARAMS:
            valuestore[WRITEABLE_PARAMS.index(pnum)] = pvalue
            return 0x6000 | pnum, pvalue  # -> BUSY
        if is_function(pnum):
            # go to BUSY for some and ERR_RETRY for others
            if pnum in (128, 133):
                return 0x6000 | pnum, pvalue
            return 0xE000 | pnum, pvalue  # ERR_RETRY
        # no function, no storage -> ERR_READ_ONLY
        return 0xC000 | pnum, pvalue
    if cmd == 3:  # BUSY
        return 0x2000 | pnum, pvalue
    raise RuntimeError(
        f'handle_pctl({pctl}, {pvalue}, {valuestore}): This should never happen!',
    )


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
    v, s = handle_dx16(value, target, status >> 16)
    return v, s << 16


@program(
    msg=Var(array(byte, 0, 80)),
    msglen=Var(byte, 0),
)
def Implementation(v):
    d = g.data

    d.ax64_value, d.ax64_target, d.ax64_estatus = advance64(
        d.ax64_value, d.ax64_target, d.ax64_estatus,
    )
    d.ax64_nerrid = d.ax64.estatus >> 15 if d.ax64_estatus[[31]] else 0

    d.ax32_value, d.ax32_target, d.ax32_estatus = advance64(
        d.ax32_value, d.ax32_target, d.ax32_estatus,
    )

    d.lax32_value, d.lax32_target, d.lax32_status = advance32(
        d.lax32_value, d.lax32_target, d.lax32_status,
    )

    d.dx16_target &= 0xFF
    d.dx16_value, d.dx16_status = handle_dx16(
        d.dx16_value, d.dx16_target, d.dx16_status,
    )

    d.dx32_target &= 0xFFFF
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
    d.fax64_nerrid = d.fax64.estatus >> 15 if d.fax64_estatus[[31]] else 0

    for i in range(16):
        d.fax32_params[i] = max(0, d.fax32_params[i])
    d.fax32_value, d.fax32_target, d.fax32_status = advance32(
        d.fax32_value, d.fax32_target, d.fax32_status,
        usermin=d.fax32_params[0], usermax=d.fax32_params[1],
        warnmin=d.fax32_params[2], warnmax=d.fax32_params[3],
        speed=d.fax32_params[12],
    )

    d.vx32_valuetargets[30], d.vx32_valuetargets[31], d.vx32_status = advance32(
        d.vx32_valuetargets[30], d.vx32_valuetargets[31], d.vx32_status,
    )
    if d.vx32_status[[14]]:  # while start/busy/stop
        for i in range(30):
            d.vx32_valuetargets[i] = d.vx32_valuetargets[30]
    # handle pctl.
    d.vx32_pctl, d.vx32_pvalue = handle_pctl(d.vx32_pctl, d.vx32_pvalue, d.fax32_params)

    d.vx64_valuetargets[30], d.vx64_valuetargets[31], d.vx64_estatus = advance64(
        d.vx64_valuetargets[30], d.vx64_valuetargets[31], d.vx64_estatus,
    )
    if d.vx64_estatus[[30]]:  # while start/busy/stop
        for i in range(30):
            d.vx64_valuetargets[i] = d.vx64_valuetargets[30]
    d.vx64_nerrid = d.vx64.estatus >> 15 if d.vx64_estatus[[31]] else 0
    # handle pctl.
    d.vx64_pctl, d.vx64_pvalue = handle_pctl(d.vx64_pctl, d.vx64_pvalue, d.fax64_params)

    d.sao64_value = handle_sxo(d.sao64_value, d.sao64_target, 0.12)
    d.sao32_value = handle_sxo(d.sao32_value, d.sao32_target, 0.12)

    d.sdo64_value = handle_sxo(d.sdo64_value, d.sdo64_target, 1)
    d.sdo32_value = handle_sxo(d.sdo32_value, d.sdo32_target, 1)
    d.sdo16_value = handle_sxo(d.sdo16_value, d.sdo16_target, 1)

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
            ts = int(min(MSGIO_NDATA, v.msglen))
            memcpy(adr(d.msg_data[0]), adr(v.msg[0]), ts)
            v.msglen = v.msglen - ts
            if v.msglen:
                memcpy(adr(v.msg[0]), adr(v.msg[MSGIO_NDATA]), v.msglen)
            d.msg_mbox = (5 << 13 if v.msglen else 1 << 13) + ts
        else:
            d.msg_mbox = 7 << 13


@program()
def Init(_v):
    for i in count(1):
        try:
            g.Devices[i].Name = typecode_description(g.Devices[i].TypCode)
        except RuntimeError:  # noqa: PERF203
            break


@program(
    is_initialized = Var(boolean, default=False),
)
def Main(v):
    if not v.is_initialized:
        Init()
        v.is_initialized = True
    Indexer()
    Implementation()
