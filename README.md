awk
=====

A library to provide advanced awk-like functionalities for file manipulation in Python.

Motivation
-------------

Help manipulating files organised in recrods and fields, providing helpers such as `Column` to extract to access the file by columns and header parsing for files containing a header on their first line.


Structure
------------

`awk` provides four main classes: `Record`, `Reader`, `Parser` and `Column`.

### `Reader` class
Provides facilities to read the file one `Record` at a time, possibly using the first line as header. If the header is provided then fields in the record can be accesses via the keys specified in the header, otherwise standard access is provided (see the [Record class](#reader-class) for the details).

### `Parser` class
Provides facilities to manipulate and filter out records and fields before reading them.

### `Record` class
Represents an awk record, it allows access to the record's fields by index, starting from 0, or by key. A key can be either of the form `'$2'`, as per the awk standard, or a string specified in the file's header. See the [Examples section](#examples) for a more detailed explanation of how indexing a record works.

### `Column` class
Provides a column-based access to the file. The columns can be specified as a key corresponding to one of the keys in the header or as a number in case there is no header. If no header is specified, this class can be used to extract slices of columns from the file.

### A note on efficiency
All the functions that parse files return generators. That is made to avoid loading huge files in ram before parsing them. Every piece of code in this library was made with attention to the efficiency of parsing large files.


Usage
--------

### Install

Using pip:

    sudo pip install awk

or cloning this repo:

    sudo python setup.py install

### Examples

#### Reader
Imagine to have the following file `testinput`:

	A B C D E F G
	2 8 0 0 5 7 7
	3 0 7 0 0 7 0
	2 3 5 6 6 6 8
	0 2 1 0 8 3 7

the following code will return every line as a record:

```python
from awk import Reader
with Reader('testinput') as reader:
    for record in reader:
        print(record)
```

output:

    Record($1: A, $2: B, $3: C, $4: D, $5: E, $6: F, $7: G)
    Record($1: 2, $2: 8, $3: 0, $4: 0, $5: 5, $6: 7, $7: 7)
    Record($1: 3, $2: 0, $3: 7, $4: 0, $5: 0, $6: 7, $7: 0)
    Record($1: 2, $2: 3, $3: 5, $4: 6, $5: 6, $6: 6, $7: 8)
    Record($1: 0, $2: 2, $3: 1, $4: 0, $5: 8, $6: 3, $7: 7)

the records in the output can be used to loop over their fields or to access their fields in the following fashions:
- `record[1]` (indices start from 0)
- `record[1:3:2]` (indices start from 0)
- `record['$2']` (indices start from `'$1'`)
    
The following code will parse the same file, parsing the header as keys for the various fields, and return a record:

```python
from awk import Reader
with Reader('testinput', header=True) as reader:
    for record in reader:
        print(record)
```

output:

    Record(A: 2, B: 8, C: 0, D: 0, E: 5, F: 7, G: 7)
    Record(A: 3, B: 0, C: 7, D: 0, E: 0, F: 7, G: 0)
    Record(A: 2, B: 3, C: 5, D: 6, E: 6, F: 6, G: 8)
    Record(A: 0, B: 2, C: 1, D: 0, E: 8, F: 3, G: 7)

Notice that despite the file has a header, we can still access the record's fields as specified in the example above,
but in this case also access by key (i.e. `record['B']`) is supported.


#### Parser
This is the class which most reflects the awk command philosophy, performing computation on a file organised in fields and records.
For instance, we can use the following code to square every value in our file:

```python
from awk import Parser
parser = Parser('testinput',
                header=True,
                ordered=True,
                field_func=lambda key, field: int(field)**2)
for record in parser.parse():
    print(record)
```

output:

    Record(A: 4, B: 64, C: 0, D: 0, E: 25, F: 49, G: 49)
    Record(A: 9, B: 0, C: 49, D: 0, E: 0, F: 49, G: 0)
    Record(A: 4, B: 9, C: 25, D: 36, E: 36, F: 36, G: 64)
    Record(A: 0, B: 4, C: 1, D: 0, E: 64, F: 9, G: 49)

We can make every record the sum of its fields:

```python
from awk import Parser
parser = Parser('testinput',
                header=True,
                ordered=True,
                field_func=lambda key, field: int(field)**2,
                record_func=lambda nr, nf, record: sum(record.values()))
for record in parser.parse():
    print(record)
```

output:

    191
    107
    210
    127

and filter out all fields whose key is a vowel and all records whose sum is greater than 100:

```python
from awk import Parser
parser = Parser('testinput',
                header=True,
                ordered=True,
                field_func=lambda key, field: int(field)**2,
                record_func=lambda nr, nf, record: sum(record.values()),
                field_pre_filter=lambda key, field: key not in 'AE',
                record_post_filter=lambda nr, nf, record: record > 100)
for record in parser.parse():
    print(record)
```

output

    162
    170

#### Column
This class provides column-based access to the file. Some examples:

Extracting a single column:

```python
from awk import Column
columns = Column('testinput')
print(list(columns[3]))
```

output:

    ('D', '0', '0', '6', '0')


Extracting the last column wit a two-lines limit:

```python
from awk import Column
columns = Column('testinput', max_lines=2)
print(list(columns[-1]))
```

output:

    ('G', '7')


Extracting columns 3 to 6:

```python
from awk import Column
columns = Column('testinput')
print(list(columns[3:6]))
```

output:

    (('D', '0', '0', '6', '0'), ('E', '5', '0', '6', '8'), ('F', '7', '7', '6', '3'))


Extracting every second column from 2 to 7:

```python
from awk import Column
columns = Column('testinput')
print(list(columns[2:7:2]))
```

output:

    (('C', '0', '7', '5', '1'), ('E', '5', '0', '6', '8'), ('G', '7', '0', '8', '7'))


Extracting the columns in reverse order with a limit of 3 lines:

```python
from awk import Column
columns = Column('testinput', max_lines=3)
print(list(columns[::-1]))
```

output:

    (('G', '7', '0'), ('F', '7', '7'), ('E', '5', '0'), ('D', '0', '0'), ('C', '0', '7'), ('B', '8', '0'), ('A', '2', '3'))

Extracting columns A, C and E:

```python
from awk import Column
columns = Column('testinput', header=True)
for line in columns.get('A', 'C', 'E'):
    print(line)
```

output:

    ('2', '0', '5')
    ('3', '7', '0')
    ('2', '5', '6')
    ('0', '1', '8')

Extracting columns 1, 3 and 5


```python
from awk import Column
columns = Column('testinput')
for line in columns.get(1, 3, 5):
    print(line)
```

output (remember that except when slicing, field and column indexes start from 1 as per the awk standard):

    ('A', 'C', 'E')
    ('2', '0', '5')
    ('3', '7', '0')
    ('2', '5', '6')
    ('0', '1', '8')


TODO list
--------------

* Allow to provide unary functions (e.g. int, float, etc.) as record_func and field_func which are given as input the field/record without key/nr/nf parameters

* Create a Writer class to store structured output on other files

* Allow to provide a custom record separator
