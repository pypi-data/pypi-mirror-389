"""Repository support
"""

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

import os.path
import sys

import sumo.utils
import sumo.lock
import sumo.JSON
import sumo.patch
import sumo.path
import sumo.tar
import sumo.darcs
import sumo.mercurial  # "hg"
import sumo.git
import sumo.subversion # "svn"
import sumo.cvs

__version__="4.7.1" #VERSION#

assert __version__==sumo.utils.__version__
assert __version__==sumo.lock.__version__
assert __version__==sumo.JSON.__version__
assert __version__==sumo.patch.__version__
assert __version__==sumo.path.__version__
assert __version__==sumo.tar.__version__
assert __version__==sumo.darcs.__version__
assert __version__==sumo.mercurial.__version__
assert __version__==sumo.git.__version__
assert __version__==sumo.subversion.__version__
assert __version__==sumo.cvs.__version__

# pylint: disable= consider-using-f-string

known_repos=set(("darcs","hg","git","svn","cvs"))
known_no_repos= set(("path","tar"))
known_sources= set(known_no_repos).union(known_repos)

known_sourcespec_keys=set(("type", "url", "tag", "rev", "patches", "commands"))

known_repo_modes= set(("local", "get","pull","push"))

# ---------------------------------------------------------
# scan a directory:

def repo_from_dir(directory, hints, verbose, dry_run):
    """scan a directory and return a repository object.

    Hints must be a dictionary. This gives hints how the directory should be
    scanned. Currently we know these keys in the dictionary:

    "ignore changes": sumo.utils.RegexpMatcher
        All local changes in files that match the RegexpMatcher object are
        ignored. By this we can get the remote repository and tag from a
        directory although there are uncomitted changes. A common application
        is to ignore changes in file "configure/RELEASE".
    "dir patcher": sumo.utils.RegexpPatcher
        This patcher is applied to the directory that is stored in the object.
    "url patcher": sumo.utils.RegexpPatcher
        This patcher is applied to the URL that is stored in the object.
    "force local": bool
        If this is True, the returned repository object does not contain a
        remote repository url even if there was one.
    "write check": bool
        If this is True, when the repository data directory is not writable
        the function returns <None>.

    May raise:
        TypeError : when hints parameter is not a dict
    """
    if not isinstance(hints, dict):
        raise TypeError("hints parameter '%s' is of wrong type" % \
                        repr(hints))
    obj= sumo.darcs.Repo.scan_dir(directory, hints, verbose, dry_run)
    if obj is not None:
        return obj
    obj= sumo.mercurial.Repo.scan_dir(directory, hints, verbose, dry_run)
    if obj is not None:
        return obj
    obj= sumo.git.Repo.scan_dir(directory, hints, verbose, dry_run)
    if obj is not None:
        return obj
    obj= sumo.subversion.Repo.scan_dir(directory, hints, verbose, dry_run)
    if obj is not None:
        return obj
    obj= sumo.cvs.Repo.scan_dir(directory, hints, verbose, dry_run)
    if obj is not None:
        return obj
    return None

def src_from_dir(directory, hints, verbose, dry_run):
    """scan a directory and return a repository object.

    Hints must be a dictionary. This gives hints how the directory should be
    scanned. Currently we know these keys in the dictionary:

    "ignore changes": sumo.utils.RegexpMatcher
        All local changes in files that match the RegexpMatcher object are
        ignored. By this we can get the remote repository and tag from a
        directory although there are uncomitted changes. A common application
        is to ignore changes in file "configure/RELEASE".
    "dir patcher": sumo.utils.RegexpPatcher
        This patcher is applied to the directory that is stored in the object.
    "url patcher": sumo.utils.RegexpPatcher
        This patcher is applied to the URL that is stored in the object.
    "force path" : bool
        If this is True, a Path object is always returned, even if a repository
        was found.
    """
    if not isinstance(hints, dict):
        raise TypeError("hints parameter '%s' is of wrong type" % \
                        repr(hints))
    if hints.get("force path"):
        return sumo.path.Repo.scan_dir(directory, hints, verbose, dry_run)

    obj= sumo.tar.Repo.scan_dir(directory, hints, verbose, dry_run)
    if obj is not None:
        return obj
    # insert other repo supports here
    return sumo.path.Repo.scan_dir(directory, hints, verbose, dry_run)

# ---------------------------------------------------------
# check out:

def apply_commands(cmds, target_dir, verbose, dry_run):
    """apply custom commands in module."""
    old_dir= sumo.system.changedir(target_dir, verbose, dry_run)
    try:
        for cmd in cmds:
            sumo.system.system(cmd, False, False, None, verbose, dry_run)
    finally:
        sumo.system.changedir(old_dir, verbose, dry_run)

def checkout(sourcespec, destdir, lock_timeout, verbose, dry_run):
    """check out a working copy.

    sourcespec must be a SourceSpec object.

    May raise:
        ValueError: from sumo.*.Repo.checkout
    """
    # pylint: disable=R0913
    #                          Too many arguments
    if not isinstance(sourcespec, SourceSpec):
        raise TypeError("error, '%s' is not of type SourceSpec" % \
                        repr(sourcespec))
    repotype= sourcespec.sourcetype()
    spec= sourcespec.spec_val()
    if repotype == "darcs":
        sumo.darcs.Repo.checkout(spec, destdir, lock_timeout,
                                    verbose, dry_run)
    elif repotype == "hg":
        sumo.mercurial.Repo.checkout(spec, destdir, lock_timeout,
                                        verbose, dry_run)
    elif repotype == "git":
        sumo.git.Repo.checkout(spec, destdir, lock_timeout,
                                  verbose, dry_run)
    elif repotype == "svn":
        sumo.subversion.Repo.checkout(spec, destdir, lock_timeout,
                                         verbose, dry_run)
    elif repotype == "cvs":
        sumo.cvs.Repo.checkout(spec, destdir, lock_timeout,
                                  verbose, dry_run)
    elif repotype== "tar":
        sumo.tar.Repo.checkout(spec, destdir, lock_timeout,
                                  verbose, dry_run)
    elif repotype== "path":
        sumo.path.Repo.checkout(spec, destdir, lock_timeout,
                                   verbose, dry_run)
    else:
        raise ValueError("unsupported repotype: %s" % repotype)
    cmds= sourcespec.commands()
    if cmds is not None:
        apply_commands(cmds, destdir, verbose, dry_run)
    p= sourcespec.patches()
    if p:
        sumo.patch.apply_patches(destdir, p, verbose, dry_run)


# ---------------------------------------------------------
# SourceSpec class:

class SourceSpec(sumo.JSON.Container):
    """hold the source specification.
    """
    # pylint: disable=R0904
    #                          Too many public methods
    def __init__(self, dict_):
        """create the object."""
        if bool(set(dict_.keys()).difference(known_sourcespec_keys)):
            # Note that __del__(self) is called even if the object was not
            # constructed properly like here. This matters here since
            # sumo.JSON.Container defines __del__(). We handle this problem
            # in function __del__ in sumo.JSON.
            raise ValueError("invalid source spec dict %s" % repr(dict_))
        super().__init__(dict_, use_lock= True)
    # pylint: disable=C0301
    #                          Line too long
    def to_deps_dict(self):
        """convert to dict as it is stored in dependency database.
        """
        d= self.datadict()
        type_= d.get("type")
        if type_ is None:
            raise ValueError(("incomplete SourceSpec %s cannot be "
                              "converted to dict\n") % repr(self))
        # pylint: disable=no-else-return
        if type_=="path":
            # for 'path' it's a simple string:
            url= d.get("url")
            if url is None:
                raise ValueError(("SourceSpec %s cannot be "
                                  "converted to dict, url is missing\n") % \
                                 repr(self))
            return { type_: url }
        else:
            d_cpy= {}
            for k, v in d.items():
                if k=="type":
                    continue
                # skip over values that are empty strings:
                if v=="":
                    continue
                d_cpy[k]= v
        return { type_ : d_cpy }
    @classmethod
    def from_deps_dict(cls, dict_):
        """create from a dict as it is stored in dependency database.
        """
        type_= sumo.utils.single_key(dict_)
        if type_=="path":
            # for 'path' it's a simple string:
            new= {"url": dict_[type_]}
        else:
            new= dict(dict_[type_])
        new["type"]= type_
        return cls(new)
    @classmethod
    def from_string_sourcespec(cls, string):
        """scan a source specification.

        A sourcespec has the following, new, format:

        DEFINTION [DEFINTION]

        where DEFINTION is:

        NAME=VALUE [,VALUE...]

        Note that VALUE may be a simple string not including
        the characters '=', ',' and '"' or a JSON string.

        NAME must be one of:
          type
          url
          rev
          tag
          patches
          commands

        An old format is also supportted, these two formats are also valid:

          TYPE
          TYPE URL

        May raise:
            TypeError, ValueError

        Here are some examples:
        >>> SourceSpec.from_string_sourcespec("type=path url=ab")
        SourceSpec({'type': 'path', 'url': 'ab'})
        >>> SourceSpec.from_string_sourcespec("type=path")
        SourceSpec({'type': 'path'})
        >>> SourceSpec.from_string_sourcespec("type=darcs url=ab")
        SourceSpec({'type': 'darcs', 'url': 'ab'})
        >>> SourceSpec.from_string_sourcespec("type=darcs url=ab tag=R1-1")
        SourceSpec({'tag': 'R1-1', 'type': 'darcs', 'url': 'ab'})
        >>> SourceSpec.from_string_sourcespec("type=darcs url=ab tag=R1-1 patches=f1")
        SourceSpec({'patches': ['f1'], 'tag': 'R1-1', 'type': 'darcs', 'url': 'ab'})
        >>> SourceSpec.from_string_sourcespec("type=darcs url=ab tag=R1-1 patches=f1,f2")
        SourceSpec({'patches': ['f1', 'f2'], 'tag': 'R1-1', 'type': 'darcs', 'url': 'ab'})
        >>> SourceSpec.from_string_sourcespec("typex=path")
        Traceback (most recent call last):
            ...
        ValueError: invalid names found in source spec 'typex=path'
        """
        def patches_to_list(dict_):
            """ensure that 'patches' in dict is a list."""
            p= dict_.get("patches")
            if p is None:
                return
            if isinstance(p, list):
                return
            dict_["patches"]= [p]
        def check_dict(allowed_keys, dict_):
            """check if all dict keys are from a given list."""
            return not bool(set(dict_.keys()).difference(set(allowed_keys)))
        if not isinstance(string, str):
            raise TypeError("wrong type of source spec %s" % repr(string))
        if (not string) or string.isspace():
            raise ValueError("invalid source spec %s" % repr(string))

        if not "=" in string:
            l= string.strip().split(None, 1)
            defs= { "type": l[0] }
            if len(l)==2:
                # url is optional
                # if there is no url, there is no remote repository
                defs["url"]= l[1]
            elif len(l)!=1:
                raise ValueError("invalid source spec %s" % repr(string))
        else:
            defs= sumo.utils.definition_list_to_dict(string)
            if not check_dict(known_sourcespec_keys, defs):
                raise ValueError("invalid names found in source spec %s" % \
                                 repr(string))
            patches_to_list(defs)
        return cls(defs)
    # pylint: enable=C0301
    #                          Line too long
    def sourcetype(self):
        """return the type of the source."""
        d= self.datadict()
        return d["type"]
    def is_repo(self):
        """return if SourceSpec refers to a repository.
        """
        return self.sourcetype() in known_repos
    def path(self, new_val= None):
        """return the path if the type is "path"."""
        pars= self.datadict()
        type_= pars["type"]
        if type_!= "path":
            raise TypeError("error, 'path()' can only be called for "
                            "SourceSpec objects of type 'path'")
        if new_val is None:
            return pars["url"]
        pars["url"]= new_val
        return None
    def tag(self, new_val= None):
        """return the tag if it exists."""
        pars= self.datadict()
        if new_val is None:
            return pars.get("tag")
        pars["tag"]= new_val
        return None
    def url(self, new_val= None):
        """return the url if it exists."""
        pars= self.datadict()
        if new_val is None:
            return pars.get("url")
        pars["url"]= new_val
        return None
    def commands(self, new_val= None):
        """return the patches if they exist."""
        pars= self.datadict()
        if new_val is None:
            return pars.get("commands")
        pars["commands"]= new_val
        return None
    def patches(self, new_val= None):
        """return the patches if they exist."""
        pars= self.datadict()
        if new_val is None:
            return pars.get("patches")
        pars["patches"]= new_val
        return None
    def spec_val(self):
        """return the *value* of the source specification.
        """
        pars= self.datadict()
        return pars
    def copy_spec(self, other):
        """simply overwrite self with other.

        If a value in other is "", the key is deleted.
        """
        pars= self.datadict()
        o_pars= other.datadict()
        keys= set(pars.keys())
        o_keys= set(o_pars.keys())
        for k in keys.difference(o_keys):
            del pars[k]
        for k in o_keys:
            v= o_pars[k]
            if v!="":
                pars[k]= v
                continue
            if k in keys:
                del pars[k]
    def change_source(self, other):
        """set source spec by copying information from another object.

        returns True if the spec was changed, False if it wasn't.

        If a value in other is "", the key is deleted.

        May raise:
            ValueError
        """
        pars= self.datadict()
        type_= pars.get("type")
        o_pars= other.datadict()
        o_type_= o_pars.get("type")

        if o_type_ is None:
            if type_ is None:
                raise ValueError("no source type defined in %s" % \
                                 repr(other))
            # assume same type:
            o_type_= type_
        if type_!=o_type_:
            # different type, replace everything:
            self.copy_spec(other)
            return True
        changed= False
        for (k,v) in o_pars.items():
            orig= pars.get(k)
            if v=="":
                if orig is None:
                    continue
                del pars[k]
                changed= True
                continue
            if orig!=v:
                changed= True
                pars[k]= v
        # return whether there were changes:
        return changed
    def change_source_by_tag(self, tag):
        """change the source spec just by providing a tag.

        Note: If the source specification has "rev" set instead of "tag" this
              property will be removed before the change is applied.

        returns True if the spec was changed, False if it wasn't.
        """
        pars= self.datadict()
        type_= pars["type"]
        if type_ in known_no_repos:
            raise ValueError("you cannot provide just a new tag for "
                             "a source specification of "
                             "type '%s'" % type_)
        changes= False
        # delete "rev" key if present:
        if "rev" in pars:
            del pars["rev"]
            changes= True
        old= pars.get("tag")
        if old!=tag:
            pars["tag"]= tag
            changes= True
        return changes

# ---------------------------------------------------------
# ManagedRepo class

class ManagedRepo():
    # pylint: disable=too-many-instance-attributes
    """Object for managing data in a repository.

    Do pull before read,
    commit and push after write.
    """
    def __init__(self, sourcespec,
                 mode, directory,
                 lock_timeout,
                 verbose, dry_run):
        """create the object.

        sourcespec must be a SourceSpec object or <None>.

        spec must be a dictionary with "url" and "tag" (optional).

        Note: distributed VCS: are darcs,mercurial,git
              centralized VCS: subversion, cvs

        mode must be "local", "get", "pull" or "push".
          local:
               initial: local repo must exist, dist. VCS only
               reading: do nothing, dist. VCS only
               writing: just commit, dist. VCS only
          get:
               initial: create the repo if it doesn't yet exist,
               reading: do not pull or update repo
               writing: dist.VCS: no pull, commit, no push
                        cent.VCS: no update, no commit
          pull:
               initial: create the repo if it doesn't yet exist,
               reading: pull or update repo
               writing: dist.VCS: pull, commit, no push
                        cent.VCS: update, no commit
          push:
               initial: create the repo if it doesn't yet exist,
               reading: pull or update repo
               writing: dist.VCS: pull, commit, push
                        cent.VCS: update, commit

        If sourcespec is None, create an empty object that basically
        does nothing.

        Does checkout the repository if the directory does not yet exist.

        May raise:
            TypeError                    : When parameter sourcespec has wrong
                                           type.
            AssertionError               : when parameter "mode" is wrong
                                           when checkout didn't create a directory
                                           when directory exists but is, in
                                                fact, a file
            OSError                      : when directory does not exist or
                                           cannot be written to
            ValueError                   : from checkout()
            sumo.lock.LockedError     : can't get lock
            sumo.lock.AccessError     : no rights to create lock
            sumo.lock.NoSuchFileError : file path doesn't exist
            OSError                      : other operating system errors while
                                           trying to lock
        """
        # pylint: disable=too-many-arguments too-many-positional-arguments
        # pylint: disable=too-many-statements
        # pylint: disable=too-many-branches
        self.sourcespec= sourcespec
        if sourcespec is None:
            return

        if not isinstance(sourcespec, SourceSpec):
            raise TypeError("error, '%s' is not of type SourceSpec" % \
                            repr(sourcespec))

        if mode not in known_repo_modes:
            raise AssertionError("unknown mode: %s" % repr(mode))
        self.lock_timeout= lock_timeout
        self.mode= mode
        self.directory= directory
        self.verbose= verbose
        self.dry_run= dry_run
        # lockfile will be named "repo.lock":
        lockname= os.path.join(self.directory, "repo")
        self.lock= sumo.lock.MyLock(lockname, self.lock_timeout)

        if not os.path.exists(self.directory):
            # must create
            # first get a lock for the directory to create:
            lk= sumo.lock.MyLock(self.directory, self.lock_timeout)
            # may raise sumo.lock.LockedError,
            #           sumo.lock.AccessError,
            #           sumo.lock.NoSuchFileError
            lk.lock()

            try:
                # The directory may have been created in the meantime by
                # another process. Do checkout only if it still doesn't exist:
                if not os.path.exists(self.directory):
                    # may raise ValueError:
                    checkout(self.sourcespec, self.directory,
                             self.lock_timeout,
                             self.verbose, self.dry_run)
                    if not os.path.exists(self.directory):
                        raise AssertionError("checkout of %s to %s failed" % \
                                             (self.sourcespec,
                                              self.directory))
            finally:
                lk.unlock()
        if not os.path.isdir(self.directory):
            raise AssertionError("error, '%s' is not a directory" % \
                                 self.directory)

        no_write_access= False
        errmsg= None
        # get a repository lock:
        try:
            self.lock.lock()
        except (sumo.lock.AccessError, sumo.lock.LockedError) as e:
            # we do not have write access on the repository:
            no_write_access= True
            errmsg= str(e)

        if no_write_access:
            # basically disable all action on the repository:
            # Setting self.sourcespec to <None> basically disables the
            # ManagedRepo object.
            if self.mode not in ('local', 'get'):
                sumo.utils.errmessage(\
                    ("warning: locking the dependency database failed: "
                     "%s. Disabling repository operations on the "
                     "dependency database for now.") % errmsg)
                sys.stderr.flush()
            self.sourcespec= None
            return

        self.repo_obj= None
        try:
            # will never raise TypeError when called like this:
            hints= {"write check": True}
            if self.mode == "local":
                hints["force local"]= True
            self.repo_obj= repo_from_dir(self.directory,
                                         hints,
                                         self.verbose, self.dry_run)
        finally:
            self.lock.unlock()

        if self.repo_obj is None:
            # basically disable all action on the repository:
            # Setting self.sourcespec to <None> basically disables the
            # ManagedRepo object.
            self.sourcespec= None
        elif self.repo_obj.distributed_repo():
            # ^^^ call "distributed_repo()" only if repo_obj is not None
            if self.repo_obj.get_remote_url() is None:
                # no remote repo defined
                # repo found but remote repo couldn't be contacted:
                if self.mode in ("pull", "push"): # "local" and "get" are okay
                    self.mode='get'
                    sumo.utils.errmessage(\
                        "warning: remote repository for dependency "
                        "database repository couldn't be contacted, "
                        "forcing mode 'get'.")

    def local_changes(self):
        """return if there are local changes."""
        if self.sourcespec is None:
            # for the "empty" ManagedRepo object just return <None>:
            return None
        return self.repo_obj.local_changes
    def commit(self, message):
        """commit changes."""
        self.lock.lock()
        try:
            self.repo_obj.commit(message)
        finally:
            self.lock.unlock()
    def prepare_read(self):
        """do checkout or pull."""
        if self.sourcespec is None:
            return
        # pylint: disable=E1103
        #                          Instance of 'Repo' has no 'pull' member
        if self.mode in ('pull', 'push'):
            self.lock.lock()
            try:
                if self.repo_obj.distributed_repo():
                    self.repo_obj.pull_merge()
                else:
                    self.repo_obj.update()
            finally:
                self.lock.unlock()
    def finish_write(self, message):
        """do commit and push."""
        if self.sourcespec is None:
            return
        if not self.repo_obj:
            raise AssertionError("internal error, repo obj missing")
        # pylint: disable=E1103
        #                          Instance of 'Repo' has no '...' member
        self.lock.lock()
        try:
            if self.repo_obj.distributed_repo():
                self.repo_obj.commit(message)
                if self.mode=='push':
                    self.repo_obj.push()
            else:
                if self.mode=='push':
                    self.repo_obj.commit(message)
        finally:
            self.lock.unlock()

def _test():
    """perform internal tests."""
    import doctest # pylint: disable= import-outside-toplevel
    doctest.testmod()

if __name__ == "__main__":
    _test()
