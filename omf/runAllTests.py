''' Walk the /omf/ directory, run _tests() in all modules. '''

import os
import sys
import subprocess

IGNORE_DIRS = ["data", ".git", "static", "templates", "uploads", "scratch"]
IGNORE_FILES = ["runAllTests.py"]  # to avoid infinite loop.


def runAllTests(startingdir):
    os.chdir(startingdir)
    nextdirs = []
    the_errors = 0
    misfires = {}
    for item in os.listdir("."):
        if item not in IGNORE_FILES and item.endswith(".py") and "def _tests():" in open(item).read():
            print "********** TESTING", item, "************"
            p = subprocess.Popen(["python", item], stderr=subprocess.PIPE)
            p.wait()
            if p.returncode:
                the_errors += 1
                misfires[os.path.join(os.getcwd(), item)] = p.stderr.read()
        elif os.path.isdir(item) and item not in IGNORE_DIRS:
            nextdirs.append(os.path.join(os.getcwd(), item))
    for d in nextdirs:
        e, m = runAllTests(d)
        the_errors += e
        misfires.update(m)
    return the_errors, misfires


def testRunner():
    # You can just run tests in a specific dir if you want
    os.chdir(sys.argv[1] if len(sys.argv) > 1 else ".")
    i, mis = runAllTests(os.getcwd())
    print "\n\n+------------------------+"
    print "\n\nTEST RESULTS"
    print "\n\n+------------------------+"
    print i, "tests failed:\n\n"
    for fname, err in mis.items():
        print fname
        print err, "\n\n"

if __name__ == "__main__":
    testRunner()
