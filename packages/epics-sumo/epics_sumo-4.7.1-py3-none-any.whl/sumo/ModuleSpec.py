"""module specifications.
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

import sys
import re

if __name__ == "__main__":
    # if this module is directly called like a script, we have to add the path
    # ".." to the python search path in order to find modules named
    # "sumo.[module]".
    sys.path.append("..")

# pylint: disable=wrong-import-position

import sumo.utils
import sumo.JSON

__version__="4.7.1" #VERSION#

assert __version__==sumo.utils.__version__
assert __version__==sumo.JSON.__version__

# pylint: disable= consider-using-f-string

# -----------------------------------------------
# modulespecification
# -----------------------------------------------

_VERSIONFLAGS= set(("eq","le","ge","rx",""))

class Spec():
    """a class representing a single module specification."""
    def __init__(self, modulename, versionname, versionflag):
        """initialize the object.

        Here are some examples:

        >>> Spec("ALARM","R3-2","eq")
        Spec('ALARM','R3-2','eq')
        >>> Spec("ALARM","R3-2","eq")
        Spec('ALARM','R3-2','eq')
        """
        if versionflag not in _VERSIONFLAGS:
            raise TypeError(f"internal error, wrong versionflag "
                            f"{versionflag!r}")
        self.modulename= modulename
        self.versionname= versionname
        self.versionflag= versionflag
        # Note: self.rx may be set in self.test():
        self.rx= None
    def __repr__(self):
        """return repr string."""
        return "%s(%s,%s,%s)" % (self.__class__.__name__,\
                                 repr(self.modulename),\
                                 repr(self.versionname),\
                                 repr(self.versionflag))
    def no_version_spec(self):
        """returns True if there is no version spec."""
        return not self.versionname
    def is_exact_spec(self):
        """return if the spec is an exact version specification."""
        if not self.versionname:
            return False
        return self.versionflag=="eq"
    def assert_exact(self):
        """raise ValueError exception if spec is not *exact*.

        An exact module specification is a specification where for a module
        there is exactly one version given.
        """
        if not self.is_exact_spec():
            raise ValueError("error at specification '%s', module "
                             "specification must be exact" % \
                             self.to_string())
    @classmethod
    def from_name_version(cls, modulename, moduleversion):
        """create modulespec from modulename and moduleversion.
        """
        return cls(modulename, moduleversion, "eq")
    @classmethod
    def from_string(cls, spec):
        """create modulespec from a string.

        A module specification has one of these forms:
          modulename
          modulename:version

        version may be:
          versionname        : exactly this version
          +versionname       : this version or newer
          -versionname       : this version or older
          /versionname/      : regular expression

        Here are some examples:

        >>> Spec.from_string("ALARM")
        Spec('ALARM','','')
        >>> Spec.from_string("ALARM:R3-2")
        Spec('ALARM','R3-2','eq')
        >>> Spec.from_string("ALARM:+R3-2")
        Spec('ALARM','R3-2','ge')
        >>> Spec.from_string("ALARM:-R3-2")
        Spec('ALARM','R3-2','le')
        >>> Spec.from_string("ALARM:/(|R)[0-9-]+/")
        Spec('ALARM','(|R)[0-9-]+','rx')
        """
        # pylint: disable= too-many-branches
        modulename= None
        versionname= ""
        versionflag= ""
        lst= spec.split(":", maxsplit= 1)
        if len(lst)<=1:
            modulename= lst[0]
        else:
            (modulename, rest)= lst
            if rest!="":
                if rest[0]=="-":
                    versionname= rest[1:]
                    versionflag= "le"
                elif rest[0]=="+":
                    versionname= rest[1:]
                    versionflag= "ge"
                elif (rest[0]=="/") and (rest[-1]=="/"):
                    versionname= rest[1:-1]
                    versionflag= "rx"
                else:
                    versionname= rest
                    versionflag= "eq"
        #print(repr(modulename),repr(versionname),repr(versionflag))
        return cls(modulename,
                   versionname,
                   versionflag)
    def to_string(self):
        """return a spec string.

        Here are some examples:

        >>> Spec("ALARM","R3-2","eq").to_string()
        'ALARM:R3-2'
        >>> Spec("ALARM","R3-2","ge").to_string()
        'ALARM:+R3-2'
        >>> Spec("ALARM","R3-2","le").to_string()
        'ALARM:-R3-2'
        >>> Spec("ALARM","","").to_string()
        'ALARM'
        >>> Spec("ALARM","(|R)[0-9-]+","rx").to_string()
        'ALARM:/(|R)[0-9-]+/'
        """
        elms= [self.modulename]
        if self.versionname:
            elms.append(":")
            if self.versionflag=="eq":
                elms.append(self.versionname)
            elif self.versionflag=="le":
                elms.append(f"-{self.versionname}")
            elif self.versionflag=="ge":
                elms.append(f"+{self.versionname}")
            elif self.versionflag=="rx":
                elms.append(f"/{self.versionname}/")
            else:
                raise AssertionError("internal error")
        return "".join(elms)
    @staticmethod
    def compare_versions(version1, version2, flag):
        """Test if a version matches another version."""
        if not version1:
            return True
        if not version2:
            return True
        if flag=="rx":
            # presume version1 to be a regular expession
            if not isinstance(version1, re.Pattern):
                raise TypeError(f"internal error, wrong type: {version1!r}")
            return version1.match(version2) is not None
        if flag=="eq":
            return version1==version2
        k1= sumo.utils.rev2key(version1)
        k2= sumo.utils.rev2key(version2)
        if flag=="le":
            return k1>=k2
        if flag=="ge":
            return k1<=k2
        raise ValueError("unknown flag: '%s'" % repr(flag))

    def equal(self, version):
        """Test if a version is equal to a spec.

        Note: this returns always False when self.versionflag!="eq".
        """
        if self.versionflag!="eq":
            return False
        return self.versionname == version

    def test(self, version):
        """Test if a version matches the spec.

        Here are some examples:
        >>> m= Spec.from_string("ALARM:R3-2")
        >>> m.test("R3-1")
        False
        >>> m.test("R3-2")
        True
        >>> m.test("R3-3")
        False

        >>> m= Spec.from_string("ALARM:-R3-2")
        >>> m.test("R3-1")
        True
        >>> m.test("R3-2")
        True
        >>> m.test("R3-3")
        False

        >>> m= Spec.from_string("ALARM:+R3-2")
        >>> m.test("R3-1")
        False
        >>> m.test("R3-2")
        True
        >>> m.test("R3-3")
        True
        """
        if self.versionflag=="rx":
            # lazy initialization of regexp object:
            if self.rx is None:
                # note may raise re.error:
                self.rx= re.compile(self.versionname)
            ver= self.rx
        else:
            ver= self.versionname
        return Spec.compare_versions(ver, version,
                                     self.versionflag)

class Specs():
    """A class representing a list of Spec objects."""
    # pylint: disable=R0903
    #         Too few public methods
    def __init__(self, speclist= None):
        """note: this DOES NOT a deep copy of the list.

        Here is an example:

        >>> def p(s):
        ...     for m in s:
        ...         print(m)

        >>> a=Spec('A','R2','eq')
        >>> b=Spec('B','R2','eq')
        >>> p(Specs((a,b)))
        Spec('A','R2','eq')
        Spec('B','R2','eq')
        """
        if speclist is None:
            self.specs= []
        else:
            self.specs= speclist
    def __repr__(self):
        """return repr string."""
        return "%s(%s)" % (self.__class__.__name__,
                           ",".join([repr(s) for s in self.specs]))
    def sorted(self):
        """return a sorted "specs" object."""
        new= sorted(self.specs, key= lambda s: s.modulename)
        return self.__class__(new)
    def __iter__(self):
        """the default iterator."""
        yield from self.specs
    def add(self, spec):
        """add a new module spec."""
        self.specs.append(spec)
    @classmethod
    def from_dict(cls, dict_):
        """create from a dict mapping modulename->[versions]
        """
        new= cls()
        for name, versions in dict_.items():
            for version in versions:
                new.add(Spec.from_name_version(name, version))
        return new
    @staticmethod
    def scan_special(st):
        """scan special in-line commands."""
        if not st:
            # empty string or None
            return None
        if st[0]!=":":
            return None
        return st[1:].split(":")
    @staticmethod
    def _from_strings(module_dict, idx, specs, builddb_fn):
        """internal function to scan specs.

        Note:
        module_dict maps a modulename to a pair (order-key,Spec-object).

        builddb_fn: a function that for builddb_fn(buildtag) returns
                builddb.module_specs(buildtag), only needed for
                :build:buildtag.

        The order-key is used to give the list of modules the same sort order
        as they were found in the module specifications.
        """
        # pylint: disable=R0912
        #                          Too many branches
        for s in specs:
            special= Specs.scan_special(s)
            if special:
                # was special command
                if special[0]=="clear":
                    # clear module list so far
                    module_dict.clear()
                    continue
                if special[0]=="rm":
                    # remove single module
                    if len(special)<=1:
                        raise ValueError("argument to :rm: missing")
                    if special[1] in module_dict:
                        module_dict[special[1]][1]= None
                    continue
                if special[0]=="load":
                    if len(special)<=1:
                        raise ValueError("argument to :load: missing")
                    json_data= sumo.JSON.loadfile(special[1])
                    # pylint: disable=E1103
                    #         Instance of 'bool' has no 'get' member
                    json_specs= json_data.get("module")
                    if json_specs:
                        idx= Specs._from_strings(module_dict, idx,
                                                 json_specs,
                                                 builddb_fn)
                    continue
                if special[0]=="build":
                    if len(special)<=1:
                        raise ValueError("argument to :build: missing")
                    build_specs= builddb_fn(special[1])

                    idx= Specs._from_strings(module_dict, idx,
                                             build_specs,
                                             builddb_fn)
                    continue

                raise ValueError("unexpected spec: %s" % s)
            m= Spec.from_string(s)
            modulename= m.modulename
            if modulename in module_dict:
                module_dict[modulename][1]= m
                continue
            module_dict[modulename]= [idx, m]
            idx+= 1
        return idx

    @classmethod
    def from_strings(cls, specs, builddb_fn):
        """scan a list of module specification strings.

        specs:
            list of module specification strings
        builddb_fn:
            a function that for builddb_fn(buildtag) returns
            builddb.module_specs(buildtag), only needed for :build:buildtag.

        returns a new Specs object.

        Note that if a modulename is used twice, the later definition
        overwrites the first one. However, the module retains it's position in
        the internal list of modules.

        Here are some examples:

        >>> def p(s):
        ...     for m in s:
        ...         print(m)

        >>> p(Specs.from_strings(["A:R2","B:-R3","C:+R1"], None))
        Spec('A','R2','eq')
        Spec('B','R3','le')
        Spec('C','R1','ge')
        >>> p(Specs.from_strings(["A:R2","B:-R3","A:R3"], None))
        Spec('A','R3','eq')
        Spec('B','R3','le')
        >>> p(Specs.from_strings(["A:R2","B:-R3",":rm:A"], None))
        Spec('B','R3','le')
        >>> p(Specs.from_strings(["A:R2","B:-R3",":rm:A","A:R3"], None))
        Spec('A','R3','eq')
        Spec('B','R3','le')
        """
        module_dict= {}
        Specs._from_strings(module_dict, 0, specs, builddb_fn)

        l= [modulespec for (_,modulespec) in sorted(module_dict.values()) \
                       if modulespec]
        return cls(l)
    def assert_exact(self):
        """raise ValueError exception if not all spec are *exact*.

        An exact module specification is a specification where for each module
        there is one version given.
        """
        for spec in self:
            if spec.is_exact_spec():
                continue
            raise ValueError("error at specification '%s', all module "
                             "specifications must be exact" % \
                             spec.to_string())
    def assert_unique(self):
        """raise ValueError exception if a module is found more than once.

        This ensures that the module specifications have only one specification
        for each modulename.
        """
        modules= set()
        for spec in self:
            if spec.modulename not in modules:
                modules.add(spec.modulename)
                continue
            raise ValueError("error, module '%s' is mentioned twice in "
                             "module specifications" % spec.modulename)
    def to_stringlist(self):
        """convert back to a list of strings."""
        l= []
        for spec in self:
            l.append(spec.to_string())
        return sorted(l)
    def to_dist_dict(self):
        """convert to a dict mapping modulename-->versionname.

        May raise ValueError exception if the specs are not all exact and
        unique.
        """
        self.assert_exact()
        self.assert_unique()
        d= {}
        for spec in self:
            d[spec.modulename]= spec.versionname
        return d
    def module_set(self):
        """return a set containing all module names."""
        s= set()
        for spec in self:
            s.add(spec.modulename)
        return s

def _test():
    """perform internal tests."""
    import doctest # pylint: disable= import-outside-toplevel
    doctest.testmod()

if __name__ == "__main__":
    _test()
