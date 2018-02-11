
import Tkinter as tk
import matplotlib
matplotlib.use('TkAgg')
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np

class Editview(tk.Frame):
	def __init__(self, container, signal, **kwargs):
		self._signal = signal
		self._view_interval = (0,1)
		self._redraw_waiting = False
		tk.Frame.__init__(self, container, **kwargs)
		self._figure = matplotlib.figure.Figure(figsize=(6,1), dpi=100)
		self._axes = self._figure.add_axes([0,0,1,1])
		self._axes.get_xaxis().set_visible(False)
		self._axes.get_yaxis().set_visible(False)
		self._canvas = FigureCanvasTkAgg(self._figure, master=self)
		self._canvas.show()
		widget = self._canvas.get_tk_widget()
		widget.pack(fill=tk.BOTH, expand=True)
		self.bind('<Configure>', self.on_resize)
		self._draw()

	def on_resize(self, event):
		self._draw()

	def view(self, interval):
		# Display the slice of the signal specified by the fractional interval.
		# Limit the interval to some reasonable scale for our signal length.
		minlength = 32.0 / float(len(self._signal.mono))
		begin, end = interval
		length = max(minlength, end - begin)
		pos = (begin + end) / 2.0
		begin = max(0, pos - length / 2.0)
		end = min(1.0, begin + length)
		self._view_interval = (begin, end)
		self._draw()

	def _draw(self):
		if not self._redraw_waiting:
			self._redraw_waiting = True
			self.after(100, self._plot)

	def _plot(self):
		self._redraw_waiting = False
		self._axes.clear()
		resolution = self.winfo_width()
		samples = self._signal.mono
		begin, end = self._view_interval
		# Slice the interval down to the sample array we are interested in.
		samples = samples[int(begin * len(samples)):int(end * len(samples))]
		# Set the axis limits, since we just cleared them.
		self._axes.set_ylim(-1, 1)
		self._axes.set_xlim(0, len(samples))
		# Draw a faint origin line across the horizontal axis.
		self._axes.axhline(0, color='lightgray', zorder=0)
		if len(samples) > resolution:
			self._plot_bins(samples, resolution)
		if len(samples) * 4 < resolution:
			self._plot_points(samples, resolution)
		else:
			self._plot_line(samples, resolution)
		self._canvas.draw()

	def _plot_bins(self, samples, resolution):
		# Matplotlib would choke if it tried to draw the entire sample array,
		# so we'll slice it up with one bin per pixel, find the min and max
		# values in each bin, then plot a vertical line between them. 
		splits = np.array_split(samples, resolution)
		mins = [x.min() for x in splits]
		maxes = [x.max() for x in splits]
		ticks = [len(x) for x in splits]
		self._axes.fill_between(ticks, mins, maxes, lw=0.0, edgecolor=None)

	def _plot_points(self, samples, resolution):
		# Our points are getting spaced pretty far apart, so we'll mark each
		# sample value and interpolate a smooth curve between them.
		ticks = np.arange(len(samples))
		filltime = np.linspace(ticks[0], ticks[-1], resolution)
		stineman = matplotlib.mlab.stineman_interp
		interp = stineman(filltime, ticks, samples, None)
		self._axes.plot(ticks, samples, '.', filltime, interp)

	def _plot_line(self, samples, resolution):
		# We have a reasonable number of samples, so draw an ordinary waveform.
		self._axes.plot(np.arange(len(samples)), samples, lw=0.5)

