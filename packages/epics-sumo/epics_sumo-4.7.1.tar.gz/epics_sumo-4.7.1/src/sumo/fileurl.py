"""file-url support"""

# Copyright 2025 Helmholtz-Zentrum Berlin für Materialien und Energie GmbH
# <https://www.helmholtz-berlin.de>
#
# Author: Goetz Pfeiffer <goetzpf@googlemail.com>
#
# This program is free software: you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation, either version 3 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program.  If not, see <http://www.gnu.org/licenses/>.

# pylint: disable=invalid-name

import re
import urllib.request # not needed: urllib.parse, urllib.error
import sumo.system

__version__="4.7.1" #VERSION#

assert __version__==sumo.system.__version__

# pylint: disable= consider-using-f-string

rx_url= re.compile(r'([A-Za-z][A-Za-z0-9\.+-]*):')

urllib_schemes= set(("http","ftp","file"))

def assert_scp():
    """test if scp exists."""
    try:
        sumo.system.test_program("scp")
    except IOError as e:
        if "usage" in str(e):
            # scp was found, but it returned an error
            sumo.system.program_tests.add("scp")

def get(url, dest, verbose, dry_run):
    """Get by url."""
    m= rx_url.match(url)
    if m is None:
        # try to copy:
        if verbose:
            print("shutil.copyfile(%s, %s)\n" % (repr(url), repr(dest)))
        sumo.system.shutil_copyfile(url, dest, verbose, dry_run)
        return
    scheme_name= m.group(1)
    if scheme_name=="ssh":
        if not url.startswith("ssh://"):
            raise ValueError("error, ssh url '%s' not supported" % url)
        st= url.replace("ssh://","",1)
        assert_scp()
        cmd= "scp \"%s\" \"%s\"" % (st, dest)
        sumo.system.system(cmd, False, False, None, verbose, dry_run)
        return
    if scheme_name in urllib_schemes:
        if verbose or dry_run:
            print("urllib.urlretrieve(%s, %s)\n" % (repr(url), repr(dest)))
        if not dry_run:
            urllib.request.urlretrieve(url, dest)
        return
    raise ValueError("error, url '%s' not supported" % url)
