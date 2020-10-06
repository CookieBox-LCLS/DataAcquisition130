import glob
import lecroyparser
import sys
#add library subfolder
sys.path.append("C:/Users/andre/Documents/GitHub/DataAcquisition130/libraries")
from generalPurposeProcessing_lib import cutFourierScaleInHalf
from generalPurposeProcessing_lib import addHitsToHistogram
from generalPurposeProcessing_lib import calculateBinnedHistogramTrace
import matplotlib.pyplot as plt
import numpy as np
from scipy import fft
from CFD_lib import andreiKamalovCFD_statistical as CFD
from TOFtoEnergyConversion_lib import calculateOverlapMatrixTOFtoEnergy

updateEveryXTraces = 1000
binWidth = 3


class analyzeCorrelatedTraces():

	#helper method to intialize figure and axis handles.
	def initPlots(self, directory, timeZero=0, appliedVoltage=0):
		numSamples = 19960
		# if timeZero < 0 :
		# 	numSamples += int(timeZero)
		Fs = 40e9
		self.freqAxis = list(range(int(numSamples/2) - 1))
		self.freqAxis = [f*Fs/numSamples for f in self.freqAxis]

		####initialize and construct overlap matrix - matrix that converts times of flight to energy
		#establish time axis
		timeAxis = [i/Fs for i in list(range(numSamples))]
		#load the time parameters needed to calculate the overlap matrix
		TIMEMIN = min(timeAxis)
		TIMEMAX = max(timeAxis)
		ENERGYMIN = 0
		ENERGYMAX = 300
		energySamples = 1500
		#make the call to recalcualte the overlap matrix.
		self.overlapMatrix, self.energyVector = calculateOverlapMatrixTOFtoEnergy(energyMin=ENERGYMIN, energyMax=ENERGYMAX, energySamples=energySamples, timeMin = TIMEMIN, timeMax=TIMEMAX, timeSamples=numSamples, timeZero=timeZero/Fs, appliedVoltage=appliedVoltage)


		####construct raw trace plotter
		#setup figure that will be used for raw trace plot outs
		self.figHandleTraces = plt.figure(figsize=(6,4))
		self.axisTraces = self.figHandleTraces.add_axes([0, 0, 1, 1])

		xLimLow = 1000
		xLimHigh = 6000
		self.xLimits = [xLimLow, xLimHigh]

		#####construct fft figure
		#setup figure that will be used to plot FFT results
		self.figHandleFourier = plt.figure(figsize=(6,4))
		self.axisFourier = self.figHandleFourier.add_axes([0, 0, 1, 1])
		self.xLimFourierLow = 1
		self.xLimFourierHigh = 1000

		#setup range for which to window in on ringing signal
		self.ringingRangeLow = 0
		self.ringingRangeHigh = numSamples
		#figure out length of summed up fourier axis
		axisFourier = cutFourierScaleInHalf(range(self.ringingRangeLow, self.ringingRangeHigh))
		self.arrayFourierSum = np.zeros(len(axisFourier))

		######setup for histogram plots
		self.figHandleHistograms = plt.figure(figsize=(6,4))
		self.axisHistogram = self.figHandleHistograms.add_axes([0, 0, 1, 1])
		#re-use x limits from trace plot to apply to the histogram plot.
		#initialize the histogram variables that will be used to store the found hits for both channels
		self.histogramOne = np.zeros(numSamples)
		self.histogramTwo = np.zeros(numSamples)
		#add directory to histogram plot
		self.figHandleHistograms.suptitle(directory)

		#####setup for energy histogram plot
		self.figHandleEnergyHistogram = plt.figure(figsize=(6,4))
		self.axisEnergyHistogram = self.figHandleEnergyHistogram.add_axes([0, 0, 1, 1])
		#setup energy histo's
		self.energyHistogramOne = np.zeros(self.energyVector.size)
		self.energyHistogramTwo = np.zeros(self.energyVector.size)
		self.figHandleEnergyHistogram.suptitle(directory)

	#helper method to plot the raw traces passed in onto the common figure/axis handle
	def plotBothChannels(self, dataOne, dataTwo, updatePlots):
		#plots look better if the traces are to scale.  try normalizing them
		normalizedOne = self.normalizeTrace(dataOne)
		normalizedTwo = self.normalizeTrace(dataTwo)

		if updatePlots:
			#find where hits are on the two traces
			rawData, hitIndicesOne, hitLimitsHighOne, convPeakMaxOne = CFD(normalizedOne)
			rawData, hitIndicesTwo, hitLimitsHighTwo, convPeakMaxTwo = CFD(normalizedTwo)

			#clear previous lines
			linesOld = self.axisTraces.lines
			for i in range(len(linesOld)):
				lineToDel = linesOld.pop(0)
				del lineToDel
			#clear previous scatter plots
			scatterOld = self.axisTraces.collections
			for i in range(len(scatterOld)):
				scatterToDel = scatterOld.pop(0)
				del scatterToDel
			#plot normalized traces
			self.axisTraces.plot(normalizedOne, color="blue")
			self.axisTraces.plot(normalizedTwo, color="green")
			#plot scatter markers to denote hits
			for i in range(len(hitIndicesOne)):
				collectionToPlot = [hitIndicesOne[i], hitLimitsHighOne[i]]
				self.axisTraces.scatter(collectionToPlot, normalizedOne[collectionToPlot], color="red")
			#repeat for hits for trace two
			for i in range(len(hitIndicesTwo)):
				collectionToPlot = [hitIndicesTwo[i], hitLimitsHighTwo[i]]
				# self.axisTraces.scatter(collectionToPlot, normalizedTwo[collectionToPlot], color="red")
			#set limits
			self.axisTraces.set_xlim(self.xLimits)

			#update calls to draw the plot
			self.figHandleTraces.canvas.draw()


	#function to add the ringing frequency component to an ongoing summation
	def addNewTraceRinging(self, ringingChannelData, updatePlots):
		subsetLimitLow = self.ringingRangeLow
		subsetLimitHigh = self.ringingRangeHigh
		ringingDataSubset = ringingChannelData[range(subsetLimitLow, subsetLimitHigh)]

		#compute the fourier components of ringing subset, and add them to an ongoing summation
		fftOfSubset = fft(ringingDataSubset)
		#only want magnitude
		absFFT = np.absolute(fftOfSubset)
		fftToAdd = cutFourierScaleInHalf(absFFT)
		#add the new fft component to the ongoing summation
		self.arrayFourierSum += fftToAdd

		if updatePlots:
			#plot out summed fft of ringing range
			#clear fft plot of last trace
			lineOld = self.axisFourier.lines
			for i in range(len(lineOld)):
				lineToDel = lineOld.pop(0)
				del lineToDel
			#update the plot of the fourier figure
			self.axisFourier.plot(self.freqAxis[self.xLimFourierLow:self.xLimFourierHigh], self.arrayFourierSum[self.xLimFourierLow:self.xLimFourierHigh])
			#apply limits
			self.axisFourier.set_xlim(self.freqAxis[self.xLimFourierLow], self.freqAxis[self.xLimFourierHigh])

			#update calls to draw the plots
			self.figHandleFourier.canvas.draw()

	#find hits in trace data supplied and add it to growing histograms
	def addToHistograms(self, dataOne, dataTwo, updatePlots):
		#normalize the raw traces
		normalizedOne = self.normalizeTrace(dataOne)
		normalizedTwo = self.normalizeTrace(dataTwo)

		#process new trace and add hits for channel 1
		rawData, hitIndices, hitLimitsHigh, convPeakMax = CFD(normalizedOne)
		self.histogramOne = addHitsToHistogram(hitIndices, self.histogramOne)

		#do the same for channel 2
		rawData, hitIndices, hitLimitsHigh, convPeakMax = CFD(normalizedTwo)
		self.histogramTwo = addHitsToHistogram(hitIndices, self.histogramTwo)


		if updatePlots:
			#plot the current histogram for channel 1
			#clear previous lines in time histogram
			linesOld = self.axisHistogram.lines
			for i in range(len(linesOld)):
				lineToDel = linesOld.pop(0)
				del lineToDel

			#clear previous lines in energy histogram
			linesOld = self.axisEnergyHistogram.lines
			for i in range(len(linesOld)):
				lineToDel = linesOld.pop(0)
				del lineToDel

			#plot the current/new histograms
			self.axisHistogram.plot(calculateBinnedHistogramTrace(self.histogramOne, binWidth))
			self.axisHistogram.plot(calculateBinnedHistogramTrace(self.histogramTwo, binWidth))
			#set limits
			self.axisHistogram.set_xlim(self.xLimits)

			#calculate new energy histogram values
			self.energyHistogramOne = np.matmul(self.overlapMatrix, self.histogramOne)
			self.energyHistogramTwo = np.matmul(self.overlapMatrix, self.histogramTwo)
			#plot the new energy histogram values on the appropriate axis
			self.axisEnergyHistogram.plot(self.energyVector, self.energyHistogramOne)
			# self.axisEnergyHistogram.plot(self.energyHistogramTwo)


			#update calls to draw the plots
			self.figHandleHistograms.canvas.draw()
			self.figHandleEnergyHistogram.canvas.draw()

		pass


	#function to normalize a trace to be positive, such that the max of the trace is 1.
	def normalizeTrace(self, dataIn):
		#ensure that the dataIn value is normalized to zero.  Do this by finding a median value of the trace
		dataInNorm = dataIn - np.median(dataIn)
		#normalize the data such that the highest point has absolute value of 1.  First, find the maximal value but also figure out if peak is upwards or downwards going
		maximalValueAbs = np.absolute(np.max(dataInNorm))
		minimalValueAbs = np.absolute(np.min(dataInNorm))
		if(maximalValueAbs > minimalValueAbs):
			#the peak is positive going.  normalize with positive value
			dataInNorm = dataInNorm/maximalValueAbs
		else:
			#the peak is negative going.  normalize with negative value
			dataInNorm = -1*dataInNorm/minimalValueAbs

		return dataInNorm

	#method to begin running the main loop of this program
	def runMainLoop(self, directory):
				#setup directory for correlated traces
		dataFolderDirectory = directory
		#create arrays that contain all the .trc files for both chan 1 and chan 2 (Separate)
		globPathNameChanOne = dataFolderDirectory + '/C1*.trc'
		globPathNameChanTwo = dataFolderDirectory + '/C2*.trc'
		fileArrayOne = glob.glob(globPathNameChanOne)
		fileArrayTwo = glob.glob(globPathNameChanTwo)

		#setup to progress through entire array of .trc files
		numTraces = len(fileArrayOne)
		fileArrayIndex = 0

		#perform a while loop to progress through the individual correlated trace measurements
		while (fileArrayIndex < numTraces):
			#extract data from .trc files associated with the current index counter into arrays of data
			fileChanOne = fileArrayOne[fileArrayIndex]
			fileChanTwo = fileArrayTwo[fileArrayIndex]
			timeAxis = lecroyparser.ScopeData(fileChanOne).x
			dataChanOne = lecroyparser.ScopeData(fileChanOne).y
			dataChanTwo = lecroyparser.ScopeData(fileChanTwo).y

			if (fileArrayIndex % updateEveryXTraces == 0) :
				updatePlotsFlag = True
			else:
				updatePlotsFlag = False

			#process correlated channels as desired
			#show user what traces look like
			self.plotBothChannels(dataChanOne, dataChanTwo, updatePlotsFlag)

			#go into the ringing range and add that fourier component to an ongoign sum
			self.addNewTraceRinging(dataChanTwo, updatePlotsFlag)

			#process the current traces to add their hits to the growing histograms
			self.addToHistograms(dataChanOne, dataChanTwo, updatePlotsFlag)

			#increment the file array index to proceed to the next trace
			fileArrayIndex += 1

			if updatePlotsFlag :
				# plt.waitforbuttonpress()
				plt.pause(0.1)


		return self.energyHistogramOne, self.energyVector


directoryArray = []
timeZeroArray = []
appliedVoltageArray = []

figHandleCompare = plt.figure(figsize=(6,4))
axisCompare = figHandleCompare.add_axes([0, 0, 1, 1])

#select which data set to look through.  
#for 200V, use ringing analysis range of 1250:1650
# directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/200_500_2300_2700'
# timeZero = -400
# appliedVoltage = 200
# directoryArray.append(directory)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/200_500_2100_2500'
# directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/200_500_1900_2300'
#for 100V, use ringing analysis range of 1800:2200
# directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/100_400_2200_2600'
# timeZero = -400
# appliedVoltage = 100
# directoryArray.append(directory)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/100_400_2000_2400'
# directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/100_400_1800_2200'
#for 50V, use ringing analysis range of 2700:3100
# directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/50_350_1750_2150'
# directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/50_350_1950_2350'
directory = 'C:/Andrei/ScopeCollect/08_28_2020/correlationMeasurements/50_350_2150_2550'
timeZero = -400
appliedVoltage = 50
directoryArray.append(directory)
timeZeroArray.append(timeZero)
appliedVoltageArray.append(appliedVoltage)


#compare correlated traces with replaced lens stack (no meshes)
# directory = 'C:/Andrei/ScopeCollect/09_08_2020/correlatedToFs/100V_400V_2200V_2600V'
# timeZero = -310
# appliedVoltage = 100
# directoryArray.append(directory)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
#for 70V, try range of 2400:2800
# directory = 'C:/Andrei/ScopeCollect/09_08_2020/correlatedToFs/70V_370V_2170V_2570V'
directory = 'C:/Andrei/ScopeCollect/09_08_2020/correlatedToFs/50V_350V_2150V_2550V'
timeZero = -310
appliedVoltage = 50
directoryArray.append(directory)
timeZeroArray.append(timeZero)
appliedVoltageArray.append(appliedVoltage)


numFiles = len(directoryArray)

#engage pyplot interactive mode
plt.ion()
#initiate analyzer construct
analyzer = analyzeCorrelatedTraces()


for i in range(numFiles):
	directoryNow = directoryArray[i]
	timeZeroNow = timeZeroArray[i]
	appliedVoltageNow = appliedVoltageArray[i]

	#initiate plots used
	analyzer.initPlots(directoryNow, timeZero=timeZeroNow, appliedVoltage=appliedVoltageNow)
	#initiate main loop of analyzer class
	energyHistoOne, energyVector = analyzer.runMainLoop(directoryNow)


	axisCompare.plot(energyVector, energyHistoOne)
	figHandleCompare.canvas.draw()