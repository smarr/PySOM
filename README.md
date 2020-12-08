PySOM - The Simple Object Machine Smalltalk
===========================================

Introduction
------------

SOM is a minimal Smalltalk dialect used to teach VM construction at the [Hasso
Plattner Institute][SOM]. It was originally built at the University of Århus
(Denmark) where it was used for teaching and as the foundation for [Resilient
Smalltalk][RS].

In addition to RPySOM, other implementations exist for Java (SOM, TruffleSOM),
C (CSOM), C++ (SOM++), Python (PySOM), and Squeak/Pharo Smalltalk (AweSOM).

A simple Hello World looks like:

```Smalltalk
Hello = (
  run = (
    'Hello World!' println.
  )
)
```

This repository contains a Python-base implementation of SOM, including
SOM's standard library and a number of examples. Please see the [main project
page][SOMst] for links to other VM implementations.

The implementation use either an abstract-syntax-tree or a 
bytecode-based interpreter. One can chose between them with the `SOM_INTERP` environment variable.

 - AST-based interpreter: `SOM_INTERP=AST`
 - bytecode-based interpreter: `SOM_INTERP=BC`

To checkout the code:

    git clone https://github.com/SOM-st/PySOM.git

PySOM's tests can be executed with:

    $ ./som.sh -cp Smalltalk TestSuite/TestHarness.som
   
A simple Hello World program is executed with:

    $ ./som.sh -cp Smalltalk Examples/Hello/Hello.som

To compile PySOM, a recent PyPy is recommended and the RPython source
code is required. The source distribution of PyPy 7.3 can be used like this:

    wget https://downloads.python.org/pypy/pypy2.7-v7.3.1-src.tar.bz2
    tar xvf pypy2.7-v7.3.1-src.tar.bz2
    export PYPY_DIR=`pwd`/pypy2.7-v7.3.1-src/

Information on previous authors are included in the AUTHORS file. This code is
distributed under the MIT License. Please see the LICENSE file for details.


History
-------

In 2013, the implementations of PySOM, RPySOM, and RTruffleSOM where split
over multiple repositories. Since end of 2020, they are reunited here and PySOM
can be used with Python 2.7, Python 3.8, as well as compiled with RPython.
Thus, https://github.com/SOM-st/PySOM is again the only and the canonical
repository.


Build Status
------------

Thanks to Travis CI, all commits of this repository are tested.
The current build status is: [![Build Status](https://travis-ci.com/SOM-st/PySOM.png?branch=master)](https://travis-ci.com/SOM-st/PySOM)

 [SOM]: http://www.hpi.uni-potsdam.de/hirschfeld/projects/som/
 [SOMst]: https://travis-ci.org/SOM-st/
 [RS]:  http://dx.doi.org/10.1016/j.cl.2005.02.003
