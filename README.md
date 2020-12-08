RPySOM - The Simple Object Machine Smalltalk combining Self-Optimizing Interpreters with Meta-Tracing
======================================================================

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

This repository contains a RPython-based implementation of SOM, including
SOM's standard library and a number of examples. Please see the [main project
page][SOMst] for links to other VM implementations.

The implementation use either an abstract-syntax-tree or a 
bytecode-based interpreter. One can chose between them with the `SOM_INTERP` environment variable.

 - AST-based interpreter: `SOM_INTERP=AST`
 - bytecode-based interpreter: `SOM_INTERP=BC`

To checkout the code:

    git clone https://github.com/SOM-st/RPySOM.git

RPySOM's tests can be executed with:

    $ ./som.sh -cp Smalltalk TestSuite/TestHarness.som
   
A simple Hello World program is executed with:

    $ ./som.sh -cp Smalltalk Examples/Hello/Hello.som

To compile RPySOM, a recent PyPy is recommended and the RPython source
code is required. The source distribution of PyPy 7.3 can be used like this:

    wget https://downloads.python.org/pypy/pypy2.7-v7.3.1-src.tar.bz2
    tar xvf pypy-5.1.1-src.tar.bz2
    export PYPY_DIR=`pwd`/pypy-5.1.1-src/

Information on previous authors are included in the AUTHORS file. This code is
distributed under the MIT License. Please see the LICENSE file for details.

Build Status
------------

Thanks to Travis CI, all commits of this repository are tested.
The current build status is: [![Build Status](https://travis-ci.org/SOM-st/RPySOM.png?branch=master)](https://travis-ci.org/SOM-st/RPySOM)

 [SOM]: http://www.hpi.uni-potsdam.de/hirschfeld/projects/som/
 [SOMst]: https://travis-ci.org/SOM-st/
 [RS]:  http://dx.doi.org/10.1016/j.cl.2005.02.003
