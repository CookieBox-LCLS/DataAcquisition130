import win32com.client
import numpy as np
app = win32com.client.Dispatch("LeCroy.XStreamDSO")

#dataIsReadyForReadout returns boolean True or False 
def dataIsReadyForReadout():
	waveformReady = app.Acquisition.Acquire(1, False)
	return waveformReady

#read in data from channel 1
def readInDataFromScope_c1():
	#use with defult scaling argument of True.  the returned data is doubles (64 bit float) CHECK THIS FOR CORRECTNESS!!!!  HAVING ISSUES WITH LITERATURE REFERENCES
	newWaveform = app.Acquisition.C1.Out.Result.DataArray
	#alternatively, can set scaling argument to False.  For those cases, the output is a 16-bit signed integer CHECK THIS FOR CORRECTNESS!!!!  HAVING ISSUES WITH LITERATURE REFERENCES
	#newWaveFormInt = app.Acquisition.C1.Out.Result.DataArray(arrayValuesScaled=False)
	#convert to numpy array before being returned out
	newWaveFormAsArray = np.array(newWaveform)
	return newWaveFormAsArray

#read in data from channel 1 and also get the time axis
def readInDataFromScopeWithTime_c1():
	#readout the data
	newWaveform = app.Acquisition.C1.Out.Result.DataArray
	#lecroy does not provide a method to readout the time-axis.  However, Lecroy does provide methods to enable reconstruction of the time axis.  This can be done by finding the time separation between adjacent measurements, and also finding the number of samples in a measured trace
	timeSpacing = app.Acquisition.C1.Out.Result.HorizontalPerStep
	numSteps = app.Acquisition.C1.Out.Result.Samples
	#numpy.arange creates an array of integers up until its argument.  For example, np.arange(4) will yield the array: [0, 1, 2, 3].  This is used, in conjunction with the time steps between each sample, to produce a replica of the waveform's time axis.
	timeAxis = timeSpacing * np.arange(numSteps)
	#convert to numpy array before being returned out
	newWaveFormAsArray = np.array(newWaveform)

	return newWaveFormAsArray, timeAxis