
import math
import numpy as np
from scipy import interpolate
import pyqtgraph as pg

class SeafoilRelationshipPlot:

    def __init__(self, data_x, data_y, data_x_time, data_y_time, sfb, enable_interpolation=True):
        self.data_x = data_x
        self.data_y = data_y
        self.data_x_time = data_x_time
        self.data_y_time = data_y_time

        self.time_min_idx = 0
        self.time_max_idx = len(data_x_time)
        self.enable_interpolation = True
        self.sfb = sfb

        self.name_x = None
        self.name_y = None
        self.unit_x = None
        self.unit_y = None

        self.x_min = np.min(data_x)
        self.x_max = np.max(data_x)
        self.x_resolution = 1.0
        self.x_unit_conversion = 1.0

        self.y_min = np.min(data_y)
        self.y_max = np.max(data_y)
        self.y_resolution = 1.0
        self.y_unit_conversion = 1.0

        self.min_sample = 5
        self.normalize = "max"

        self.enable_polyfit = False
        self.polyndegree = 1

        self.enable_plot_stat_curves = True
        self.enable_plot_trajectory = False
        self.modulo_x = False

        # Processed data
        self.x_vect = None
        self.y_stat_mean = None
        self.y_stat_max = None
        self.y_stat_min = None
        self.y_hist = None

        self.y_hist_modulo = None
        self.x_vect_modulo = None

        self.x_polyfit = None
        self.x_vect_fit = None

        self.x_center_value = 0

        # Plot references
        self.pg_plot = None
        self.pcmi = None
        self.plot_min = None
        self.plot_max = None
        self.plot_mean = None
        self.plot_polyfit = None
        self.plot_taj = None
        self.color_matrix_list = [(0, 0, 255, 100), (0, 255, 0, 100), (255, 0, 0, 100), (255, 255, 0, 100), (255, 0, 255, 100), (0, 255, 255, 100)]
        self.color_matrix_idx = 0

        # Tools
        self.spinbox = None

    def get_color_matrix(self):
        return self.color_matrix_list[self.color_matrix_idx]

    def set_x_parameters(self, name_x, unit_x, x_min, x_max, x_resolution=1.0, x_unit_conversion=1.0):
        self.name_x = name_x
        self.unit_x = unit_x
        self.x_resolution = x_resolution
        self.x_unit_conversion = x_unit_conversion
        self.x_min = x_min / x_unit_conversion
        self.x_max = x_max / x_unit_conversion

    def set_y_parameters(self, name_x, unit_x, y_min, y_max, y_resolution=1.0, y_unit_conversion=1.0):
        self.name_y = name_x
        self.unit_y = unit_x
        self.y_resolution = y_resolution
        self.y_unit_conversion = y_unit_conversion
        self.y_min = y_min / y_unit_conversion
        self.y_max = y_max / y_unit_conversion

    def set_min_sample(self, min_sample=5, normalize="max"):
        self.min_sample = min_sample
        self.normalize = normalize

    def enable_polyfit(self, polyndegree=1):
        self.enable_polyfit = True
        self.polyndegree = polyndegree

    def plot_options(self, enable_plot_stat_curves=False, enable_plot_trajectory=False, modulo_x=False):
        self.enable_plot_stat_curves = enable_plot_stat_curves
        self.enable_plot_trajectory = enable_plot_trajectory
        self.modulo_x = modulo_x

    def preprocess_data(self):
        # Remove duplicate time values (mostly for gpx data)
        self.data_y_time, idx = np.unique(self.data_y_time, return_index=True)
        self.data_y = self.data_y[idx]

        if self.enable_interpolation:
            f_y = interpolate.interp1d(self.data_y_time, self.data_y, bounds_error=False, kind="zero")
            self.data_y = f_y(self.data_x_time)

        self.x_vect = np.arange(self.x_min, self.x_max, self.x_resolution)

    def compute_histogram(self):
        # y stats
        self.y_stat_mean = np.zeros(len(self.x_vect))
        self.y_stat_max = np.zeros(len(self.x_vect))
        self.y_stat_min = np.zeros(len(self.x_vect))
        self.y_hist = np.zeros([len(self.x_vect), int((self.y_max - self.y_min) / self.y_resolution)])

        # Select time interval
        data_x = self.data_x[self.time_min_idx:self.time_max_idx]
        data_y = self.data_y[self.time_min_idx:self.time_max_idx]

        for i, x in enumerate(self.x_vect):
            idx = np.where((data_x >= x) & (data_x < (x + self.x_resolution))) # .data ??
            if len(idx[0]) > self.min_sample:
                y_data = np.sort(data_y[idx])
                self.y_stat_mean[i] = np.mean(y_data)
                self.y_stat_max[i] = np.mean(y_data[int(len(y_data) * 0.9):])
                self.y_stat_min[i] = np.mean(y_data[:int(len(y_data) * 0.1)])

                # Get histogram of y
                for y_val in y_data[np.where((y_data >= self.y_min) & (y_data < self.y_max))]:
                    idx_y = math.floor((y_val - self.y_min) / (self.y_max - self.y_min) * len(self.y_hist[0]))
                    if len(self.y_hist[0]) > idx_y >= 0:
                        self.y_hist[i, idx_y] += 1

                # Normalize histogram
                if self.normalize == "max":
                    max_hist = np.max(self.y_hist[i])
                    if max_hist > 0:
                        self.y_hist[i] = self.y_hist[i] / max_hist
                elif self.normalize == "one":
                    self.y_hist[i] = self.y_hist[i] > 0

    def compute_polyfit(self):
        # Add a polynomial fit to y_mean
        if self.enable_polyfit:
            x_vect_fit = None
            x_polyfit = None

            try:
                last_idx = np.where(self.y_stat_mean > 0)[0][-1]
                x_vect_fit = self.x_vect[:last_idx]
                z = np.polyfit(x_vect_fit, self.y_stat_mean[:last_idx], self.polyndegree)
                x_polyfit = np.poly1d(z)
            except Exception as e:
                print("Oops!  error ", e)
                self.enable_polyfit = False

    def generate_pcmi(self):
        if self.pcmi is None:
            colormap = pg.ColorMap(pos=[0., 1.0],
                                   color=[(0, 0, 255, 0), self.get_color_matrix()],
                                   mapping=pg.ColorMap.CLIP)
            self.pcmi = pg.PColorMeshItem(edgecolors=None, antialiasing=False, colorMap=colormap)

        idx_center = np.where(self.x_vect >= self.x_center_value)[0][0]

        # put the subarray of y_hist in the right order
        self.y_hist_modulo = np.concatenate((self.y_hist[idx_center:], self.y_hist[:idx_center]), axis=0)
        half_range = (self.x_max - self.x_min)/2
        self.x_vect_modulo = np.arange(-half_range, half_range, self.x_resolution)

        x_pcmi = np.outer((self.x_vect_modulo + self.x_resolution) * self.x_unit_conversion, np.ones(int((self.y_max-self.y_min) / self.y_resolution)))
        y_pcmi = np.outer(np.ones(len(self.x_vect_modulo)), np.arange(self.y_min, self.y_max, self.y_resolution)[:-1] * self.y_unit_conversion)
        self.pcmi.setData(x_pcmi, y_pcmi, self.y_hist_modulo[:-1,:-1])

    def generate_plots(self):
        was_first_time = False
        if self.pg_plot is None:
            self.pg_plot = pg.PlotWidget()
            self.pg_plot.addLegend()
            self.pg_plot.showGrid(x=True, y=True)
            self.pg_plot.setLabel('left', self.name_y + " (" + self.unit_y + ")")
            was_first_time = True

        if self.enable_plot_stat_curves:
            if self.enable_polyfit:
                if self.plot_polyfit is None:
                    self.plot_polyfit = self.pg_plot.plot(self.x_vect_fit * self.x_unit_conversion, self.x_polyfit(self.x_vect_fit)[:-1] * self.y_unit_conversion, pen=(0, 255, 255), name="polyfit", stepMode=True)
                else:
                    self.plot_polyfit.setData(self.x_vect_fit * self.x_unit_conversion, self.x_polyfit(self.x_vect_fit)[:-1] * self.y_unit_conversion)
            if self.plot_mean is None:
                self.plot_mean = self.pg_plot.plot(self.x_vect * self.x_unit_conversion, self.y_stat_mean[:-1] * self.y_unit_conversion, pen=pg.mkPen((255, 0, 0), width=5), name=self.name_y + " mean", stepMode=True)
                self.plot_max = self.pg_plot.plot(self.x_vect * self.x_unit_conversion, self.y_stat_max[:-1] * self.y_unit_conversion, pen=(0, 255, 0), name=self.name_y + " max (10%)", stepMode=True)
                self.plot_min = self.pg_plot.plot(self.x_vect * self.x_unit_conversion, self.y_stat_min[:-1] * self.y_unit_conversion, pen=(0, 0, 255), name=self.name_y + " min (10%)", stepMode=True)
            else:
                self.plot_mean.setData(self.x_vect * self.x_unit_conversion, self.y_stat_mean[:-1] * self.y_unit_conversion)
                self.plot_max.setData(self.x_vect * self.x_unit_conversion, self.y_stat_max[:-1] * self.y_unit_conversion)
                self.plot_min.setData(self.x_vect * self.x_unit_conversion, self.y_stat_min[:-1] * self.y_unit_conversion)

        if was_first_time:
            self.pg_plot.addItem(self.pcmi)


        if self.enable_plot_trajectory:
            # Select index where the speed is greater than x_min
            idx = np.where(self.data_x[self.time_min_idx:self.time_max_idx] > self.x_min)
            data_x_modulo = (self.data_x[self.time_min_idx:self.time_max_idx][idx] - self.x_center_value) % (self.x_max - self.x_min) - (self.x_max - self.x_min) / 2.

            if self.plot_taj is None:
                cm = pg.colormap.get('summer', source='matplotlib')  # prepare a linear color map
                pen = cm.getPen(span=(self.y_min*self.y_unit_conversion, self.y_max*self.y_unit_conversion))  # gradient from blue (y=0) to white (y=1)
                self.plot_taj = self.pg_plot.plot(data_x_modulo*self.x_unit_conversion,
                                                  self.data_y[self.time_min_idx:self.time_max_idx][idx]*self.y_unit_conversion,
                                                  pen=pen, #(255, 0, 0),
                                                  name=self.name_y,
                                                  stepMode=False)

                # set the plot as invisible
                self.plot_taj.setVisible(False)

            else:
                self.plot_taj.setData(data_x_modulo*self.x_unit_conversion, self.data_y[self.time_min_idx:self.time_max_idx][idx]*self.y_unit_conversion)

    def update_time(self, time_interval):
        # find the index of the time interval
        self.time_min_idx = np.where(self.data_x_time >= time_interval[0])[0][0]
        self.time_max_idx = np.where(self.data_x_time <= time_interval[1])[0][-1]
        self.compute_histogram()
        self.generate_pcmi()
        self.generate_plots()

    def update_x_center(self):
        self.x_center_value = ((self.spinbox.value() / self.x_unit_conversion + (self.x_max - self.x_min) / 2.) % (self.x_max - self.x_min))
        self.generate_pcmi()
        self.generate_plots()

        # Find the max value of the histogram
        # Find the indices of all '1's in the matrix (transposed)
        # Get the first last of '1' by row, which is closest to the top ([-1])
        # Get the column ([1])
        try:
            max_hist_positive = (np.argwhere(np.transpose(self.y_hist_modulo[self.x_vect_modulo >= 0]))[-1][1]+1)*self.x_resolution
            max_hist_negative = 180 - (np.argwhere(np.transpose(self.y_hist_modulo[self.x_vect_modulo < 0]))[-1][1]+1)*self.x_resolution

            max_hist_positive_value = (np.argwhere(np.transpose(self.y_hist_modulo[self.x_vect_modulo >= 0]))[-1][0])*self.y_resolution + self.y_min
            max_hist_negative_value = (np.argwhere(np.transpose(self.y_hist_modulo[self.x_vect_modulo < 0]))[-1][0])*self.y_resolution + self.y_min

            # Add in the legend the max value of the histogram (round to 2 decimals
            self.pg_plot.setTitle(f"Max left: {max_hist_negative*self.x_unit_conversion} [{max_hist_negative_value*self.y_unit_conversion:.2f} kt] "
                             f"Max right: {max_hist_positive*self.x_unit_conversion} [{max_hist_positive_value*self.y_unit_conversion:.2f} kt]")
        except Exception as e:
            self.pg_plot.setTitle("Max left: (error) Max right: (error) " + str(e))

        self.sfb.configuration["analysis"]["wind_heading"] = float(self.spinbox.value())

    def generate_plot_relationship(self):

        # Example : x = data_gnss.speed, y = data_height.height, name_x = "speed", name_y = "height"
        # Example : x = data_gnss.track, y = data_gnss.speed, name_x = "track", name_y = "speed"

        self.preprocess_data()
        self.compute_histogram()

        # 2D matrix
        self.generate_pcmi()

        # Plot
        self.generate_plots()

        if self.modulo_x:
            # Add a spin box to change the center value of the x axis
            self.spinbox = pg.SpinBox(value=self.x_min*self.x_unit_conversion,
                                 bounds=[self.x_min*self.x_unit_conversion, self.x_max*self.x_unit_conversion],
                                 step=self.x_resolution*self.x_unit_conversion)
            self.spinbox.setValue(int(self.sfb.configuration["analysis"]["wind_heading"]))
            # Set wrap to True to allow the value to wrap around the limits
            self.spinbox.setWrapping(True)

            self.spinbox.sigValueChanged.connect(self.update_x_center)
            self.update_x_center()

        if self.spinbox is not None:
            return self.pg_plot, self.spinbox
        else:
            return self.pg_plot