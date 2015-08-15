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

import unittest

from flap.path import Path, ROOT

class PathTests(unittest.TestCase):


    def testRoot(self):
        path = ROOT
        self.assertTrue(path.isRoot())

        
    def testPathToFile(self):
        path = (ROOT / "test" / "source.tex")
        
        self.assertFalse(path.isRoot())
        self.assertEqual(path.container(), (ROOT / "test"))
        self.assertEqual(path.fullname(), "source.tex")


    def testHasExtension(self):
        path = ROOT / "source.tex"
        
        self.assertTrue(path.hasExtension())
    
        
    def testBasename(self):
        path = ROOT / "source.tex"
        
        self.assertEqual(path.basename(), "source")
  
        
    def testContainement(self):
        path1 = ROOT / "dir" / "file.txt"
        path2 = ROOT / "dir"

        self.assertTrue(path1 in path2)

        
    def testContainmentUnderEquality(self):
        path1 = ROOT / "dir" / "file.txt"
        path2 = ROOT / "dir" / "file.txt"
        
        self.assertFalse(path1 in path2)
        self.assertFalse(path2 in path1) 


    def testPathBuilding(self):
        path = Path.fromText("\\Users\\franckc\\file.txt")
        
        self.assertEqual(path, ROOT / "Users" / "franckc" / "file.txt")


    def testParts(self):
        path = Path.fromText("C:\\Users\\franckc\\pub\\JOCC\\main.tex")
        
        self.assertEqual(path.parts(), ["C:", "Users", "franckc", "pub", "JOCC", "main.tex"])


if __name__ == "__main__":
    unittest.main()