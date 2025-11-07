sumo ioc
========

This page describes how you can build an 
`EPICS <http://www.aps.anl.gov/epics>`_ 
IOC for Linux with sumo
with the help of a simple script that does all the work for you.

Prepare the directory
+++++++++++++++++++++

First we create a new directory where we will store all the 
sources and programs. Enter these commands::

  cd $HOME
  mkdir sumo-ioc
  cd sumo-ioc

Now you need to download the build script and put it in the
directory you just created:

- :download:`downloads/ioc/create-sumo-ioc.sh`

You have to make the downloaded script executable with this command::

  chmod u+x *.sh

The script options
++++++++++++++++++

.. note::
   If you don't want to know about details now and just want to try this example 
   skip to the next section 'Running the script'.

The script has some options that you can use to control names of directories 
and weather a python virtual environment is created.

You get a short help for the script options with::

  ./create-sumo-ioc.sh -h

This is the help text::

  create-sumo-ioc.sh - create a sample softIOC on your host with sumo
  
  It is necessary that your host is connected to the internet
  
  Usage:
  
  create-sumo-ioc.sh [OPTIONS]
  
  OPTIONS:
    -h --help  : this help
    -V --venv  : Always create a python virtual environment. The default
                 is that the program asks you if you want to create one.
    -7 --base7 : Build for EPICS Base 7, base 3 is the default.
    --iocname IOCNAME :
                 name of the IOC, default: 'myIOC'.
    --iocdir DIRECTORY :
                 name of the IOC directory, default: 'IOC'.
    --sumodir DIRECTORY :
                 name of the sumo directory, default: 'SUMO'.
    --venvdir DIRECTORY :
                 name of the virtual environment directory, default: 'VENV'.
  
Running the script
++++++++++++++++++

.. note::
   Below we assume that you didn't change the names of default
   directories with options of the build script ``create-sumo-ioc.sh``.

In order to build the IOC with a python virtual environment and EPICS Base 3.15
enter::

  ./create-sumo-ioc.sh -V

This installs sumo in a python virtual environment, builds EPICS Base
and creates a very simple IOC.

.. note::
   All you need to know to play with this IOC is also shown in file
   'README.txt'.

You can start the IOC with the following command. The interactive IOC shell
will run in your text terminal window::

  ./IOC/start_ioc.sh

The IOC has a single record, named 'trigger' that increments it's value 
every second.

This can be shown with the ``camonitor`` command. To run this commands
open a new text terminal while the IOC is running and change to the 
directory of the sumo ioc project. If you used the proposed directory from the
top of this page, this would be ``$HOME/sumo-ioc``, enter::

  cd $HOME/sumo-ioc

Now you have to set some environment variables in order to be able to use sumo
and scripts from EPICS Base, enter::

  source setenv.sh

Now you can watch the changes of the 'trigger' record::

  camonitor trigger

How improve this example
++++++++++++++++++++++++

In order to use other device supports you have to add new entries to file 
``configure/MODULES`` in the ``IOC`` directory.

All device supports you add in ``MODULES`` must be defined in file
``SUMO/database/DEPS.DB``. You can extend this file, the format
is described
at :ref:`dependency database <reference-sumo-db-The-dependency-database>`.

When you have changed file ``MODULES`` you have to download and build the new 
device support with::

  sumo build new --makeflags "-sj" --progress

The two options at the end are not strictly necessary but do speed up the build
process and show the download progress.

You then have to update your IOC project to use the new device support. You
have to be in your ``IOC`` directory for this::

  sumo build use

Then recompile the IOC with::

  make clean -sj && make -sj


