import sys

import numpy as np
import argparse
import os

from PyQt5 import QtWidgets

from log_analyzer.seafoil_bag import SeafoilBag
from log_analyzer.tools.seafoil_heading_computation import SeafoilHeadingComputation

# Test of the SeafoilHeadingComputation class
if __name__ == "__main__":
    # Create window
    app = QtWidgets.QApplication(sys.argv)
    # Create a QMainWindow
    window = QtWidgets.QMainWindow()

    # Get the current working directory
    cwd = os.getcwd()
    # Get the input arguments
    parser = argparse.ArgumentParser(description='Compute heading from a Seafoil bag file')
    parser.add_argument('seafoil_bag', type=str, help='Seafoil bag file')
    args = parser.parse_args()

    # open a seafoil bag
    seafoil_bag = SeafoilBag(args.seafoil_bag)
    seafoil_bag.load_data()

    seafoil_heading_computation = SeafoilHeadingComputation(seafoil_bag, window)
    window.show()
    sys.exit(app.exec_())