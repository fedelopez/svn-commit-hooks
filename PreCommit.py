import re
import sys
from StdOutCapture import StdOutCapture
from SvnLookCatCommand import SvnLookCatCommand
from SvnLookChangedCommand import SvnLookChangedCommand

PAUSE_IN_JAVA_FILE_MSG = 'File contains: a pause or stop: '
ILLEGAL_IMPORT_MSG = 'File contains: an illegal import statement: '
INTELLIJ_FORM_WITH_INVALID_REFERENCE_MSG = 'IntelliJ form references to a resource bundle: '
SOLO_TEST_MSG = 'File contains solo test, solo group, ddescribe, or iit: '

__author__ = 'Fede Lopez'

class PreCommit():
    def __init__(self, repositoryPath, transaction):
        self.repositoryPath = repositoryPath
        self.transaction = transaction

    def pauseInCommentedLine(self, line):
        return re.search(r"//.+\b(TestSetup|TestBase)\.\bpause\(\)", line) is not None

    def pauseInCommentedBlock(self, line):
        return re.search(r"/\*.+\b(TestSetup|TestBase)\.\bpause\(\).+\*/", line) is not None

    def pauseInLine(self, line):
        pauseInstruction = ('TestSetup.pause()', 'TestBase.pause()', 'Waiting.stop()')
        for instruction in pauseInstruction:
            if instruction in line:
                return True
        return False

    def hasSoloTestInLine(self, line):
        soloInstruction = ('solo_test', 'solo_group', 'ddescribe', 'iit(')
        for instruction in soloInstruction:
            if instruction in line:
                return True
        return False

    def hasPause(self, line):
        if self.pauseInLine(line):
            if self.pauseInCommentedLine(line):
                return False
            if self.pauseInCommentedBlock(line):
                return False
            return True
        return False

    def hasIllegalImportStatement(self, line):
        return re.search(r"com\.sun\.istack\.internal", line) is not None

    def intelliJFormHasInvalidReference(self, line):
        return re.search(r"resource-bundle=\".+key=\"\w*\"", line) is not None

    def checkFile(self, fileAsString):
        for lineOfCode in fileAsString:
            if self.hasPause(lineOfCode):
                return PAUSE_IN_JAVA_FILE_MSG
            if self.hasSoloTestInLine(lineOfCode):
                return SOLO_TEST_MSG
            if self.hasIllegalImportStatement(lineOfCode):
                return ILLEGAL_IMPORT_MSG
            if self.intelliJFormHasInvalidReference(lineOfCode):
                return INTELLIJ_FORM_WITH_INVALID_REFERENCE_MSG
        return None

    def main(self):
        exitCode = 0
        svnCommand = SvnLookChangedCommand(self.repositoryPath, self.transaction)
        stdOutCapture = StdOutCapture(svnCommand.command())
        changedFiles = stdOutCapture.linesFromStdOut()
        for changedFile in changedFiles:
            svnLookCatCommand = SvnLookCatCommand(self.repositoryPath, self.transaction, changedFile)
            cmd = svnLookCatCommand.command()
            if cmd is not None:
                stdOutCapture = StdOutCapture(cmd)
                lines = stdOutCapture.linesFromStdOut()
                result = self.checkFile(lines)
                if result is not None:
                    sys.stderr.write("\n" + result + svnLookCatCommand.filePath)
                    exitCode = -1
        return exitCode

if __name__ == '__main__':
    preCommit = PreCommit(sys.argv[1], sys.argv[2])
    sys.exit(preCommit.main())