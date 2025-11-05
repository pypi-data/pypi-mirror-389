## Overview

This package is intended for:

*  the arithmetic of natural sexagesimal numbers, mainly in their “floating” aspect (i.e., by removing all possible trailing sexagesimal zeros from the right), as performed by the Babylonian scribes and their apprentices in ancient times. 

* the arithmetic of physical quantities, length, surface, etc. described using the metrology of the Old Babylonian Period.

Inspired by the arithmetic and metrological parts of Baptiste Mélès' [MesoCalc](https://github.com/BapMel/mesocalc), it aims to bring this type of calculation to `Python3` programming and to the `Python3` command line as an interactive calculator.

`mesomath` module contains four submodules:

*  `babn.py`
*  `hamming.py`
*  `mesolib.py`
*  `npvs`


one utility script:

*  `createDB.py`

one example script:

*  `example-melville.py`

four test/demo scripts:

*  `test-babn.py`
*  `test-hamming.py`
*  `test-mesolib.py`
*  `test-npvs.py`

and two applications in the `progs` subdirectory:

*  `metrotable.py` to print segments of metrological tables.
*  `mtlookup.py` to search for the abstract number that corresponds to a measure or to list measures that correspond to a given abstract number.

## Documentation

Documentation for this package is in [Read the Docs](https://mesomath.readthedocs.io/index.html),

Includes:

* A [tutorial on using this package as a command-line calculator](https://mesomath.readthedocs.io/tutorial.html).
* Tutorials for the two included applications:
* * [`metrotable`](https://mesomath.readthedocs.io/progs/metrotable.html)
* * [`mtlookup`](https://mesomath.readthedocs.io/progs/mtlookup.html)


## Dependencies

`mesomath` only uses  standard Python modules: `math`, `itertools`, `argparse`, `sys`, `re` and `sqlite3`. 

Tested with Python 3.11.2 under Debian GNU/Linux 12 (bookworm) in x86_64 and aarch64 (raspberrypi 5).

##   `babn.py`

This is the main module defining the `BabN` class for representing sexagesimal natural numbers. You can perform mathematical operations on objects of the `BabN` class using the operators +, -, *, **, /, and //, and combine them using parentheses, both in a program and interactively on the Python command line. It also allows you to obtain their reciprocals in the case of regular numbers, their approximate inverses in the general case, approximate square and cube floating roots and obtain divisors and lists of "nearest" regular numbers. See the `test-babn.py` script.

### Note:

*  Operator `/` return the approximate floating division of `a/b` for any pair of numbers.
*  Operator `//` is for the "Babylonian Division" of `a` by `b`, i.e. `a//b` returns `a` times the reciprocal of `b`, which requires `b` to be regular.

###  Use as an interactive calculator

Consult the [tutorial](https://mesomath.readthedocs.io/tutorial.html)!

The easiest way is to invoque the interactive python interpreter and import the class BabN; for instance

    $ python3 -i
    Python 3.11.2 (main, Apr 28 2025, 14:11:48) [GCC 12.2.0] on linux
    Type "help", "copyright", "credits" or "license" for more information.
    >>> from mesomath.babn import BabN as bn
    >>> a = bn(405)
    >>> a
    6:45
    >>>  (etc.)

or, with ipython:

    $ ipython3 
    Python 3.11.2 (main, Apr 28 2025, 14:11:48) [GCC 12.2.0]
    Type 'copyright', 'credits' or 'license' for more information
    IPython 8.5.0 -- An enhanced Interactive Python. Type '?' for help.

    In [1]: from mesomath.babn import BabN as bn

    In [2]: a = bn(405)

    In [3]: a
    Out[3]: 6:45

    In [4]: a.explain()
    |  Sexagesimal number: [6, 45] is the decimal number: 405.
    |    It may be written as 2^0 * 3^4 * 5^1 * 1),
    |    so, it is a regular number with reciprocal: 8:53:20

    In [5]:  (etc.)


But you can also create an executable script for your operating system that invokes the interpreter; for example, on Linux, create a file named `babcal` containing (customize `PYTHONPATH` below to your needs) :

    #!/usr/bin/env -S PYTHONPATH={path to directory containing mesomath module}  python3 -i -c 'from mesomath.babn import BabN as bn; print("\nWelcome to Babylonian Calculator\n    ...the calculator that every scribe should have!\nUse: bn(number)\n")'

then, after making it executable and instaling it somewhere on the PATH: 

    $ babcalc
    
    Welcome to Babylonian Calculator
    ...the calculator that every scribe should have!
    Use: bn(number)
    
    >>> a = bn(405)
    >>> a
    6:45
    >>>  (etc.)


## `hamming.py`

Regular or Hamming numbers are numbers of the form:

    H = 2^i * 3^j × 5^k
    
    where  i, j, k ≥ 0 

This module is used to obtain lists of such numbers and ultimately build a SQLite3 database of them up to 20 sexagesimal digits. This database is used by BabN to search for regular numbers close to a given one. See the scripts: `createDB.py` and `test-hamming.py`.

## `mesolib.py`

This is a rather obsolete module, as its functionality has been moved to the methods of the `BabN` class. It can be safely ignored and will likely be removed in the future. In any case, please refer to the `test-mesolib.py` script.

## `npvs.py`

This module defines the generic class `Npvs` for handling measurements in various units within a system. It is built using length measurements in the imperial system of units, from inches to leagues, as an example. This class is inherited by the `_MesoM` class which adapts it to Mesopotamian metrological use. The `_MesoM` class, in turn, is inherited by:

*  class `BsyG`: Babylonian counting System G (iku ese bur bur_u sar sar_u sar_gal)
*  class `BsyS`: Babylonian counting  System S (dis u ges gesu sar sar_u sar_gal)
*  class `MesoM`: To represent physical quantities, inherited by:
    *  class `Blen`: Babylonian length system (susi kus ninda us danna)
    *  class `Bsur`: Babylonian surface system (se gin sar gan)
    *  class `Bvol`: Babylonian volume system  (se gin sar gan)
    *  class `Bcap`: Babylonian capacity system  (se gin sila ban bariga gur)
    *  class `Bwei`: Babylonian weight system (se gin mana gu)
    *  class `Bbri`: Babylonian brick counting system (se gin sar gan)

Please, read the [tutorial](https://mesomath.readthedocs.io/tutorial.html) to see how to use all these classes.

##  `createDB.py`

This script has become more or less obsolete since its functionality was incorporated into the BabN class, which now creates the regular number database if it cannot find it when needed.

Use:

    $ python3 createDB.py

to create the default regular number database `regular.db3` in your directory.  You can also use:

    $ python3 createDB.py -o 'path/name'

to create it in a non-standar location. In this case, think of using:

    BabN.database = 'path/name'

to inform `BabN`  of its location.

##  `example-melville.py`

This script shows the application of `mesomath` to the solution of two real examples given by Duncan J. Melville in: [Reciprocals and Reciprocal algorithms in Mesopotamian Mathematics (2005)](https://www.researchgate.net/publication/237309438_RECIPROCALS_AND_RECIPROCAL_ALGORITHMS_IN_MESOPOTAMIAN_MATHEMATICS)

    $ python3 example-melville.py 

Output:

    Searching the reciprocal of 2:5  according to D. J. Melville (2005)

    Example 1: from Table 2. Simple Reciprocal algorithm

    d1 = BabN('2:5')
    r1 = d1.tail()
    r2 = r1.rec()
    r3 = d1 * r2
    r4 = r3.rec()
    r5 = r4 * r2

    Result r5 =  28:48

    Example 2: from Table 3. using "The Technique"

    r1 = d1.tail()
    r2 = r1.rec()
    r3 = d1.head() * r2
    r4 = r3+BabN(1)
    r5 = r4.rec()
    r6 = r5 * r2

    Result r6 =  28:48
