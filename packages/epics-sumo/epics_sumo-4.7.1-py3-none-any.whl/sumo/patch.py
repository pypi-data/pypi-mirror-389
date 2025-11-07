"""patch file support."""

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

import os
import subprocess
import sumo.system
import sumo.fileurl

__version__="4.7.1" #VERSION#

assert __version__==sumo.system.__version__
assert __version__==sumo.fileurl.__version__

# pylint: disable= consider-using-f-string

def assert_patch():
    """ensure that patch exists."""
    sumo.system.test_program("patch")

def call_patch(patch_file, target_dir, verbose, dry_run):
    """call the patch utility.

    This function does:
      cd target_dir && patch -p1 < patch_file
    """
    assert_patch()
    cmd= "patch -p1"
    if dry_run or verbose:
        print("> cd %s && %s < %s" % (target_dir, cmd, patch_file))
    if dry_run:
        return
    old_dir= sumo.system.changedir(target_dir,
                                      verbose= False, dry_run= False)
    try:
        # pylint: disable=consider-using-with
        inp= open(patch_file, "r", encoding= "utf-8")
        p= subprocess.Popen(cmd, shell=True,
                            stdin= inp,
                            close_fds=True)
        p.wait()
    finally:
        sumo.system.changedir(old_dir, verbose= False, dry_run= False)
        inp.close()
    if p.returncode != 0:
        raise IOError("patch %s could not be fully applied" % patch_file)

def apply_patches(destdir, patchlist, verbose, dry_run):
    """apply a list of patches to a directory."""
    ap_destdir= os.path.abspath(destdir)
    for p in patchlist:
        filename= os.path.basename(p)
        dest_path= os.path.join(ap_destdir, filename)
        sumo.fileurl.get(p, dest_path, verbose, dry_run)
        call_patch(dest_path, destdir, verbose, dry_run)
