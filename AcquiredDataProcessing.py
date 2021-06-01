import re
import numpy as np
import matplotlib.pyplot as plt
import sys
import scipy
#add library subfolder
sys.path.append("C:/Users/andre/Documents/GitHub/DataAcquisition130/libraries")
#import functions in library subfolder
from CFD_lib import andreiKamalovCFD_statistical as CFD
from generalPurposeProcessing_lib import writeOutRawData as writeOut
from generalPurposeProcessing_lib import generateNewFileAndHeader as generateNewFileAndHeader
from generalPurposeProcessing_lib import initializeHistogram
from generalPurposeProcessing_lib import addHitsToHistogram
from generalPurposeProcessing_lib import addToHitRateDistribution
from generalPurposeProcessing_lib import updateHitRateRunningWindow
from generalPurposeProcessing_lib import cutFourierScaleInHalf
from TOFtoEnergyConversion_lib import calculateOverlapMatrixTOFtoEnergy

#denote the byte size of the native data structure that the data is formatted in.  For example, if binary data represents float64, set the variable 'savedDataTypeSizeInBytes' to '8'
savedDataTypeSizeInBytes = 8
#denote the data type to interpret the binary data with.  Should be float64, unless trace files are worked with.  for .trc files, float32 seems to be expected.
dt = np.dtype("float64")
#flag for whether the user would like to manually progress through each trace
flagEachTraceStop = False
#flag for controlling whether to calculate and plot energy histogram or not.
plotEnergyHistogramFlag = False
#bin width for ToF histogram
binWidth = 1
#interactive mode needs to be on for plotting in a loop structure
plt.ion()

#setup parameters for overlap matrix calculation
Fs = 40e9
ENERGYMIN = 0
ENERGYMAX = 300
energySamples = 1500


#write in directory that contains data files.  please keep the slash at the end to indicate being inside the folder.
#also write in the actual data file name.  Header file is inferred from data file name.

folderArray = []
fileArray = []
timeZeroArray = []
appliedVoltageArray = []
legendNamesList = []



# #1300V across MCP (large pore)
# folderName = "C:/Andrei/ScopeCollect/08_14_2020/walkwayToF_70V_NoAmp_unlessNoted/370V_1670V_2070V/"
# dataFileName = "2020_08_14_15_39_05"
# timeZero = 0
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("1300V across, regular")


# #1400 across large pore
# folderName = "C:/Andrei/ScopeCollect/08_14_2020/walkwayToF_70V_NoAmp_unlessNoted/370V_1770V_2170V/"
# dataFileName = "2020_08_14_16_20_37"
# timeZero = 0
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("1400V across, regular")

# #1400 across MCP (small pore)
# folderName = "C:/Andrei/ScopeCollect/08_28_2020/short_eToFOnly/70_370_1770_2170/"
# dataFileName = "2020_08_28_15_05_23"
# timeZero = 0
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("1400V across, small pore")


# # #1600 across large pore
# folderName = "C:/Andrei/ScopeCollect/08_14_2020/walkwayToF_70V_NoAmp_unlessNoted/370V_1970V_2370V/"
# dataFileName = "2020_08_14_17_49_15"
# timeZero = 0
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("1600V across, regular")

# #1600 across MCP(small pore)
# folderName = "C:/Andrei/ScopeCollect/08_28_2020/short_eToFOnly/70_370_1970_2370/"
# dataFileName = "2020_08_28_15_29_10"
# timeZero = 0
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("1600V across, small pore")


# #1800 across large pore
# folderName = "C:/Andrei/ScopeCollect/08_14_2020/walkwayToF_70V_NoAmp_unlessNoted/370V_2170V_2570V/"
# dataFileName = "2020_08_14_16_48_57"
# timeZero = 0
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("1800V across, regular")

# # #1800V across MCP small pore
# folderName = "C:/Andrei/ScopeCollect/08_28_2020/short_eToFOnly/70_370_2170_2570/"
# dataFileName = "2020_08_28_15_48_50"
# timeZero = 0
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("1800V across, small pore")



# #2000 across large pore
# folderName = "C:/Andrei/ScopeCollect/08_14_2020/walkwayToF_70V_NoAmp_unlessNoted/370V_2370V_2770V/"
# dataFileName = "2020_08_14_17_16_10"
# timeZero = 0
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("2000V across, regular")



# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_50V/BackTubeMCPMesh_50V/350V_2150V_2550V/"
# dataFileName = "2020_08_27_15_53_24"
# timeZero = -500
# appliedVoltage = 50
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)


# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_100V/BackTubeMCPMesh_100V/400V_2200V_2600V/"
# dataFileName = "2020_08_27_12_35_37"
# timeZero = -500
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_150V/BackTubeMCPMesh_150V/450V_2250V_2650V/"
# dataFileName = "2020_08_27_16_26_28"
# timeZero = -500
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_200V/BackTubeMCPMesh_200V/500V_2300V_2700V/"
# dataFileName = "2020_08_27_12_15_52"
# timeZero = -500
# appliedVoltage = 200
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("0V retardation")

# ###retardation tests for 200V applied on front, lower voltages on back components
# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_200V/BackTubeMCPMesh_150V/450V_2250V_2650V/"
# dataFileName = "2020_08_27_11_56_57"
# timeZero = -600
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("50V retardation")


# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_200V/BackTubeMCPMesh_100V/400V_2200V_2600V/"
# dataFileName = "2020_08_27_17_49_21"
# timeZero = -800
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("100V retardation")


# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_200V/BackTubeMCPMesh_50V/350V_2150V_2550V/"
# dataFileName = "2020_08_27_17_23_11"
# timeZero = -1000
# appliedVoltage = 50
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# legendNamesList.append("150V retardation")



# folderName = "C:/Andrei/ScopeCollect/09_08_2020/walkwayToF_only/50V_350V_2150V_2550V/"
# dataFileName = "2020_09_08_12_50_14"
# timeZero = -265
# appliedVoltage = 50
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/09_08_2020/walkwayToF_only/70V_370V_2170V_2570V/"
# dataFileName = "2020_09_08_13_22_12"
# timeZero = -465
# appliedVoltage = 70
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/09_08_2020/walkwayToF_only/100V_400V_2200V_2600V/"
# dataFileName = "2020_09_08_13_33_34"
# timeZero = -465
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/09_08_2020/walkwayToF_only/150V_450V_2250V_2650V/"
# dataFileName = "2020_09_08_13_47_25"
# timeZero = -465
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/09_08_2020/walkwayToF_only/200V_500V_2300V_2700V/"
# dataFileName = "2020_09_08_14_03_20"
# timeZero = -465
# appliedVoltage = 200
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)


#walkway tof with coulomb charging after the wire was removed.  May be interesting to look at frequency components to see if fourier components have changed at all
# folderName = "C:/Andrei/ScopeCollect/09_28_2020/noseFront_100V/BackTubeMCPMesh_100V/400V_2200V_2600V/"
# dataFileName = "2020_09_28_16_43_54"
# timeZero = 700
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/09_28_2020/noseFront_150V/BackTubeMCPMesh_150V/450V_2250V_2650V/"
# dataFileName = "2020_09_28_17_03_24"
# timeZero = 700
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)



#######11/18/2020 data

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/postScans_100V_100V/"
# dataFileName = "2020_11_18_21_24_49"
# timeZero = 0
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_50/backAt_50/"
# dataFileName = "2020_11_18_14_05_41"
# timeZero = 0
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_100/backAt_100/"
# dataFileName = "2020_11_18_13_35_00"
# timeZero = 0
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_100/backAt_50/"
# dataFileName = "2020_11_18_18_55_16"
# timeZero = 0
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_150/backAt_150/"
# dataFileName = "2020_11_18_14_48_55"
# timeZero = 0
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_150/backAt_100/"
# dataFileName = "2020_11_18_15_20_49"
# timeZero = 0
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_150/backAt_50/"
# dataFileName = "2020_11_18_15_49_41"
# timeZero = 0
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)






# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_200/backAt_200/"
# dataFileName = "2020_11_18_20_23_32"
# timeZero = 0
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("0V retardation")

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_200/backAt_150/"
# dataFileName = "2020_11_18_19_54_49"
# timeZero = 0
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("50V retardation")

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_200/backAt_100/"
# dataFileName = "2020_11_18_19_22_48"
# timeZero = 0
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("100V retardation")

# folderName = "C:/Andrei/ScopeCollect/11_18_2020/retardationTests/frontAt_200/backAt_50/"
# dataFileName = "2020_11_18_16_32_35"
# timeZero = 0
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)
# legendNamesList.append("150V retardation")



#high resolution example
folderName = "C:/Andrei/ScopeCollect/scratch/400V_2000V_2400V/"
# dataFileName = "2020_08_13_18_54_57"
# dataFileName = "2020_08_13_20_03_16"
dataFileName = "2020_08_13_20_43_36"
timeZero = 0
appliedVoltage = 100
folderArray.append(folderName)
fileArray.append(dataFileName)
timeZeroArray.append(timeZero)
appliedVoltageArray.append(appliedVoltage)
legendNamesList.append("0V retardation")





# #8-27-2020 data sets here
# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_200V/BackTubeMCPMesh_50V/350V_2150V_2550V/"
# dataFileName = "2020_08_27_17_23_11"
# timeZero = 0
# appliedVoltage = 200
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_150V/BackTubeMCPMesh_50V/350V_2150V_2550V/"
# dataFileName = "2020_08_27_17_03_02"
# timeZero = 0
# appliedVoltage = 150
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_100V/BackTubeMCPMesh_50V/350V_2150V_2550V/"
# dataFileName = "2020_08_27_13_15_58"
# timeZero = 0
# appliedVoltage = 100
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)

# folderName = "C:/Andrei/ScopeCollect/08_27_2020/retardationTests/noseFront_50V/BackTubeMCPMesh_50V/350V_2150V_2550V/"
# dataFileName = "2020_08_27_15_53_24"
# timeZero = 0
# appliedVoltage = 50
# folderArray.append(folderName)
# fileArray.append(dataFileName)
# timeZeroArray.append(timeZero)
# appliedVoltageArray.append(appliedVoltage)







figHandleCountHistogram = plt.figure(figsize=(15,9))
axesHandleCountHistogram = figHandleCountHistogram.add_axes([0.15, 0.15, 0.8, 0.7])
figHandlePeakWidths = plt.figure(figsize=(15,9))
axesHandlePeakWidths = figHandlePeakWidths.add_axes([0.15, 0.15, 0.8, 0.7])
peakWidthsLegendsList = []
figHandleRiseTimes = plt.figure(figsize=(7,5))
axesHandleRiseTimes = figHandleRiseTimes.add_axes([0, 0, 1, 1])
figHandleFourierSum = plt.figure(figsize=(7,5))
axesHandleFourierSum = figHandleFourierSum.add_axes([0, 0, 1, 1])
figHandleFourierSumCutoff = plt.figure(figsize=(7,5))
axesHandleFourierSumCutoff = figHandleFourierSumCutoff.add_axes([0, 0, 1, 1])
if plotEnergyHistogramFlag:
	figHandleEnergyHistogram = plt.figure(figsize=(7,5))
	axesHandleEnergyHistogram = figHandleEnergyHistogram.add_axes([0, 0, 1, 1])

#calculate fourier axis
Fs = 40e9
dtime = 25e-12
numSamples = 20000
freqAxis = list(range(int(numSamples/2)))
freqAxis = [f*Fs/numSamples for f in freqAxis]



numFiles = len(folderArray)



#################
#HELPER METHODS SECTION
#################

#bin a raw histogram into the bin width specified by the user.  return a plot line's y-values to resemble histogram blocks, but be of the same length as the input variable 'rawHistogram'
def calculateBinnedHistogramTrace(rawHistogram, binWidth):
	lenFullTrace = rawHistogram.size
	#calculate the number of complete bins that rawHistogram can be binned into, for given binWidth
	numberCompleteBins = int(np.floor(lenFullTrace/binWidth))
	#reshape as much of the rawHistogram trace as possible
	lengthToBeReshaped = numberCompleteBins*binWidth
	reshapedTraceArray = np.reshape(rawHistogram[0:lengthToBeReshaped], [numberCompleteBins, binWidth])
	#use the reshaped trace to simplify calculation of bins.  sum up along axis 1 to sum across the bin width dimension.  in other words, sum up the components of a single bin with width binWidth.
	sumsOfBins = np.sum(reshapedTraceArray, 1)

	#using the binnedTrace, and the unutilized tail end of rawHistogram, stich together an array of the same dimension as rawHistogram, but with values that represent binned data.
	binnedPortionOfTrace = np.repeat(sumsOfBins, binWidth)#account for the binned portion of the trace.
	#stitch on any part of the trace not used in the binning
	unusedTraceTail = rawHistogram[lengthToBeReshaped:lenFullTrace]
	binnedTrace = np.concatenate((binnedPortionOfTrace, unusedTraceTail))#need argument of method to be a tuple of the two arrays to be stitched together.

	return binnedTrace

#make a binned histogram plot, between the select x-limits
def singleBinnedPlot(fullHistogram, binWidth, xLimLow, xLimHigh):
	binnedHistogram = calculateBinnedHistogramTrace(fullHistogram, binWidth)
	#make the plot
	plt.figure(figsize=(14,10))
	plt.plot(binnedHistogram)
	plt.xlim(xLimLow, xLimHigh)
	maxHeight = 1.05*np.amax(binnedHistogram)
	plt.ylim(0, maxHeight)
	plt.title("Histogram Binned with Width %d" % (binWidth), fontsize=26)
	plt.show()



#simpleMethod to generate some simple plots.  xlimits expected in index
def makeHistogramPlotsSimple(fullHistogram, binWidth, xLimLow, xLimHigh):
	binnedHistogram = calculateBinnedHistogramTrace(fullHistogram, binWidth)

	#make plot of full scale histogram, no binning
	plt.figure(figsize=(14,10))
	plt.plot(fullHistogram)
	plt.xlim(0, len(fullHistogram))
	maxHeight = 1 + np.amax(fullHistogram)
	plt.ylim(0, maxHeight)
	plt.title("Unbinned histogram", fontsize=30)
	plt.show()
	#plot the full scale histogram, with binning
	singleBinnedPlot(fullHistogram, binWidth, 0, len(fullHistogram))
	#make the zoomed in plot for the unbinned plot
	plt.figure(figsize=(14,10))
	plt.plot(fullHistogram)
	plt.xlim(xLimLow, xLimHigh)
	maxHeight = 1 + np.amax(fullHistogram[xLimLow:xLimHigh])
	plt.ylim(0, maxHeight)
	plt.title("Unbinned histogram, zoomed in", fontsize=30)
	plt.show()
	#make the zoomed in plot for the binned plot
	singleBinnedPlot(fullHistogram, binWidth, xLimLow, xLimHigh)


#function to plot a single trace out and it's hits
def makePlotTraceWithHits(dataIn, hitsFound, xLimLow=-1, xLimHigh=-1, colorIn="blue"):
	plt.figure(figsize=(14,10))
	plt.plot(dataIn, color=colorIn)
	if(len(hitsFound) > 0):
		plt.scatter(hitsFound, dataIn[hitsFound], color="red")
	if xLimLow != -1:
		#use user supplied value
		plt.xlim(left = xLimLow)

	if xLimHigh != -1:
		#use user supplied valueq
		plt.xlim(right = xLimHigh)

	plt.show()

#heper function to make a one line call to plot to preferences
def plotSimple(dataToPlot):
	plt.figure(figsize=(7,5))
	plt.plot(dataToPlot)
	plt.show()

#a wrapper method that contains all the single trace analysis that may be of interest
def executeSingleTraceAnalysis(dataIn):
	#if each trace is being cycled through, it is probably nice to plot out each trace in the user output
	if(flagEachTraceStop):
		#call CFD to help make the per trace plots
		rawData, hitIndices, hitLimitsHigh, convPeakMax = CFD(dataIn)

		#make the per trace raw data plot
		if(len(hitIndices) > 0):
			makePlotTraceWithHits(dataIn, np.concatenate((hitIndices, hitLimitsHigh), axis=0), xLimLow = hitIndices[0]-50, xLimHigh = hitIndices[0] + 1200)
			# makePlotTraceWithHits(dataIn, hitIndices, colorIn="green")
		else:
			# makePlotTraceWithHits(dataIn, hitIndices, colorIn="green")
			pass

	numHits = len(hitIndices)
	#if there's one hit, this trace may be useful to look at in fft domain
	if(numHits == 1):
		#calculate the FFT and only look at half of it (say, just positive frequencies)
		fourierFull = scipy.fft(dataIn)
		fourierMagnitude = np.absolute(fourierFull)
		fourierHalf = cutFourierScaleInHalf(fourierMagnitude)
		# plotSimple(fourierHalf)

		#call a bunch of functions to try and calculate/profile the single hit.  These functions should return meaningful characteristics of the single hit, and produce a quantity that can be used to compile a data set's statistics
		#create a normalized wavefunction
		normalizedData = normalizeTrace(dataIn)
		#figure out the FWHM of the temporal spike
		# characterizeTemporalFWHM(normalizedData)
		#figure out the rise time of the peak
		# characterizeTemporalRiseTime(normalizedData)

		# timeSignalFreqSubset = keepOnlyFrequencyRange(fourierFull, 9750, 10250)
		# plt.plot(np.abs(np.roll(fourierFull, int(len(fourierFull)/2))))
		# plt.show()
		# plt.plot(timeSignalFreqSubset[1500:4500])
		# plt.show()

#function to normalize a trace to be positive, such that the max of the trace is 1.
def normalizeTrace(dataIn):
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

#function to characterize the temporal FWHM of a peak, for a trace that has a single confirmed hit.  expects input trace to be normalized
def characterizeTemporalFWHM(dataInNorm):
	#set below variable to 0.5 for FWHM.  can play with this value to find FWQM if desired
	ratioToFind = 0.5

	#find x-value that has the maxima
	maxValIndex = np.argmax(dataInNorm)
	if(np.size(maxValIndex) != 1):
		#this peak has something weird about it
		raise ValueError("a trace that should have a single hit has found two indices that have the maximum value.")
	
	#find where the ratioToFind value is crossed later in time
	indexHigh = maxValIndex
	while(dataInNorm[indexHigh] > ratioToFind):
		indexHigh = indexHigh + 1

	#find where the ratioToFind value is crossed earlier in time
	indexLow = maxValIndex
	while(dataInNorm[indexLow] > ratioToFind):
		indexLow = indexLow - 1

	#calculate and return the number of time-steps that represent the peak's temporal FWHM
	lengthOfTime = indexHigh - indexLow + 1

	#if wanted to, can verify visually that FWHM was collected correctly
	if True:
		verifyFoundFWHMbyPlot(dataInNorm, maxValIndex, indexLow, indexHigh)

	return lengthOfTime

#function to characterize the number of time steps needed for peak rise.  Should be used on traces that have a single isolated hit.  Done by finding a max in the peak and then looking for time difference between peak max and some percentage of peak max (say, 10% of peak max).  expects input trace to be normalized.
def characterizeTemporalRiseTime(dataInNormalized):
	#define what fraction of the peak is to be considered the threshold that defines the time of the rising edge
	#use first thousand bins to measure statistical noise of this trace
	stdDev = np.std(dataInNormalized[0:1000])
	cutoffRatio = 3*stdDev

	#find the x-value that has the maximal value
	maxValIndex = np.argmax(dataInNormalized)
	if(np.size(maxValIndex) != 1):
		#this peak has something weird about it
		raise ValueError("a trace that should have a single hit has found two indices that have the maximum value.")

	#find where the ratioToFind value is crossed earlier in time
	indexLow = maxValIndex
	streakBelowThreshold = 0
	streakLengthToPass = 5
	while (streakBelowThreshold < streakLengthToPass):
		#keep running until three consecutive points are below the threshold
		while(dataInNormalized[indexLow] > cutoffRatio):
			#looking at a point which is above the cutoff ratio.  reset the streak
			streakBelowThreshold = 0
			#and decrement index towards start of time
			indexLow = indexLow - 1

		streakBelowThreshold += 1
		indexLow = indexLow - 1


	riseTime = maxValIndex - indexLow + 1 - streakLengthToPass

	#if wanted to, can verify visually that FWHM was collected correctly
	if False:
		verifyFoundFWHMbyPlot(dataInNormalized, maxValIndex, (indexLow + streakLengthToPass), maxValIndex)

	return riseTime

#helper function that can be caled if used wants to verify that the FWHM found by method 'characterizeTemporalFWHM' is correct, by visual comparison
def verifyFoundFWHMbyPlot(dataIn, indexMax, indexLow, indexHigh):
	startTraceLow = indexMax - 2*(indexMax - indexLow)
	startTraceHigh = indexMax + 2*(indexHigh - indexMax)
	plt.figure(figsize=(7,5))
	plt.plot(list(range(startTraceLow, startTraceHigh)), dataIn[startTraceLow:startTraceHigh], color="blue")
	plt.plot(list(range(indexLow, indexHigh+1)), dataIn[indexLow:indexHigh+1], color="red")
	plt.show()


#accept a set of frequencies, keep only a subset of them, and then ifft them
def keepOnlyFrequencyRange(fft, indexStartRange, indexEndRange):
    
	freqCopy = np.asarray(fft)
	freqCopy = np.roll(freqCopy, int(len(fft)/2))
	if indexStartRange <= 0:
		pass
	else:
		freqCopy[0:(indexStartRange-1)] = 0

	if indexEndRange >= len(fft):
		pass
	else:
		freqCopy[(indexEndRange+1):-1] = 0

	freqCopy = np.roll(freqCopy, -1*int(len(fft)/2))

	timeSignal = scipy.ifft(freqCopy)

	return timeSignal


def calculateFWHMOfFoundHit(rawData, indexLow, indexHigh, convolvedMaxIndex):
	maxVal = rawData[convolvedMaxIndex]
	lowValLeft = rawData[indexLow]
	desiredVal = (maxVal + lowValLeft) / 2
	indexNow = indexLow
	while lowValLeft < desiredVal:
		indexNow += 1
		lowValLeft = rawData[indexNow]
	indexLeftLast = indexNow

	lowValRight = rawData[indexHigh]
	desiredVal = (maxVal + lowValRight) / 2
	indexNow = indexHigh
	while lowValRight < desiredVal:
		indexNow -= 1
		lowValRight = rawData[indexNow]

	spanOfHit = indexNow - indexLeftLast
	return spanOfHit

#################
#START OF SCRIPT
#################



for i in range(numFiles):
	folderName = folderArray[i]
	dataFileName = fileArray[i]


	headerFileName = dataFileName + "_HEADER.txt"

	#################
	#LOAD IN DATA
	#################
	#this section loads in the raw data and prepares everything necessary for data extraction.  USER MUST WRITE IN FILE AND FOLDER NAMES IN THE APPROPRIATE BLOCK SOMEWHERE IN THE HEADER

	#set up to load binary data in.  use "rb" to indicate read only from binary for data file
	dataFile = open(folderName + dataFileName, "rb")
	#set up read only for ascii format header file.
	headerFile = open(folderName + headerFileName, "r")

	#extract the individual trace size from the header.  Done using imported library re (regular expressions)
	for line in headerFile:
		match = re.search("The size of an individual trace, in bytes, within the binary file is: (\d+)", line)
		if match:
			#record the trace data size that is in the header file.
			traceDataSize = (int(match.group(1)))
			numSamples = traceDataSize/8

	#################
	#PROCESS SAVED RAW DATA
	#################
	#setup variables that are useful for each run
	tracesProcessed = 0
	totalNumberHits = 0
	numberSamplesFourier = 0
	#default the reading loop condition to true
	moreToRead = True
	#loop through each trace
	while moreToRead:
		#try reading in data.  
		segmentNow = dataFile.read(traceDataSize)
		#convert binary segment into a numpy array of appropriate data type
		traceNow = np.frombuffer(segmentNow, dtype=dt)


		if(len(traceNow) == 0):
			moreToRead = False
			print("The end of file was reached, with 0 bytes in the final read")
		elif(len(traceNow) < traceDataSize/savedDataTypeSizeInBytes):
			print("A trace was read in with a byte size that is not equal to the size prescribed in the header file.")
		else:
			#a normal, complete trace has been extracted.  This section may be used to process traces as desired by user.

			#perform processing similar to that done on the o-scope
			rawData, hitIndices, hitLimitsHigh, convPeakMax = CFD(traceNow)
			normedTrace = normalizeTrace(rawData)

#			plt.figure()
#			plt.plot(traceNow)
#			if (hitIndices.size > 0):
#				plt.scatter(hitIndices, traceNow[hitIndices], s=150)
#			plt.draw()
#			plt.pause(0.001)

			totalNumberHits = totalNumberHits + len(hitIndices)

			#if this is the first trace, set up some variables for the first time
			if(tracesProcessed == 0):
				histogramCollected = initializeHistogram(rawData)

				peakWidthHistogram = initializeHistogram(rawData)
				riseTimeHistogram = initializeHistogram(rawData)
				#setup fourier absolute spectra
				fourierFull = scipy.fft(rawData)
				fourierMagnitude = np.absolute(fourierFull)
				fourierHalf = cutFourierScaleInHalf(fourierMagnitude)
				fourierSum = np.zeros(len(fourierHalf))

			#add hits found in this trace to the histogram
			histogramCollected = addHitsToHistogram(hitIndices, histogramCollected)

			if len(hitIndices) <= 10:
				FWHMList = []
				for l in range(len(hitIndices)):
					FWHMList.append(calculateFWHMOfFoundHit(normedTrace, hitIndices[l], hitLimitsHigh[l], convPeakMax[l]))
				peakWidthHistogram = addHitsToHistogram(FWHMList, peakWidthHistogram)

				riseTimeHistogram = addHitsToHistogram((convPeakMax - hitIndices), riseTimeHistogram)
				#add to fourier spectrum
				fourierFull = scipy.fft(rawData)
				fourierMagnitude = np.absolute(fourierFull)
				fourierHalf = cutFourierScaleInHalf(fourierMagnitude)
				fourierSum += fourierHalf
				numberSamplesFourier += 1
			
				if flagEachTraceStop:
					executeSingleTraceAnalysis(traceNow)
					input("Press a key to continue")

			tracesProcessed = tracesProcessed + 1



			pass



	timeAxis = np.array([k*40 for k in list(range(int(numSamples)))])

	histogramCollected = calculateBinnedHistogramTrace(histogramCollected, binWidth)
	plt.figure(figHandleCountHistogram.number)
	lineHandle = plt.plot(timeAxis/1000, histogramCollected/np.sum(histogramCollected), linewidth=1)
	peakWidthsLegendsList.append(lineHandle)
	plt.draw()
	plt.pause(1)
	#make a zoomed in version for each histogram
	figHandleTemp = plt.figure(figsize=(9, 6))
	figHandleTemp.add_axes([0.2, 0.2, 0.7, 0.6])
	plt.plot(timeAxis/1000, histogramCollected/np.sum(histogramCollected), linewidth=1, color=lineHandle[0].get_color())
	if i == 0:
		plt.xlim([64, 74])
		plt.xticks([64, 74])
	elif i == 1:
		plt.xlim([72, 82])
		plt.xticks([72, 82])
	elif i == 2:
		plt.xlim([84, 94])
		plt.xticks([84, 94])
	elif i == 3:
		plt.xlim([108, 118])
		plt.xticks([108, 118])
	plt.ylim([0, 0.0005])
	plt.xticks(fontsize=26)
	plt.yticks(fontsize=26)
	plt.yticks([0, 0.0005])
	plt.title("Zoomed in Histogram", fontsize=36)
	plt.xlabel("Time of Flight (ns)", fontsize=36)
	plt.pause(1)
	plt.draw()


	peakWidthHistogram = peakWidthHistogram/np.sum(peakWidthHistogram)
	plt.figure(figHandlePeakWidths.number)
	lineHandle = plt.plot(timeAxis, peakWidthHistogram, linewidth=4)
	# peakWidthsLegendsList.append(lineHandle)
	plt.pause(1)
	plt.draw()

	axesHandleRiseTimes.plot(riseTimeHistogram)
	axesHandleRiseTimes.set_title("rise time distribution")
	axesHandleRiseTimes.set_xlim(0, 60)
	axesHandleRiseTimes.set_ylim(0)
	plt.pause(1)
	plt.draw()

	axesHandleFourierSum.plot(freqAxis, fourierSum/numberSamplesFourier)
	axesHandleFourierSum.set_ylim(0)
	plt.pause(1)
	plt.draw()

	partialFourier = fourierSum[0:1200]
	freqAxisPartial = freqAxis[0:1200]
	axesHandleFourierSumCutoff.plot(freqAxisPartial, partialFourier/np.sum(partialFourier))
	axesHandleFourierSumCutoff.set_ylim(0)
	plt.pause(1)
	plt.draw()


	#optional plotting of energy histogram
	if plotEnergyHistogramFlag:
		appliedVoltage = appliedVoltageArray[i]
		timeZero = timeZeroArray[i]
		numSamples = histogramCollected.size
		#establish time axis
		timeAxis = [k/Fs for k in list(range(numSamples))]
		#load the time parameters needed to calculate the overlap matrix
		TIMEMIN = min(timeAxis)
		TIMEMAX = max(timeAxis)
		overlapMatrix, energyVector = calculateOverlapMatrixTOFtoEnergy(energyMin=ENERGYMIN, energyMax=ENERGYMAX, energySamples=energySamples, timeMin = TIMEMIN, timeMax=TIMEMAX, timeSamples=numSamples, timeZero=timeZero/Fs, appliedVoltage=appliedVoltage)
		energyHistogram = np.matmul(overlapMatrix, histogramCollected)
		energyHistogramNorm = energyHistogram/max(energyHistogram)
		axesHandleEnergyHistogram.plot(energyVector, energyHistogramNorm)




	averageRate = totalNumberHits/tracesProcessed
	print("the average number of hits is {}".format(averageRate))


	#################
	#SECTION TO MAKE PLOTS FROM PROCESSED DATA
	#################
	binWidthForPlot = 2
	xLimLow = 2000
	xLimHigh = 5000

	# makeHistogramPlotsSimple(histogramCollected, binWidthForPlot, xLimLow, xLimHigh)
	#singleBinnedPlot(histogramCollected, binWidthForPlot, xLimLow, xLimHigh)

	#################
	#SECTION TO CLOSE OUT THE RUN AND CLEAN UP
	#################
	#close out files
	headerFile.close()
	dataFile.close()



#make nice plot showing histogram comparison
plt.figure(figHandleCountHistogram.number)
plt.title("eToF Histograms for ATI Electrons\nAccelerated to 200V", fontsize=36)
plt.xlabel("Time of Flight (ns)", fontsize=36)
plt.ylabel("Signal Strength (normalized)", fontsize=36)
plt.xticks(fontsize=26)
plt.yticks(fontsize=26)
plt.yticks([0, 0.0025])
legHandle = plt.legend(tuple([i[0] for i in peakWidthsLegendsList]), tuple(legendNamesList), fontsize=20)
[i.set_linewidth(4) for i in legHandle.get_lines()]
plt.xlim([60, 150])
plt.ylim([0, 0.0025])
plt.pause(1)
plt.draw()

plt.figure(figsize=(15,9))
plt.plot(timeAxis/1000, histogramCollected/np.sum(histogramCollected), linewidth=1)
plt.xlim([60, 150])
plt.ylim([0, 0.005])
plt.draw()



#may be nice to also plot ylim[0, 0.0005].  1 - xlim[64, 74]  2 - xlim[72, 82]  3 - xlim[84, 94] 4 - xlim[108,118]


#make nice plot of FWHM duration
# plt.figure(figHandlePeakWidths.number)
# plt.title("Waveform Hit Temporal Duration (FWHM)", fontsize=36)
# plt.xlabel("Duration (ps)", fontsize=36)
# plt.ylabel("Signal Distribution Histogram \n(normalized)", fontsize=36)
# plt.xticks(fontsize=26)
# plt.yticks(fontsize=26)
# plt.yticks([])
# plt.legend(tuple([i[0] for i in peakWidthsLegendsList]), tuple(legendNamesList), fontsize=20)
# plt.xlim([0, 1500])
# plt.ylim([0, 0.3])
# plt.pause(1)
# plt.draw()