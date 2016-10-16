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

from itertools import zip_longest
from collections import OrderedDict


class FileNotOpenException(Exception):
    pass


class MissingHeaderException(Exception):
    pass

DEFAULT_FIELD_SEP = '\t'
DEFAULT_RECORD_SEP = '\n'


def _DEFAULT_FIELD_FUNC(field_key, field):
    return field


def _DEFAULT_FIELD_FILTER(field_key, field):
    return True


def _DEFAULT_RECORD_FUNC(NR, NF, record):
    return record


def _DEFAULT_RECORD_FILTER(NR, NF, record):
    return True


class Reader(object):

    def __init__(self, filename, fs=DEFAULT_FIELD_SEP, header=False, ordered=False):
        """Initialises a Reader

        Arguments:
        filename -- the name of the file to parse

        Keyword arguments:
        fs -- character that separates the fields
        header -- if set to True, the reader interprets the first line of the file as a header.
                  In this case every record is returned as a dictionary and every field in the header
                  is used as the key of the corresponding field in the following lines
        ordered -- if header i True, then the records will be output as `OrderedDict`s instead of normal dictionaries
        """
        self.filename = filename
        self.header = header
        self.fs = fs
        self.ordered = ordered
        self._openfile = None
        self._keys = None

    @property
    def keys(self):
        """returns the keys of the header if present, otherwise None"""
        return self._keys

    def __enter__(self):
        self._openfile = open(self.filename)
        if self.header:
            first_line = next(self._openfile).rstrip()
            self._keys = tuple(first_line.split(self.fs))
        return self

    def __exit__(self, *args):
        self._openfile.close()
        self._openfile = None

    def __iter__(self):
        return self

    def __next__(self):
        if self._openfile is None:
            raise FileNotOpenException
        line = next(self._openfile).rstrip()
        fields = tuple(line.split(self.fs))
        if self.header:
            if len(fields) > len(self._keys):
                zip_func = zip
            else:
                zip_func = zip_longest

            if not self.ordered:
                fields = {k: v for k, v in zip_func(self._keys, fields)}
            else:
                fields = OrderedDict((k, v) for k, v in zip_func(self._keys, fields))

        return fields


class Parser(object):

    def __init__(self,
                 filename,
                 fs=DEFAULT_FIELD_SEP,
                 header=False,
                 ordered=False,
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
        fs -- character that separates the fields
        header -- if set to True, the parser interprets the first line of the file as a header.
                  In this case every record is returned as a dictionary and every field in the header
                  is used as the key of the corresponding field in the following lines
        ordered -- if header i True, then the records will be output as `OrderedDict`s instead of normal dictionaries
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
        self.field_func = field_func
        self.record_func = record_func
        self.field_pre_filter = field_pre_filter
        self.record_pre_filter = record_pre_filter
        self.field_post_filter = field_post_filter
        self.record_post_filter = record_post_filter

    def _get_field(self, record):

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
        with Reader(self.filename, self.fs, self.header, self.ordered) as reader:
            for nr, record in enumerate(reader, 1):
                nf = len(record)
                if not self.record_pre_filter(nr, nf, record):
                    continue
                result = self._get_field(record)
                new_record = self.record_func(nr, nf, result)
                if self.record_post_filter(nr, nf, new_record):
                    yield new_record


def column(filename, key, fs=DEFAULT_FIELD_SEP, header=False, item_func=lambda x: x):
    """
    returns the key-th column of filename as a list starting from 1 if there is no header,
    otherwise it returns the column with key in the header
    If some records have less than key fields and there is no header, None is returned for those fields
    item_func(field) is applied to every field before returning it
    """
    parser = Parser(filename, fs, header, field_pre_filter=lambda field_key, field: field_key == key)
    for record in parser.parse():
        try:
            if header:
                yield item_func(next(iter(record.values())))
            else:
                yield item_func(record[0])
        except IndexError:
            # the current line does not have column n
            yield None
