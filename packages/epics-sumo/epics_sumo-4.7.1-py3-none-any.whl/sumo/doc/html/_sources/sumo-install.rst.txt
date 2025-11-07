Installing Sumo
===============

Preface
-------

Sumo is available on `pypi <https://pypi.org/project/epics-sumo/>`_,
as a debian or rpm package and as a tar.gz or wheel file.

Requirements
------------

Sumo requires `Python <https://www.python.org>`_ version 3.9 or newer.

Sumo is tested on `debian <https://www.debian.org>`_ and 
`Fedora <https://getfedora.org>`_ Linux distributions but should run on all
Linux distributions. It probably also runs on other flavors of Unix, probably
even MacOS, but this is not tested.

It may run on windows, particularly the
`Windows Subsystem for Linux <https://learn.microsoft.com/en-us/windows/wsl/install>`_
or the 
`Cygwin <https://www.cygwin.com>`_
environment, but this is also not tested.

Install methods
---------------

Quickstart
++++++++++

If you just want to give sumo a try without going too much into installation
details, you can use the following recipe. Note that this creates the
directories 'VENV' and 'SUMO' in your HOME directory::

  cd $HOME
  python -m venv VENV
  source VENV/bin/activate
  pip install epics-sumo
  echo "source $HOME/VENV/bin/activate" > VENV/setenv.sh
  sumo help completion-script >> VENV/setenv.sh
  sumo config new SUMO sumo-free-database INITIAL
  source $HOME/VENV/setenv.sh

With ``source $HOME/VENV/setenv.sh`` your shell is set up to use sumo.

Now you may use sumo, for example as shown at `Using sumo`_.

Download and install with pip
+++++++++++++++++++++++++++++

`pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_ is the python
package manager. It is easy to use, the only disadvantage is that on Linux
when run as root it circumvents your package manager.

The following chapters show various methods for installing sumo with
`pip <https://en.wikipedia.org/wiki/Pip_(package_manager)>`_.

Install in a virtual environment
::::::::::::::::::::::::::::::::

`Python virtual environment <https://docs.python.org/3/library/venv.html>`_
an easy way to install python programs and libraries in a separate directory
that doesn`t interfere with the rest of your system.

If you do not yet have a virtual environment, create and activate one with::

  python -m venv DIRECTORY
  source DIRECTORY/bin/activate

Now install epics-sumo with::

  pip install epics-sumo

Now continue at
`The sumo configuration file`_ 

Install in your home
::::::::::::::::::::

This installs epics-sumo in your home directory, see
`pip --user <https://pip.pypa.io/en/stable/cli/pip_install/#cmdoption-user>`_.
Just enter::

  pip install --user epics-sumo

Now continue at
`The sumo configuration file`_ 

Install at PYTHONUSERBASE
:::::::::::::::::::::::::

If environment variable
`PYTHONUSERBASE <https://docs.python.org/3/using/cmdline.html#envvar-PYTHONUSERBASE>`_
is set, the following command installs epics-sumo there::

  pip install --user epics-sumo

Now continue at
`The sumo configuration file`_ 

Global installation
:::::::::::::::::::

When you have administrator rights, you install epics-sumo globally like this::

  sudo pip install epics-sumo

Now continue at
`The sumo configuration file`_ 

Install with pip from a file or directory
+++++++++++++++++++++++++++++++++++++++++

Install from downloaded \*.tar.gz or \*.whl file [1]_ [2]_::

  pip install FILENAME

Install from source directory [1]_ [3]_::

  pip install DIRECTORY

.. [1] You may need use option ``--user``, see
  `Install in your home`_ above.

.. [2] You can download these files at  
  `sumo downloads at Sourceforge <https://sourceforge.net/projects/epics-sumo/files/?source=navbar>`_

.. [3] You can checkout the repository with 
   ``hg clone http://hg.code.sf.net/p/epics-sumo/mercurial epics-sumo``

Now continue at
`The sumo configuration file`_ 

Global installation with the system package manager (Linux)
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

On systems with debian package manager (debian/ubuntu/suse...) [2]_ [4]_::

  dpkg -i PACKAGEFILE

On systems with rpm package manager (fedora/RHEL/CentOS...) [2]_ [5]_::

  rpm -ivh PACKAGEFILE

.. [4] The \*.deb files were created for Debian Linux. They may work for other
   debian based distributions like ubuntu but this was not tested.

.. [5] The \*.rpm files were created for Fedora Linux. They may work for other
   rpm based distributions like RedHat Linux but this was not tested.

Now continue at
`The sumo configuration file`_ 

The sumo configuration file
---------------------------

In order to use sumo on your system you should create a configuration file.

The easiest way create configuration file and the sumo directory SUMODIR is 
to use :ref:`sumo config new <reference-sumo-config-new>`.

If you are new to sumo, simply enter this commmand::

  sumo config new SUMODIR sumo-free-database INITIAL

This installs the 
`sumo-free-database <https://sourceforge.net/projects/sumo-free-database>`_.
dependency database in directory SUMODIR/database.

See :doc:`configuration-files` for a complete description of configuration files.

See :ref:`sumo.config examples <configuration-files-config-examples>` for examples
of configuration files.

Command completion
------------------

It is highly recommended that you set up command completion as described at
:ref:`Command completion <reference-sumo-command-completion>`.

Using sumo
----------

Here is a first example how to use sumo.

You can download and build EPICS Base. Note that downloading the sources
may take about 30 seconds. Do not be alarmed by compiler warnings during the
build process, they are harmless::

  sumo build new BASE:R3-15-9 --makeflags "-sj" --progress

After the build is finished, here are more commands you can
play with:

- :ref:`sumo db list <reference-sumo-db-list>`: Show modules in the database
- :ref:`sumo db list BASE <reference-sumo-db-list>`: Show versions of EPICS base in the database
- :ref:`sumo db show BASE:R3-15-9 <reference-sumo-db-show>`: Show details for EPICS base
- :ref:`sumo build list <reference-sumo-build-list>`: Show all builds.
- :ref:`sumo build show AUTO-001 <reference-sumo-build-show>`: Show details for
  build "AUTO-001".
- :ref:`sumo config list <reference-sumo-config-list>`: Show which configuration files are loaded
- :ref:`sumo config show <reference-sumo-config-show>`: Show current configuration
- :ref:`sumo help <reference-sumo-help>`: Show main page of the program's help
