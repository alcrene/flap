#!/usr/bin/env python

#
# This file is part of Flap.
#
# Flap is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Flap is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Flap.  If not, see <http://www.gnu.org/licenses/>.
#

from flap import __version__

from flap.util.path import Path


class Display:

    PADDING = "-"

    FILE_WIDTH = 30
    LINE_WIDTH = 5
    COLUMN_WIDTH = 6
    CODE_WIDTH = 35

    ENTRY = "{file:<%d} {line:>%d} {column:>%d} {code:<%d}\n" % (FILE_WIDTH, LINE_WIDTH, COLUMN_WIDTH, CODE_WIDTH)
    HEADER = ENTRY.format(file="File", line="Line", column="Column", code="LaTeX Command")
    SUMMARY = "{count} modification(s)"

    def __init__(self, output):
        self._output = output

    def version(self):
        self._output.write("FLaP v%s\n" % __version__)

    def header(self):
        self._show(self.HEADER)
        self._show(self._horizontal_line())

    def entry(self, file, line, column, code):
        self._show(self.ENTRY, file=file, line=line, column=column, code=code)

    def footer(self):
        self._show(self._horizontal_line())
        self._show(self.SUMMARY, count=1)

    def _horizontal_line(self):
        return self.ENTRY.format(
                   file=self._pad(self.FILE_WIDTH),
                   line=self._pad(self.LINE_WIDTH),
                   column=self._pad(self.COLUMN_WIDTH),
                   code=self._pad(self.CODE_WIDTH))

    @classmethod
    def _pad(cls, length):
        return "".ljust(length, cls.PADDING)

    def _show(self, template, **values):
        self._output.write(template.format(**values))


class Controller:

    def __init__(self, file_system, display):
        self._file_system = file_system
        self._display = display

    def run(self, arguments):
        self._display.version()
        self._display.header()
        self._display.entry(file="test.tex", line=2, column=1, code="\\input{result.tex}")
        self._display.footer()

        self._file_system.create_file(Path.fromText("output/merged.tex"),
                                      "Blabla \n"
                                      "Some results \n"
                                      "Blabla \n")