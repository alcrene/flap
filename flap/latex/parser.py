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

from flap.latex.commons import Stream
from flap.latex.tokens import Token, TokenFactory


class Macro:
    """
    A LaTeX macro, including its name (e.g., '\point'), its signature as a list of expected tokens (e.g., '(#1,#2)')
    and the text that should replace it.
    """

    def __init__(self, name, signature, replacement):
        self._name = name
        self._signature = signature
        self._body = replacement

    @property
    def name(self):
        return self._name

    def parse_with(self, parser):
        return parser.evaluate_macro(self._name, self._signature, self._body)

    def __eq__(self, other):
        if not isinstance(other, Macro):
            return False
        return self._name == other._name and \
               self._signature == other._signature and \
               self._body == other._body

    def __repr__(self):
        signature = "".join(str(each_token) for each_token in self._signature)
        body = "".join(str(each_token) for each_token in self._body)
        return r"\def" + self._name + signature + body


class Environment:

    def __init__(self):
        self._definitions = dict()

    def __setitem__(self, key, value):
        self._definitions[key] = value

    def __getitem__(self, macro_name):
        return self._definitions.get(macro_name)

    def __contains__(self, macro_name):
        assert isinstance(macro_name, str), \
            "Invalid macro name. Expected string, but found '{0}' object instead.".format(type(macro_name))
        return macro_name in self._definitions


class Parser:

    def __init__(self, lexer, engine, environment):
        self._lexer = lexer
        self._tokens = None
        self._symbols = TokenFactory(self._lexer.symbols)
        self._engine = engine
        self._definitions = environment
        self._filters = {r"\input": self._process_input,
                         r"\def": self._process_definition,
                         r"\begin": self._process_environment}

    def _spawn(self, tokens=None):
        parser = Parser(self._lexer, self._engine, self._definitions)
        if tokens:
            parser._tokens = Stream(iter(tokens))
        return parser

    def rewrite(self, tokens):
        result = []
        self._tokens = Stream(iter(tokens))
        while self._next_token is not None:
            result += self._rewrite_one()
        return result

    def _rewrite_one(self):
        self._abort_on_end_of_text()
        if self._next_token.begins_a_group:
            return self._capture_group()
        elif self._next_token.is_a_command:
            return self._evaluate_one()
        else:
            return [self._tokens.take()]

    @property
    def _next_token(self):
        return self._tokens.look_ahead()

    def default(self, text):
        return [self._tokens.take()]

    def define_macro(self, name, signature, replacement):
        self._definitions[name] = Macro(name, signature, replacement)
        return []

    def evaluate_macro(self, macro, signature, body):
        self._accept(self._symbols.command(macro))
        self._evaluate_arguments(signature)
        return self._spawn(body)._evaluate_group()

    def _accept(self, expected_token):
        if self._next_token != expected_token:
            raise ValueError("Expecting %s but found %s" % (expected_token, self._next_token))
        else:
            return self._tokens.take()

    def evaluate_parameter(self, parameter):
        self._tokens.take()
        return self._definitions[parameter]

    def _evaluate_arguments(self, signature):
        for index, any_token in enumerate(signature):
            if any_token.is_a_parameter:
                parameter = str(any_token)
                if index == len(signature)-1:
                    self._definitions[parameter] = self._evaluate_one()
                else:
                    next_token = signature[index + 1]
                    self._definitions[parameter] = self._evaluate_until(next_token)
            else:
                self._accept(any_token)

    def _evaluate_one(self):
        self._abort_on_end_of_text()
        if self._next_token.begins_a_group:
            return self._evaluate_group()
        elif self._next_token.is_a_command:
            return self.evaluate_command(str(self._next_token))
        elif self._next_token.is_a_parameter:
            return self._definitions[str(self._tokens.take())]
        else:
            return [self._tokens.take()]

    def _evaluate_group(self):
        self._accept(self._symbols.begin_group())
        tokens = self._evaluate_until(self._symbols.end_group())
        self._accept(self._symbols.end_group())
        return tokens

    def _evaluate_until(self, end_marker):
        result = []
        while self._next_token != end_marker:
            result += self._evaluate_one()
        return result

    def _abort_on_end_of_text(self):
        if not self._next_token:
            raise ValueError("Unexpected end of text!")

    def evaluate_command(self, command):
        if command in self._definitions:
            macro = self._definitions[command]
            return macro.parse_with(self)
        elif command in self._filters:
            return self._filters[command]()
        else:
            return self.default(command)

    def _process_input(self):
        self._tokens.take()  # the command name
        self._tokens.take_while(lambda c: c.is_a_whitespace)
        argument = self._evaluate_one()
        file_name = self._as_text(argument)
        content = self._engine.content_of(file_name)
        return [self._symbols.character(content)]

    @staticmethod
    def _as_text(tokens):
        return "".join(str(each) for each in tokens)

    def _process_definition(self):
        self._tokens.take()
        name = self._tokens.take()
        signature = self._tokens.take_while(lambda t: not t.begins_a_group)
        body = self._capture_group()
        return self.define_macro(str(name), signature, body)

    def _process_environment(self):
        begin = self._tokens.take()
        environment = self._capture_group()
        if self._as_text(environment) == "{verbatim}":
            return [begin] + environment + self._capture_until(self._tokenise("\end{verbatim}"))
        else:
            return [begin] + environment

    def _tokenise(self, text):
        return \
            [self._symbols.command("\end"), self._symbols.begin_group()] + \
            [self._symbols.character(each) for each in "verbatim"] + \
            [self._symbols.end_group()]

    def _capture_until(self, expected_tokens):
        read = []
        while self._next_token:
            read.append(self._tokens.take())
            if read[-len(expected_tokens):] == expected_tokens:
                break
        return read

    def _capture_group(self):
        tokens = [self._accept(self._symbols.begin_group())]
        while not self._tokens.look_ahead().ends_a_group:
            tokens += self._capture_one()
        tokens.append(self._accept(self._symbols.end_group()))
        return tokens

    def _capture_one(self):
        self._abort_on_end_of_text()
        if self._next_token.begins_a_group:
            return self._capture_group()
        else:
            return [self._tokens.take()]
