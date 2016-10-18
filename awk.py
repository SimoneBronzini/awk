"""
MIT License

Copyright (c) 2016 Simone Bronzini

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import re
from itertools import zip_longest
from collections import OrderedDict


class SliceWithHeaderException(Exception):
    pass


class FileNotOpenException(Exception):
    pass


class MissingHeaderException(Exception):
    pass


class UnboundedColumnException(Exception):
    pass


DEFAULT_FIELD_SEP = r'\s+'


def _DEFAULT_FIELD_FUNC(field_key, field):
    return field


def _DEFAULT_FIELD_FILTER(field_key, field):
    return True


def _DEFAULT_RECORD_FUNC(NR, NF, record):
    return record


def _DEFAULT_RECORD_FILTER(NR, NF, record):
    return True


class Reader(object):

    def __init__(self, filename, fs=DEFAULT_FIELD_SEP, header=False, ordered=False, max_lines=None):
        """Initialises a Reader

        Arguments:
        filename -- the name of the file to parse

        Keyword arguments:
        fs -- regex that separates the fields
        header -- if set to True, the reader interprets the first line of the file as a header.
                  In this case every record is returned as a dictionary and every field in the header
                  is used as the key of the corresponding field in the following lines
        ordered -- if header i True, then the records will be output as `OrderedDict`s instead of normal dictionaries
        max_lines -- the maximum number of lines to read
        """
        self.filename = filename
        self.header = header
        self.fs = fs
        self.ordered = ordered
        self.max_lines = max_lines
        self._compiled_fs = re.compile(fs)
        self._openfile = None
        self._keys = None

    @property
    def keys(self):
        """returns the keys of the header if present, otherwise None"""
        return self._keys

    def __enter__(self):
        self._openfile = open(self.filename)
        self.lines = 0
        if self.header:
            first_line = next(self._openfile).rstrip()
            self._keys = tuple(self._compiled_fs.split(first_line))
        return self

    def __exit__(self, *args):
        self._openfile.close()
        self.lines = 0
        self._openfile = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._openfile is None:
            raise FileNotOpenException

        if self.max_lines is not None and self.lines >= self.max_lines:
            raise StopIteration

        line = next(self._openfile).rstrip()
        fields = tuple(self._compiled_fs.split(line))

        if self.header:
            if len(fields) > len(self._keys):
                zip_func = zip
            else:
                zip_func = zip_longest

            if not self.ordered:
                fields = {k: v for k, v in zip_func(self._keys, fields)}
            else:
                fields = OrderedDict((k, v) for k, v in zip_func(self._keys, fields))

        self.lines += 1

        return fields


class Parser(object):

    def __init__(self,
                 filename,
                 fs=DEFAULT_FIELD_SEP,
                 header=False,
                 ordered=False,
                 max_lines=None,
                 field_func=_DEFAULT_FIELD_FUNC,
                 record_func=_DEFAULT_RECORD_FUNC,
                 field_pre_filter=_DEFAULT_FIELD_FILTER,
                 record_pre_filter=_DEFAULT_RECORD_FILTER,
                 field_post_filter=_DEFAULT_FIELD_FILTER,
                 record_post_filter=_DEFAULT_RECORD_FILTER):
        """Initialise a Parser

        Arguments:
        filename -- the name of the file to parse

        Keyword arguments:
        fs -- a regex that separates the fields
        header -- if set to True, the parser interprets the first line of the file as a header.
                  In this case every record is returned as a dictionary and every field in the header
                  is used as the key of the corresponding field in the following lines
        ordered -- if header is True, then the records will be output as `OrderedDict`s instead of normal dictionaries
        max_lines -- the maximum number of lines to parse
        field_func -- a function f(field_key, field) which is applied to every field, field_key is
                      the number of the field if there is no header, the corresponding header key otherwise.
                      default: a function that returns the field
        record_func -- a function f(NR, NF, field) which is applied to every record, NR is the record number
                       NF is the total number of fields in the record.
                       default: a function that returns the record
        field_pre_filter -- a function f(field_key, field) which is applied to the field before `field_func`.
                            If it returns a falsy value, the field is not returned.
                            default: lambda *args: True
        record_pre_filter -- a function f(NR, NF, field) which is applied to the record before `record_func`.
                             If it returns a falsy value, the record is not returned
                             default: lambda *args: True
        field_post_filter -- a function f(field_key, field) which is applied to the field after `field_func`.
                             If it returns a falsy value, the field is not returned.
                             default: lambda *args: True
        record_post_filter -- a function f(NR, NF, field) which is applied to the record after `record_func`.
                              If it returns a falsy value, the record is not returned
                              default: lambda *args: True
        """

        self.filename = filename
        self.header = header
        self.fs = fs
        self.ordered = ordered
        self.max_lines = max_lines
        self.field_func = field_func
        self.record_func = record_func
        self.field_pre_filter = field_pre_filter
        self.record_pre_filter = record_pre_filter
        self.field_post_filter = field_post_filter
        self.record_post_filter = record_post_filter

    def _get_fields(self, record):

        if self.header:
            # expect a dict
            fields = record.items()
        else:
            # expect a list
            fields = enumerate(record, 1)

        result = []
        for key, val in fields:
            if self.field_pre_filter(key, val):
                new_field = self.field_func(key, val)
                if self.field_post_filter(key, new_field):
                    result.append((key, new_field))

        if self.header:
            if self.ordered:
                # return an OrderedDict
                return OrderedDict(result)
            # return a dict
            return dict(result)
        # return a list
        return [val for key, val in result]

    # TODO: add writing capabilities
    def parse(self):
        """Parse the file provided at initialisation time
        returns a generator of records, where every record is a dictionary if the file has a header,
        a list otherwise. The records returned and the fields in them are the result of the application
        of record_func and field_func respectively.
        Only records respecting the pre and post filters are present, same applies for the fields in each record
        """
        with Reader(self.filename, self.fs, self.header, self.ordered, self.max_lines) as reader:
            for nr, record in enumerate(reader, 1):
                nf = len(record)
                if not self.record_pre_filter(nr, nf, record):
                    continue
                result = self._get_fields(record)
                new_record = self.record_func(nr, nf, result)
                if self.record_post_filter(nr, nf, new_record):
                    yield new_record


class Column(object):

    def __init__(self,
                 filename,
                 fs=DEFAULT_FIELD_SEP,
                 header=False,
                 max_lines=None,
                 field_func=lambda x: x,
                 column_func=lambda x: x):
        """
        Initialise a Column object.
        Arguments:
        filename -- the name of the file to parse
        Keyword arguments:
        fs -- a regex that separates the fields
        header -- if set to True, the parser interprets the first line of the file as a header.
                  In this case the columns can be indexed as the key specified in the header and the first
                  element of the column is the header
        max_lines -- the maximum number of lines to parse
        field_func -- a function f(field) which is applied to every field. Default: a function that returns the field
        column_func -- a function f(column) which is applied to every clumn before returning it.
                       Default: a function that returns the field
        """
        self.filename = filename
        self.fs = fs
        self.header = header
        self.max_lines = max_lines
        self.field_func = field_func
        self.column_func = column_func

    def __getitem__(self, index):
        """
        if index is a slice, it returns a tuple of columns, where each column is the result
        of the application of `column_func()` on the column. If `header` is True, `index`
        must be a key in the header, otherwise it can be an integer. In those cases, the result
        of the application of `column_func()` on the single column is returned. `field_func()`
        is applied to every field in the column(s).
        In the case of slicing, indexes start from 0 to make slicing simpler. Please note that this function needs
        to parse the whole file unless max_lines is specified in the constructor
        """

        parser = Parser(self.filename,
                        self.fs,
                        self.header,
                        ordered=True,
                        max_lines=self.max_lines,
                        field_func=lambda key, field: self.field_func(field))

        if isinstance(index, slice):
            if self.header:
                raise SliceWithHeaderException('Cannot use slicing when a header is specified')
            columns = OrderedDict()
            for record in parser.parse():
                for i, field in enumerate(record[index]):
                    if i not in columns:
                        columns[i] = []
                    columns[i].append(field)
            # post-processing
            return [self.column_func(tuple(column)) for column in tuple(columns.values())]
        else:
            column = []
            for record in parser.parse():
                fields = list(record.values()) if self.header else record
                try:
                    column.append(fields[index])
                except IndexError:
                    column.append(None)
            return self.column_func(tuple(column))

    def get(self, *keys):
        """
        returns a generator of tuples where every element in the tuple is the field of the corresponding
        column. For example, if passed three keys, every tuple will have three elements.
        Please note that this function needs to parse the whole file unless max_lines is specified in
        the constructor

        """
        parser = Parser(self.filename,
                        self.fs,
                        self.header,
                        ordered=True,
                        field_pre_filter=lambda field_key, field: field_key in keys)
        for record in parser.parse():
            if self.header:
                record = record.values()
            yield tuple(record)
