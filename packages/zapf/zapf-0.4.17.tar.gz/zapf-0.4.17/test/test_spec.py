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

"""Basic test suite for the utils."""

import pytest

from zapf import SpecError
from zapf.spec import decode_bitfield, v_2015_02, v_2021_09


def test_convert_unitcode():
    # 2015_02 version
    assert v_2015_02.convert_unit(0, -2) == '%'  # 0xfe00
    assert v_2015_02.convert_unit(12, 0) == 'deg'
    assert v_2015_02.convert_unit(16, -3) == 'l/s'
    assert v_2015_02.convert_unit(16, -6) == '10^-6 m^3/s'  # ml/s
    assert v_2015_02.convert_unit(4, -3) == 'mm'
    # 2021_09 version
    assert v_2021_09.decode_unit(0xF000) == '%'
    assert v_2021_09.decode_unit(0x0004) == 'deg'
    assert v_2021_09.decode_unit(0xE888) == 'l/s'
    assert v_2021_09.decode_unit(0xD088) == 'ml/s'
    assert v_2021_09.decode_unit(0xE94F) == 'mT/min'
    assert v_2021_09.decode_unit(0x118C) == 'hH/h'
    assert v_2021_09.decode_unit(0x1801) == '10^3 #'
    assert v_2021_09.decode_unit(0x1806) == 'km'
    assert v_2021_09.decode_unit(0x180e) == 'kOhm'
    assert v_2021_09.decode_unit(0x000e) == 'Ohm'

    assert v_2021_09.decode_unit(0xe808) == 'l'
    assert v_2021_09.decode_unit(0xe948) == 'l/min'
    assert v_2021_09.decode_unit(0xe802) == 'mbar'
    assert v_2021_09.decode_unit(0xe806) == 'mm'
    assert v_2021_09.decode_unit(0xf040) == '%/(#)'
    assert v_2021_09.decode_unit(0x0081) == '#/s'
    assert v_2021_09.decode_unit(0x0141) == '#/min'
    assert v_2021_09.decode_unit(0x0041) == ''  # main per main '#/(#)'

    assert v_2021_09.encode_unit('%') == 0xF000
    assert v_2021_09.encode_unit('deg') == 0x0004
    assert v_2021_09.encode_unit('l/s') == 0xE888
    assert v_2021_09.encode_unit('ml/s') == 0xD088
    assert v_2021_09.encode_unit('mT/min') == 0xE94F
    assert v_2021_09.encode_unit('hH/h') == 0x118C
    assert v_2021_09.encode_unit('10^3 #') == 0x1801
    assert v_2021_09.encode_unit('km') == 0x1806
    assert v_2021_09.encode_unit('Ohm') == 14


def test_decode_bitfield():
    assert decode_bitfield(1) == 1
    with pytest.raises(SpecError):
        decode_bitfield(12, 'a string')
    assert decode_bitfield(12, [(0, 9, '', {})]) == '12'
    assert decode_bitfield(12, [(2, 7, 'N', {})]) == 'N=3'
    assert decode_bitfield(12, [(3, 'A'), (2, 'B'), (0, 'C')]) == 'A, B'
    assert decode_bitfield(12, [(0, 3, 'A', {4: 'X'}), (3, 'B')]) == 'A=X, B'
    assert decode_bitfield(12, [(0, 3, 'A', {4: 'X'}),
                                (3, 1, '', {1: 'B'})]) == 'A=X, B'
