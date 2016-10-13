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

from unittest import TestCase, main
from mock import MagicMock

from flap.latex.symbols import SymbolTable
from flap.latex.tokens import TokenFactory
from flap.latex.lexer import Lexer
from flap.latex.parser import Parser, Macro, Environment


class ParserTests(TestCase):

    def setUp(self):
        self._engine = MagicMock()
        self._symbols = SymbolTable.default()
        self._tokens = TokenFactory(self._symbols)
        self._environment = Environment()
        self._lexer = Lexer(self._symbols)
        self._parser = Parser(self._lexer, self._engine, self._environment)

    def test_parsing_a_regular_word(self):
        self._do_test_with("hello", "hello")

    def _do_test_with(self, input, output):
        tokens = self._parser.rewrite(self._lexer.tokens_from(input))
        self._verify_output_is(output, tokens)

    def _verify_output_is(self, expected_text, actual_tokens):
        output = "".join(str(t) for t in actual_tokens)
        self.assertEqual(expected_text, output)

    def test_rewriting_a_group(self):
        self._do_test_with("{bonjour}",
                           "{bonjour}")

    def test_rewriting_a_command_that_shall_not_be_rewritten(self):
        self._do_test_with(r"\macro[option=23cm]{some text}",
                           r"\macro[option=23cm]{some text}")

    def test_rewriting_a_command_within_a_group(self):
        self._do_test_with(r"{\macro[option=23cm]{some text} more text}",
                           r"{\macro[option=23cm]{some text} more text}")

    def test_rewriting_a_command_in_a_verbatim_environment(self):
        self._do_test_with(r"\begin{verbatim}\foo{bar}\end{verbatim}",
                           r"\begin{verbatim}\foo{bar}\end{verbatim}")

    def test_rewriting_a_input_in_a_verbatim_environment(self):
        self._engine.content_of.return_value = "blabla"
        self._do_test_with(r"\begin{verbatim}\input{bar}\end{verbatim}",
                           r"\begin{verbatim}\input{bar}\end{verbatim}")
        self._engine.content_of.assert_not_called()

    def test_rewriting_a_unknown_environment(self):
        self._do_test_with(r"\begin{center}blabla\end{center}",
                           r"\begin{center}blabla\end{center}")

    def test_parsing_a_macro_definition(self):
        self._do_test_with(r"\def\myMacro#1{my #1}",
                           r"")

    def test_parsing_commented_out_input(self):
        self._do_test_with(r"% \input my-file",
                           r"% \input my-file")
        self._engine.content_of.assert_not_called()

    def test_invoking_a_macro_with_one_parameter(self):
        self._define_macro(r"\foo", "(#1)", "{bar #1}")
        self._do_test_with(r"\foo(1)", "bar 1")

    def _define_macro(self, name, parameters, body):
        macro = self._macro(name, parameters, body)
        self._environment[name] = macro

    def _macro(self, name, parameters, body):
        return Macro(name, self._tokenize(parameters), self._tokenize(body))

    def _tokenize(self, text):
        return list(self._lexer.tokens_from(text))

    def test_invoking_a_macro_where_one_argument_is_a_group(self):
        self._define_macro(r"\foo", "(#1)", "{Text: #1}")
        self._do_test_with(r"\foo({bar!})",
                           r"Text: bar!")

    def test_invoking_a_macro_with_two_parameters(self):
        self._define_macro(r"\point", "(#1,#2)", "{X=#1 and Y=#2}")
        self._do_test_with(r"\point(12,{3 point 5})", "X=12 and Y=3 point 5")

    def test_defining_a_macro_without_parameter(self):
        self._do_test_with(r"\def\foo{X}",
                           r"")
        self.assertEqual(self._macro(r"\foo", "", "{X}"), self._environment[r"\foo"])

    def test_defining_a_macro_with_one_parameter(self):
        self._do_test_with(r"\def\foo#1{X}",
                           r"")
        self.assertEqual(self._macro(r"\foo", "#1", "{X}"), self._environment[r"\foo"])

    def test_defining_a_macro_with_multiple_parameters(self):
        self._do_test_with(r"\def\point(#1,#2,#3){X}",
                           r"")
        self.assertEqual(self._macro(r"\point", "(#1,#2,#3)", "{X}"),
                         self._environment[r"\point"])

    def test_macro(self):
        self._do_test_with(r"\def\foo{X}\foo",
                           r"X")

    def test_macro_with_one_parameter(self):
        self._do_test_with(r"\def\foo#1{x=#1}\foo{2}",
                           r"x=2")

    def test_macro_with_inner_macro(self):
        self._do_test_with(r"\def\foo#1{\def\bar#1{X #1} \bar{#1}} \foo{Y}",
                           r"  X Y")

    def test_parsing_input(self):
        self._engine.content_of.return_value = "File content"
        self._do_test_with(r"\input{my-file}",
                           r"File content")
        self._engine.content_of.assert_called_once_with("my-file")

    def test_macro_with_inner_redefinition_of_input(self):
        self._engine.content_of.return_value = "File content"
        self._do_test_with(r"\def\foo#1{\def\input#1{File: #1} \input{#1}} \foo{test.tex}",
                           r"  File: test.tex")

    def test_macro_with_inner_use_of_input(self):
        self._engine.content_of.return_value = "blabla"
        self._do_test_with(r"\def\foo#1{File: \input{#1}} \foo{test.tex}",
                           r" File: blabla")


if __name__ == '__main__':
    main()
