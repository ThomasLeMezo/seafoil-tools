
from PyQt5.QtWidgets import QApplication
import sys
from log_analyzer.seafoil_log_analyzer import SeafoilLogAnalyser

## Start Qt event loop unless running in interactive mode or using pyside.
if __name__ == '__main__':
    app = QApplication(sys.argv)
    if len(sys.argv)>1:
        filename = []
        for i in range(1, len(sys.argv)):
            # Add to filename list
            filename.append(sys.argv[i])
        print("filenames = ", filename)

        # offset_date = None
        # if len(sys.argv)>2:
        #     import datetime
        #     offset_date = datetime.datetime.strptime(sys.argv[2], "%Y-%m-%dT%H:%M:%S")

        sla = SeafoilLogAnalyser(filename, None)
        sys.exit(app.exec_())
    else:
        print("Usage: seafoil_log <folderpath/filename> [offset_date]")
        print("  filename: path to the rosbag folder or the .gpx file")
        print("  offset_date: optional, offset date to start the log")
        print("  example: seafoil_log /path/to/rosbag 2021-01-01T00:00:00")