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

from unittest import TestCase
from mock import MagicMock

from flap.FileSystem import InMemoryFileSystem
from flap.path import Path
from tests.acceptance.engine import TexFile, FlapTestCase, LatexProject, FileBasedTestRepository, YamlCodec


class TexFileTest(TestCase):

    def setUp(self):
        self.path = "test/main.tex"
        self.content = "foo"
        self.tex_file = TexFile(self.path, self.content)

    def test_name_is_exposed(self):
        self.assertEqual(self.path, self.tex_file.path)

    def test_content_is_exposed(self):
        self.assertEquals(self.content, self.tex_file.content)

    def test_equals_itself(self):
        self.assertEqual(self.tex_file, self.tex_file)

    def test_equals_a_similar_file(self):
        self.assertEqual(TexFile("test/main.tex", "foo"),
                         self.tex_file)

    def test_does_not_equals_tex_file_with_a_different_path(self):
        self.assertNotEqual(TexFile("dir/" + self.path, self.content),
                            self.tex_file)

    def test_does_not_equals_tex_file_with_a_different_content(self):
        self.assertNotEqual(TexFile(self.path, self.content + "blablabla"),
                            self.tex_file)


class LatexProjectTests(TestCase):

    def setUp(self):
        self.files = [ TexFile("main.tex", "blabla") ]
        self.tex = LatexProject(self.files)

    def test_files_is_exposed(self):
        self.assertEquals(self.files[0], self.tex.files["main.tex"])

    def test_equals_a_project_with_similar_files(self):
        self.assertEqual(LatexProject([TexFile("main.tex", "blabla")]),
                         self.tex)

    def test_differ_when_file_content_differ(self):
        self.assertNotEqual(LatexProject([TexFile("main.tex", "THIS IS DIFFERENT!")]),
                         self.tex)

    def test_differ_when_file_path_differ(self):
        self.assertNotEqual(LatexProject([TexFile("a/different/path.tex", "blabla")]),
                         self.tex)


class FlapTestCaseTests(TestCase):

    def setUp(self):
        self.project = LatexProject([TexFile("main.tex", "blabla")])
        self.expected = LatexProject([TexFile("main.tex", "blabla")])
        self.test_case_name = "foo"
        self.test_case = FlapTestCase(self.test_case_name, self.project, self.expected)

    def test_name_is_exposed(self):
        self.assertEqual(self.test_case_name, self.test_case.name)

    def test_reject_empty_names(self):
        with self.assertRaises(ValueError):
            FlapTestCase("", self.project, self.expected)

    def test_project_is_exposed(self):
        self.assertIs(self.project, self.test_case.project)

    def test_expectation_is_exposed(self):
        self.assertIs(self.expected, self.test_case.expected)

    def test_equals_itself(self):
        self.assertEquals(self.test_case, self.test_case)

    def test_equals_a_similar_test_case(self):
        self.assertEqual(FlapTestCase(
            "foo",
            LatexProject([TexFile("main.tex", "blabla")]),
            LatexProject([TexFile("main.tex", "blabla")])
        ),
        self.test_case)

    def test_differs_from_a_project_with_another_expectation(self):
        self.assertNotEqual(FlapTestCase(
            "foo",
            LatexProject([TexFile("main.tex", "blabla")]),
            LatexProject([TexFile("main.tex", "something different")])
        ),
        self.test_case)


class TestYamlCodec(TestCase):

    def setUp(self):
        self._codec = YamlCodec()

    def test_loading_a_simple_yaml_test_case(self):
        file = MagicMock()
        file.content.return_value = ("name: test 1\n"
                                     "project:\n"
                                     "  - path: main.tex\n"
                                     "    content: |\n"
                                     "      blabla\n"
                                     "expected:\n"
                                     "  - path: main.tex\n"
                                     "    content: |\n"
                                     "      blabla\n")

        test_case = self._read_test_case_from(file)

        expected = FlapTestCase(
                        "test 1",
                        LatexProject([TexFile("main.tex", "blabla")]),
                        LatexProject([TexFile("main.tex", "blabla")]))

        self.assertEqual(expected, test_case)

    def test_loading_test_case_with_latex_code(self):
        file = MagicMock()
        file.content.return_value = ("name: test 1\n"
                                     "project:\n"
                                     "  - path: main.tex\n"
                                     "    content: |\n"
                                     "      \\begin{document}Awesone!\\end{document}\n"
                                     "expected:\n"
                                     "  - path: main.tex\n"
                                     "    content: |\n"
                                     "      \\begin{document}Awesone!\\end{document}\n")

        test_case = self._read_test_case_from(file)

        expected = FlapTestCase(
                        "test 1",
                        LatexProject([TexFile("main.tex", "\\begin{document}Awesone!\\end{document}")]),
                        LatexProject([TexFile("main.tex", "\\begin{document}Awesone!\\end{document}")]))

        self.assertEqual(expected, test_case)

    def _read_test_case_from(self, file):
        return self._codec.extract_from(file)


class TestRepositoryTest(TestCase):

    def setUp(self):
        self.file_system = InMemoryFileSystem()
        self.repository = FileBasedTestRepository(
            self.file_system,
            Path.fromText("tests"),
            YamlCodec())

    def test_do_not_found_test_that_do_not_exist(self):
        test_cases = self._fetch_all_tests()
        self.assertEqual(0, len(test_cases))

    def test_found_one_test_if_only_one_yml_exists(self):
        self._create_file("tests/test.yml", self._dummy_yaml_test_case())
        test_cases = self.repository.fetch_all()
        self._verify(test_cases)

    def test_found_one_test_if_only_one_yaml_exists(self):
        self._create_file("tests/test.yaml", self._dummy_yaml_test_case())
        test_cases = self.repository.fetch_all()
        self._verify(test_cases)

    def test_ignore_files_that_are_not_yaml(self):
        self._create_file("tests/test.txt", self._dummy_yaml_test_case())
        test_cases = self._fetch_all_tests()
        self.assertEqual(0, len(test_cases))

    def test_spot_files_hidden_in_sub_directories(self):
        self._create_file("tests/sub_dir/test_2.yml", self._dummy_yaml_test_case())
        test_cases = self._fetch_all_tests()
        self._verify(test_cases)

    def _verify(self, test_cases):
        self.assertEqual(1, len(test_cases))
        expected = FlapTestCase(
            "test 1",
            LatexProject([TexFile("main.tex", ("\\documentclass{article}\n"
                                               "\\begin{document}\n"
                                               "  This is a simple \\LaTeX document!\n"
                                               "\\end{document}"))]),
            LatexProject([TexFile("main.tex", ("\\documentclass{article}\n"
                                               "\\begin{document}\n"
                                               "  This is a simple \\LaTeX document!\n"
                                               "\\end{document}"))])
        )
        self.assertEqual(expected, test_cases[0])

    def _dummy_yaml_test_case(self):
        return ( "name: test 1 \n"
                 "description: >\n"
                 "  This is a dummy test, for testing purposes\n"
                 "project:\n"
                 "  - path: main.tex\n"
                 "    content: |\n"
                 "      \\documentclass{article}\n"
                 "      \\begin{document}\n"
                 "        This is a simple \\LaTeX document!\n"
                 "      \\end{document}\n"
                 "expected:\n"
                 "  - path: main.tex\n"
                 "    content: |\n"
                 "      \\documentclass{article}\n"
                 "      \\begin{document}\n"
                 "        This is a simple \\LaTeX document!\n"
                 "      \\end{document}\n")

    def _fetch_all_tests(self):
        return self.repository.fetch_all()

    def _create_file(self, path, content):
        self.file_system.createFile(Path.fromText(path), content)
