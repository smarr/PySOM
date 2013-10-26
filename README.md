PySOM - The Simple Object Machine Smalltalk implemented in Python
=================================================================

Introduction
------------

SOM is a minimal Smalltalk dialect used to teach VM construction at the [Hasso
Plattner Institute][SOM]. It was originally built at the University of Århus
(Denmark) where it was used for teaching and as the foundation for [Resilient
Smalltalk][RS].

In addition to PySOM, other implementations exist for Java (SOM, TruffleSOM),
C (CSOM), C++ (SOM++), and Squeak/Pharo Smalltalk (AweSOM).

A simple Hello World looks like:

```Smalltalk
Hello = (
  run = (
    'Hello World!' println.
  )
)
```

This repository contains the Python-based implementation of SOM, including
SOM's standard library and a number of examples. Please see the [main project
page][SOMst] for links to other VM implementations.

PySOM's tests can be executed with:

    $ ./som.sh -cp Smalltalk TestSuite/TestHarness.som
   
A simple Hello World program is executed with:

    $ ./som.sh -cp Smalltalk Examples/Hello/Hello.som


Information on previous authors are included in the AUTHORS file. This code is
distributed under the MIT License. Please see the LICENSE file for details.

Build Status
------------

Thanks to Travis CI, all commits of this repository are tested.
The current build status is: [![Build Status](https://travis-ci.org/SOM-st/PySOM.png?branch=master)](https://travis-ci.org/SOM-st/PySOM)

 [SOM]: http://www.hpi.uni-potsdam.de/hirschfeld/projects/som/
 [SOMst]: https://travis-ci.org/SOM-st/
 [RS]:  http://dx.doi.org/10.1016/j.cl.2005.02.003
