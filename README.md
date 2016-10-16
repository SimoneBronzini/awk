awk
=====

A library to provide advanced awk-like functionalities to file manipulation in Python.

Motivation
-------------

Help manipulating files organised in recrods and fields, providing helpers such as `column` to extract a single column from the file and header parsing for files containing a header on their first line.


Organisation
------------

`awk` provides two main classes: `Reader` and `Parser`, plus a function `column`.

+ **Reader class**

Provides facilities to read the file one record at a time, possibly using the first line as header. If the header is provided then every record is returned as a dictionary having as keys the header fields, otherwise every record is a tuple of fields

ADD EXAMPLES

+ **Parser class**
TODO

Usage
--------

### 1) Install

    sudo python setup.py install

### 2) Uninstall

    sudo python setup.py uninstall

