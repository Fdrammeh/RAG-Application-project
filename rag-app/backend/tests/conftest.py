import os
import sys

# Put the backend directory (parent of tests/) on the import path
# so `from main import app` works when pytest runs from any location.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))