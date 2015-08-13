import os
import re
from flap.path import Path


class Listener:
    """
    Handle events emitted by FLaP.
    """
    
    def onInput(self, inputedFile):
        """
        Triggered when an input directive was found in the LaTeX source.
        """
        pass
    
    def onFlattenComplete(self):
        """
        Triggered when the flattening process is complete.
        """
        pass
    


class Flap:
    """
    The Flap engine. Does the flattening of LaTeX projects, including merging
    included files, moving graphics and resources files such as classes, styles 
    and bibliography 
    """

    INPUT_PATTERN = re.compile("\\input{([^}]+)}")
    INCLUDE_GRAPHICS = re.compile("\\includegraphics(?:\[[^\]]+\])*\{([^\}]+)\}")


    def __init__(self, fileSystem, listener = Listener()):
        self.fileSystem = fileSystem
        self.listener = listener


    def openFile(self, source):
        file = self.fileSystem.open(source)
        if file.isMissing():
            raise ValueError("The file '%s' could not be found." % source)
        return file


    def appendPrefix(self, text, fragments, current, match):
        return fragments.append(text[current:match.start() - 1])


    def appendFile(self, current, fragments, reference):
        includedFile = current.sibling(reference)
        if includedFile.isMissing():
            raise ValueError("The file '%s' could not be found." % includedFile.path())
        fragments.extend(self.flattenInputDirectives(includedFile))


    def appendSuffix(self, text, fragments, current):
        return fragments.append(text[current:len(text)])


    def flattenInputDirectives(self, file):
        text = file.content() 
        lines = text.splitlines(True)
        fragments = []
        for eachLine in lines:
            if not self.isCommentedOut(eachLine):
                current = 0
                for match in Flap.INPUT_PATTERN.finditer(eachLine):
                    self.listener.onInput(match.group(1))
                    self.appendPrefix(eachLine, fragments, current, match)
                    self.appendFile(file, fragments, "%s.tex" % match.group(1))
                    current = match.end()
                self.appendSuffix(eachLine, fragments, current)

            else:
                fragments.append(eachLine)
        
        return fragments


    def isCommentedOut(self, text):
        return text.strip().startswith("%")

    def merge(self, fragments):
        mergedContent = ''.join(fragments)
        return mergedContent


    def appendIncludeGraphics(self, root, outputDirectory, results, match):
        path = Path.fromText(match.group(1))
        graphics = root.container().filesThatMatches(path)
        if not graphics:
            raise ValueError("Unable to find file for graphic '%s' in '%s'" % (match.group(1), root.container().path()))
        
        else:
            graphic = graphics[0]
            self.fileSystem.copy(graphic, outputDirectory)
            graphicInclusion = match.group(0).replace(match.group(1), graphic.basename())
            results.append("\\" + graphicInclusion)


    def adjustIncludeGraphics(self, root, outputDirectory, fragments):
        results = []
        for eachFragment in fragments:
            current = 0
            for match in Flap.INCLUDE_GRAPHICS.finditer(eachFragment):
                self.appendPrefix(eachFragment, results, current, match)
                self.appendIncludeGraphics(root, outputDirectory, results, match)
                current = match.end()
            self.appendSuffix(eachFragment, results, current)
        return results


    RESOURCE_FILES = ["cls", "sty", "bib", "bst"]
    
    
    def copyResourceFiles(self, outputDirectory, root):
        project = root.container()
        for eachFile in project.files():
            if eachFile.hasExtension() and eachFile.extension() in Flap.RESOURCE_FILES:
                self.fileSystem.copy(eachFile, outputDirectory)
            
            
    def flatten(self, source, outputDirectory):
        root = self.openFile(source)
        self.copyResourceFiles(outputDirectory, root)
        fragments = self.flattenInputDirectives(root)        
        fragments = self.adjustIncludeGraphics(root, outputDirectory, fragments)
        result = self.merge(fragments)
        self.fileSystem.createFile(outputDirectory / "merged.tex", result)
        self.listener.onFlattenComplete()


