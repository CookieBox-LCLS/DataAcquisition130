import matplotlib.pyplot as pyplt
import numpy as np


#initializeGUI is here to produce the figure and axes on which plots will be handled witht he GUI
def initializeGUI(histogramSample):
	pyplt.ion()
	figure = pyplt.figure()
	axisHistogram = figure.add_subplot(1, 1, 1)
	histogramHandle, = axisHistogram.plot(histogramSample)
	#figure.canvas.draw()
	return figure, axisHistogram, histogramHandle

#updatePlotsMaster is a function that update the plots individually.  this is done as a separate method to help prevent the main loop from getting too long to read on it's own, and to help keep the code well organized
def updatePlotsMaster(figureIn, axisHistogram, histogramToPlot, histogramHandle):
	#for each axes

	#update the histogram
	histogramHandle.set_ydata(histogramToPlot)
	axisHistogram.set_ylim(0, np.amax(histogramToPlot))
	#axisHistogram.set_xlim(5001, 10001)
	#figureIn.canvas.draw()
	pyplt.pause(0.001)
	pyplt.show()

	return
	

#initialize histogram is used to create an array for the collected histogram.  at initialization, it is an array of zero's, the same size as a raw data trace
def initializeHistogram(rawData):
	histogram = np.zeros(len(rawData), dtype=int)
	return histogram


#addHitsToHistogram takes the indexes listed in 'newHits', and increments the respective bins in the array 'histogram'.  the method returns the updated version of 'histogram'
def addHitsToHistogram(newHits, histogram):
	#for each of the new hits in the array 'newHits',
	for ind in range(len(newHits)):
		#isolate the hit index
		hitIndexNow = newHits[ind].item()
		#and increment the respective bin in 'histogram'
		histogram[hitIndexNow] += 1

	return histogram