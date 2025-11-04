#!/usr/bin/env python3
# pylint: disable=invalid-name
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

"""Run the integrated simulator standalone, without creating a Zapf proto."""

import argparse
import itertools
import sys
import threading
import time
from pathlib import Path

from zapf.simulator.runtime import Memory
from zapf.simulator.server import AdsServer, ModbusServer


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-a', action='store_true', help='Use ADS server')
    parser.add_argument('file', help='File with the PLC simulation', type=Path)
    args = parser.parse_args()

    # needs to be created before reading the PLC code!
    mem = Memory()

    code = args.file.read_text()
    globs = {}
    # pylint: disable=exec-used
    exec(code, globs)  # noqa: S102

    mainfunc = globs['Main']
    if not getattr(mainfunc, 'is_program', False):
        raise RuntimeError('main function must be a program')

    cond = threading.Condition()
    srv = AdsServer(mem, cond, 49000) if args.a else ModbusServer(mem, cond, 5002)
    threading.Thread(target=srv.serve_forever).start()

    print('Starting main PLC loop.')
    try:
        for i in itertools.count():
            if i % 100 == 0:
                print(f'\r{i:>10} cycles', end='')
                sys.stdout.flush()
            with cond:
                mainfunc()
                cond.notify()
            time.sleep(.005)
    except KeyboardInterrupt:
        srv.shutdown()
        sys.exit(0)


if __name__ == '__main__':
    main()
