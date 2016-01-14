''' Container for all solvers. '''

import os
import sys

# Make sure this module is on the path regardless of where its imported from.
_myDir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(_myDir)

# Grab all our submodules and include them whenever we include this package:
__all__ = [x.replace('.py', '') for x in os.listdir(_myDir)
           if x[0] not in ['.', '_']]

# Import of all the sub-modules:
for name in __all__:
    exec('import ' + name)
