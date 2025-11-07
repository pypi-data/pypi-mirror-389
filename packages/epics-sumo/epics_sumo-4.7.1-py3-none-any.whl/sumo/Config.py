"""Configuration file support.
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

import os
import sys

if __name__ == "__main__":
    # if this module is directly called like a script, we have to add the path
    # ".." to the python search path in order to find modules named
    # "sumo.[module]".
    sys.path.append("..")

# pylint: disable=wrong-import-position
# pylint: disable= consider-using-f-string
import sumo.utils
import sumo.JSON

__version__="4.7.1" #VERSION#

assert __version__==sumo.JSON.__version__

# -----------------------------------------------
# config file support
# -----------------------------------------------

class ConfigFile():
    """store options in a JSON file."""
    # pylint: disable=too-many-instance-attributes
    def __init__(self, filename, env_name,
                 bool_options,
                 string_options, list_options,
                 env_expand_options):
        """create the object.

        If filename is not empty, search for config files at:
          /etc
          <path of this python file>
          $HOME
          <cwd>

        """
        # pylint: disable= too-many-arguments too-many-positional-arguments
        def newset(v):
            """simple set creator."""
            if not v:
                return set()
            return set(v)
        self._dict= {}
        self._filename= filename
        self._real_paths= []
        self._env_name= env_name
        self._bool_options= newset(bool_options)
        self._string_options= newset(string_options)
        self._list_options= newset(list_options)
        self._all_options= sumo.utils.set_union(self._bool_options,
                                                   self._string_options,
                                                   self._list_options)
        self._env_expand_options= newset(env_expand_options)
        if not filename:
            self._paths= []
        else:
            search_paths= sumo.utils.split_searchpath(\
                    os.environ.get(env_name))
            if not search_paths:
                # not specified by environment variable:
                search_paths=["/etc",
                              sumo.utils.sumolib_dir(),
                              os.environ.get("HOME"),
                              os.getcwd()]
            self._paths= []
            for path in search_paths:
                if not path:
                    continue
                p= os.path.join(path, filename)
                if os.path.isfile(p):
                    self._paths.append(p)
    def dump_str(self):
        """dump the object, return a list of lines"""
        lst= []
        lst.append("%s:" % self.__class__.__name__)
        lst.append("\tenv_name: %s" % repr(self._env_name))
        lst.append("\tbool_options: %s" % repr(self._bool_options))
        lst.append("\tstring_options: %s" % repr(self._string_options))
        lst.append("\tlist_options: %s" % repr(self._list_options))
        lst.append("\tall_options: %s" % repr(self._all_options))
        lst.append("\tenv_expand_options: %s" % repr(self._env_expand_options))
        lst.append("\tfilename: %s" % repr(self._filename))
        lst.append("\treal_paths: %s" % repr(self._real_paths))
        lst.append("\tpaths: %s" % repr(self._paths))
        lst.append("\tdict: %s" % repr(self._dict))
        return lst
    def dump(self):
        """dump the object."""
        print("\n".join(self.dump_str()))

    def get(self, optionname):
        """get an option."""
        return self._dict.get(optionname)
    def set(self, optionname, value):
        """set an option to an arbitrary value."""
        self._dict[optionname]= value
    def env_expand(self):
        r"""expand environment variables in known values.

        All $VARNAME and ${VARNAME} strings are expaned with the values of the
        environment variable VARNAME for the keys in [keys]. If you want to
        keep the dollar '$' sign uninterpreted, precede it with a backslash
        like in '\$VARNAME'.

        May raise:
            AssertionError if the value to expand is not a string
        """
        dict_= self._dict
        for key in self._env_expand_options:
            val= dict_.get(key)
            if val is None:
                continue
            if not isinstance(val, str):
                raise AssertionError("unexpected type: key: %s val: %s" % \
                                     (repr(key), repr(val)))
            dict_[key]= sumo.utils.env_expand(val)
    def merge(self, dict_, append_lists):
        """merge known keys from dict_ with self.

        May raise:
            KeyError if a dict key is unknown.
            TypeError if value of a key has the wrong type
        """
        for (key, val) in dict_.items():
            if key in self._bool_options:
                if not isinstance(val, bool):
                    raise TypeError("value %s of key %s is not a bool" % \
                                    (repr(val), repr(key)))
                self._dict[key]= val
                continue
            if key in self._string_options:
                if not isinstance(val, str):
                    raise TypeError("value %s of key %s is not a string" % \
                                    (repr(val), repr(key)))
                self._dict[key]= val
                continue
            if key in self._list_options:
                if not isinstance(val, list):
                    raise TypeError("value %s of key %s is not a list" % \
                                    (repr(val), repr(key)))
                if append_lists:
                    self._dict[key]= \
                            sumo.utils.list_update(self._dict.get(key,[]), val)
                else:
                    self._dict[key]= val
                continue
            raise KeyError("unknown key: %s" % repr(key))
    def _load_file(self, filename, must_exist, enable_loading):
        """load filename.

        Note that the special key "#include" means that another config file is
        included much as with the #include directive in C.

        May raise:
            IOError if the file couldn't be loaded
            KeyError if a dict key is unknown.
            TypeError if value of a key has the wrong type
            sumo.JSON.ParseError when a JSON file is invalid
        """
        def _load_lst(dict_, keys):
            """load lists from a dict."""
            l= []
            for k in keys:
                v= dict_.get(k)
                if v is None:
                    continue
                if not isinstance(v, list):
                    raise TypeError("value %s of key %s is not a list" % \
                                    (repr(v), repr(k)))
                if not v:
                    continue
                l.extend(v)
                del dict_[k]
            return l
        if not os.path.exists(filename):
            if not must_exist:
                return
            raise IOError("error: file \"%s\" doesn't exist" % filename)
        self._real_paths.append(filename)
        # may raise sumo.JSON.ParseError:
        data= sumo.JSON.loadfile(filename)
        # pylint: disable=E1103
        #                     Instance of 'bool' has no 'items' member
        if enable_loading:
            try:
                for f in _load_lst(data, ["#include", "#preload"]):
                    self._load_file(f, must_exist= True,
                                    enable_loading= enable_loading)
                for f in _load_lst(data, ["#opt-preload"]):
                    self._load_file(f, must_exist= False,
                                    enable_loading= enable_loading)
            except (KeyError, TypeError) as e:
                raise sumo.utils.annotate("file "+filename+": %s", e)
        try:
            self.merge(data, append_lists= True)
        except (KeyError, TypeError) as e:
            raise sumo.utils.annotate("file "+filename+": %s", e)
        if enable_loading:
            try:
                for f in _load_lst(data, ["#postload"]):
                    self._load_file(f, must_exist= True,
                                    enable_loading= enable_loading)
                for f in _load_lst(data, ["#opt-postload"]):
                    self._load_file(f, must_exist= False,
                                    enable_loading= enable_loading)
            except (KeyError, TypeError) as e:
                raise sumo.utils.annotate("file "+filename+": %s", e)
    def real_paths(self):
        """return the list of files that should be loaded or were loaded."""
        return self._real_paths
    def load(self, filenames, enable_loading):
        """load from all files in filenames list.

        enable_loading - If True, commands like "#preload" are enabled,
                         otherwise these keys are just treated like ordinary
                         values.

        May raise:
            IOError if the file couldn't be loaded
            KeyError if a dict key is unknown.
            TypeError if value of a key has the wrong type
        """
        def unify(l):
            """remove double elements in a list."""
            n= []
            for e in l:
                if e in n:
                    continue
                n.append(e)
            return n
        if filenames:
            for f in filenames:
                if os.path.isfile(f):
                    self._paths.append(f)
        for filename in self._paths:
            self._load_file(filename, must_exist= True,
                            enable_loading= enable_loading)
        # remove double filenames in #preload #postload etc:
        for k in ("#include",
                  "#preload", "#opt-preload",
                  "#postload", "#opt-postload"):
            l= self._dict.get(k)
            if l is None:
                continue
            self._dict[k]= unify(l)

    def save(self, filename, keys, verbose, dry_run):
        """dump in json format"""
        # do not include "None" values:
        dump= {}
        if not keys:
            keys= self._dict.keys()
        for k in keys:
            # we do not distinguish here between items that don't exist
            # and items that have value "None":
            v= self._dict.get(k)
            if v is None:
                continue
            dump[k]= v
        if filename=="-":
            sumo.JSON.dump(dump)
            return
        sumo.utils.backup_file(filename,
                               backup_no= 1,
                               verbose= verbose,
                               dry_run= dry_run)
        if verbose:
            print("creating %s" % filename)
        if not dry_run:
            sumo.JSON.dump_file(filename, dump)

    def merge_options(self, option_obj, merge_opts_set):
        """create from an option object.

        Merge Config object with command line options and
        command line options with Config object.

        All options that are part of the set <merge_opts_set> must be lists.
        For these options the lists are concatenated.

        May raise:
            KeyError if a dict key is unknown.
            TypeError if value of a key has the wrong type
        """
        # pylint: disable=R0912
        #                          Too many branches
        def option_obj_key(key):
            """convert ConfigFile key to Options key."""
            return key.replace("-", "_")
        # copy from option_obj to self:
        merge_dict= {}
        if merge_opts_set:
            for opt in merge_opts_set:
                o_opt= option_obj_key(opt)
                if not hasattr(option_obj, o_opt):
                    raise KeyError("%s is not a known option" % repr(opt))
                opt_val= getattr(option_obj, o_opt)
                if opt_val is not None:
                    merge_dict[opt]= opt_val
            # could possible raise KeyError, TypeError although the way it is
            # used here this shouldn't happen:
            self.merge(merge_dict, append_lists= True)
        overwrite_dict= {}
        for opt in self._all_options:
            if opt in merge_dict:
                continue
            o_opt= option_obj_key(opt)
            opt_val= getattr(option_obj, o_opt)
            if opt_val is not None:
                overwrite_dict[opt]= opt_val
        # could possible raise KeyError, TypeError although the way it is
        # used here this shouldn't happen:
        self.merge(overwrite_dict, append_lists= False)

        # copy from self to option_obj:
        for (opt, val) in self._dict.items():
            o_opt= option_obj_key(opt)
            if not hasattr(option_obj, o_opt):
                raise AssertionError(\
                        "ERROR: key '%s' not in the option object" % opt)
            if val:
                setattr(option_obj, o_opt, val)

def _test():
    """perform internal tests."""
    # pylint: disable= import-outside-toplevel
    import doctest
    doctest.testmod()

if __name__ == "__main__":
    _test()
