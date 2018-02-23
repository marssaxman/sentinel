import librosa
import numpy as np


# This decorator turns a function into a lazily evaluated, memoized property,
# where the function is invoked on first access, then replaced with its result.
class lazy_property(object):
	def __init__(self, function):
		# Save the function and its name.
		self.function = function
		self.name = function.__name__
	def __get__(self, obj, cls):
		if obj is None: return None
		# Evaluate the function, passing in 'obj', which will become 'self'
		# while the function is evaluating.
		value = self.function(obj)
		# Replace this property with the value we just generated, so that
		# the decorator instance disappears and it becomes a normal attribute.
		setattr(obj, self.name, value)
		return value


# A signal is a series of samples; a one-dimensional array with a frequency
# attribute, expressing the interval between samples.
class Signal(np.ndarray):
	def __new__(subtype, samples, frequency):
		# Create a view for the existing array using our new subtype.
		obj = np.asarray(samples).view(subtype)
		# Add the frequency attribute, which defines the timeline.
		obj.frequency = frequency
		return obj
	def __array_finalize__(self, obj):
		# self has been created by view casting or template construction.
		# if there is an obj, copy its metadata; otherwise, we are still in
		# the ndarray constructor, so we need to wait.
		if obj is None: return
		self.frequency = getattr(obj, 'frequency', None)

	@lazy_property
	def maxmag(self):
		# Magnitude of the maximum sample value
		return np.max(np.abs(self))

	@lazy_property
	def rms(self):
		# Root mean square power estimation.
		return np.sqrt(np.mean(self ** 2.0))

	@lazy_property
	def duration(self):
		# The size, measured in seconds.
		return float(len(self)) / self.frequency


# A track is an audio object collected with its metadata. It begins with a
# buffer, which may have been loaded from a file, and stores the frames, stats,
# histograms, and other information later calculated around it.
class Track:
	def __init__(self, path):
		self.path = path
		signal = Signal(*librosa.load(path, sr=44100, mono=False))
		# Most of the analysis and display code really only wants a single
		# channel, so we'll bounce this down to mono if necessary, keeping the
		# original around so we can apply edits later.
		if signal.ndim > 1:
			self.original = signal
			signal = librosa.to_mono(signal)
		self.signal = signal
