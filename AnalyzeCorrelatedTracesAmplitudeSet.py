import glob
import lecroyparser
import sys
import statistics as stats
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

updateEveryXTraces = 1
binWidth = 3
Fs = 40e9


freqTicks = [0.5, 0.75, 1, 1.25]
freqLimits = (0.5, 1.25)

class analyzeCorrelatedTraces():

	def initPlots(self):
		self.figHandleRaw = plt.figure(figsize=(12,8))
		self.axisTracesLow = self.figHandleRaw.add_axes([0.25, 0.15, 0.6, 0.35])
		self.axisTracesHigh = self.figHandleRaw.add_axes([0.25, 0.5, 0.6, 0.35])
		self.axisTracesHigh.set_xlim((25, 100))
		self.axisTracesHigh.set_ylim((-4.5, 0.5))
		self.axisTracesHigh.set_xticks([])
		self.axisTracesHigh.set_yticks([-4, -2, 0])
		self.axisTracesLow.set_xlim((20, 100))
		self.axisTracesLow.set_ylim((-10, 10))
		self.axisTracesLow.set_xticks([20, 40, 60, 80, 100])
		self.axisTracesLow.set_yticks([-5, 0, 5])
		self.axisTracesLow.set_yticklabels(['-5e-3', '0', '5e-3'])
		self.axisTracesLow.set_xlabel("Time After Trigger (ns)", fontsize=30)
		self.axisTracesHigh.set_ylabel("Transmitting MCP (V)\n", fontsize=30)
		self.axisTracesLow.set_ylabel("Receiving MCP (V)\n\n", fontsize=30)

		self.figHandleFourier = plt.figure(figsize=(9,6))
		self.axisPowerSpectrum = self.figHandleFourier.add_axes([0.15, 0.15, 0.8, 0.7])
		self.axisPowerSpectrum.set_xlim(freqLimits)
		self.axisPowerSpectrum.set_ylim((0, 10))
		self.axisPowerSpectrum.set_xticks(freqTicks)
		self.axisPowerSpectrum.set_yticks([])
		self.axisPowerSpectrum.set_xlabel("Frequency (GHz)", fontsize=30)
		self.axisPowerSpectrum.set_ylabel("Spectral Power", fontsize=30)

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
		freqCutoffLow = 0
		freqCutoffHigh = 400
		freqSamplesToKeep = freqCutoffHigh - freqCutoffLow
		fileArrayIndex = 0

		traceStrengths = np.zeros(numTraces)
		ringingStrengths = np.zeros(numTraces)
		amplitudesSpans = np.zeros(numTraces)

		#perform a while loop to progress through the individual correlated trace measurements
		while (fileArrayIndex < numTraces):
			#extract data from .trc files associated with the current index counter into arrays of data
			fileChanOne = fileArrayOne[fileArrayIndex]
			fileChanTwo = fileArrayTwo[fileArrayIndex]
			timeAxis = lecroyparser.ScopeData(fileChanOne).x
			timeAxis = timeAxis * 1e9
			dataChanOne = lecroyparser.ScopeData(fileChanOne).y
			dataChanTwo = lecroyparser.ScopeData(fileChanTwo).y

			if fileArrayIndex == 0:
				#create frequency axis
				numSamples = timeAxis.size
				self.freqAxis = Fs* np.linspace(0, numSamples-1, numSamples) / numSamples
				spectralMap = np.zeros((numTraces, freqSamplesToKeep))

			triggerStrength = np.sum(dataChanTwo)
			ampSpan = np.amax(dataChanOne) - np.amin(dataChanOne)
			chanOneSpectral = fft(dataChanOne)
			absFFT = np.absolute(chanOneSpectral)
			powerSpectrum = np.square(absFFT)

			traceStrengths[fileArrayIndex] = -1*triggerStrength*0.025
			spectralMap[fileArrayIndex, :] = powerSpectrum[freqCutoffLow:freqCutoffHigh]
			ringingStrengths[fileArrayIndex] = np.sum(powerSpectrum[freqCutoffLow:freqCutoffHigh])
			amplitudesSpans[fileArrayIndex] = ampSpan

			if False and ((fileArrayIndex % updateEveryXTraces) == 0):
				#clear previous lines
				linesOld = self.axisTracesHigh.lines
				for i in range(len(linesOld)):
					lineToDel = linesOld.pop(0)
					del lineToDel
				linesOld = self.axisTracesLow.lines
				for i in range(len(linesOld)):
					lineToDel = linesOld.pop(0)
					del lineToDel
				plt.sca(self.axisTracesHigh)
				plt.plot(timeAxis, dataChanTwo, c='tab:blue')
				plt.xticks(fontsize=26)
				plt.yticks(fontsize=26)
				# self.axisTracesHigh.set_xlim((25e-9, 1e-7))
				plt.sca(self.axisTracesLow)
				plt.plot(timeAxis, 1000*dataChanOne, c='tab:orange')
				plt.xticks(fontsize=26)
				plt.yticks(fontsize=26)
				# self.axisTracesLow.set_xlim((25e-9, 1e-7))
				plt.draw()

				linesOld = self.axisPowerSpectrum.lines
				for i in range(len(linesOld)):
					lineToDel = linesOld.pop(0)
					del lineToDel
				plt.figure(self.figHandleFourier.number)
				plt.plot(self.freqAxis/1e9, powerSpectrum)
				plt.xticks(fontsize=26)
				plt.yticks(fontsize=26)
				plt.draw()
				plt.pause(0.001)

				# plt.waitforbuttonpress()
				breakpoint()

			#increment the file array index to proceed to the next trace
			fileArrayIndex += 1

		sortKeys = np.argsort(traceStrengths)
		sortedSpectralMap = spectralMap[sortKeys, :]

		# breakpoint()
		heatMapHandle = plt.figure(figsize=(9,6))
		heatMapHandle.add_axes([0.2, 0.2, 0.7, 0.7])
		temp = np.linspace(0, numTraces-1, numTraces)
		tempFreq = self.freqAxis[freqCutoffLow:freqCutoffHigh]
		plt.pcolormesh(tempFreq*1e-9, temp, np.log(sortedSpectralMap), shading='auto', vmin=-1, vmax=2.5)
		plt.colorbar()
		plt.xlim(freqLimits)
		plt.title("Tracking log(Spectral Power)", fontsize=30)
		plt.xlabel("Frequency (GHz)", fontsize=30)
		plt.ylabel("Unique Measurements\n", fontsize=30)
		plt.yticks([], fontsize=26)
		plt.xticks(freqTicks, fontsize=26)
		plt.draw()

		plt.figure(figHandleRingStrength.number)
		scatNow = plt.scatter(traceStrengths, ringingStrengths, s=1)
		scatterList.append(scatNow)
		plt.draw()
		plt.pause(0.001)

		# plt.figure(figHandleAmpSpans.number)
		# plt.scatter(traceStrengths, amplitudesSpans, s=1)
		# plt.draw()
		# plt.pause(0.001)



figHandleRingStrength = plt.figure(figsize=(15, 9))
# figHandleAmpSpans = plt.figure(figsize=(15,9))

directoryArray = []
scatterList = []


# directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_2300_2700/long_0_300_2100_2500'
# directoryArray.append(directory)
# directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_2100_2500/long_0_300_2100_2500'
# directoryArray.append(directory)
# directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_1900_2300/long_0_300_2100_2500'
# directoryArray.append(directory)

directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_2300_2700/long_0_300_1900_2300'
directoryArray.append(directory)
directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_2100_2500/long_0_300_1900_2300'
directoryArray.append(directory)
directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_1900_2300/long_0_300_1900_2300'
directoryArray.append(directory)

# directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_2300_2700/long_0_300_1700_2100'
# directoryArray.append(directory)
# directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_2100_2500/long_0_300_1700_2100'
# directoryArray.append(directory)
# directory = 'C:/Andrei/ScopeCollect/01_12_2021/correlationMeasures/short_200_500_1900_2300/long_0_300_1700_2100'
# directoryArray.append(directory)


numFiles = len(directoryArray)

#engage pyplot interactive mode
plt.ion()
#initiate analyzer construct
analyzer = analyzeCorrelatedTraces()


analyzer.initPlots()
for i in range(numFiles):
	directoryNow = directoryArray[i]

	#initiate main loop of analyzer class
	analyzer.runMainLoop(directoryNow)

	# if ((i + 1) % 3 == 0):
	# 	breakpoint()


plt.figure(figHandleRingStrength.number)
plt.ylim([0, 100])
plt.xlim([0, 25])
plt.title("Cross-talk as a Function of Voltages", fontsize=36)
plt.xlabel("Trigger MCP Signal Strength (a.u.)", fontsize=36)
plt.ylabel("Receiving MCP\nSpectral Power (a.u.)", fontsize=36)
legHandle = plt.legend(scatterList, ["1.8kV across tMCP", "1.6kV across tMCP", "1.4kV across tMCP"], fontsize=20, markerscale=20)
plt.xticks(fontsize=26)
plt.yticks(fontsize=26)