##############################
#this library is here to house a time of flight to energy conversion.  The user is required to specify a time axis (bounds and numElements) in units of nanoseconds, an energy axis (bounds and numElements) in units of eV, and a time zero.  The step size for both axis can be found from the bounds and the number of elements desired).  The result is an overlap matrix that the time-based histogram can be multiplied by to produce an energy histogram.  Say the time axis has m elements, and the user specifies an n-element energy axis.  The overlap matrix is an n X m matrix.
##############################

import numpy as np
from math import sqrt

#set constants of the time of flight spectrometer
FLIGHT_LENGTH = 0.4 #in meters
MASS = 9.1e-31 #in kg
JOULE_PER_EV = 1.6e-19 #conversion value from 1 eV to Joule
NANOSECONDS_PER_SECOND = 1e9 #conversion value from 1 sec to ns
#COMBINED_CONSTANT is calculated here to minimize the number of arithmethic operations performed later.  It represents the constant to be divided by sqrt(Energy) to return time of flight in nanoseconds for an ideal particle on an ideal ToF trajectory.
COMBINED_CONSTANT = (FLIGHT_LENGTH*sqrt(MASS)/sqrt(2*JOULE_PER_EV))*NANOSECONDS_PER_SECOND


#calculate the overlap matrix which can be used to multiply a time-axis, to convert the ToF histogram into an energy histogram.  Returns an N (number of energy bins) by M (number of time bins) matrix.
#To get an energy histogram, take the overlap matrix and matrix multiply it by the time vector (value 0 of time vector is SHORTEST time of flight available, can be before time zero, final value is LONGEST time of flight available), to produce an energy vector, where the first element is the lowest energy (energyMin), and the last entry is the largest energy (energyMax) converted to.
def calculateOverlapMatrixTOFtoEnergy(energyMin=0, energyMax=30, energySamples=100, timeMin = 0, timeMax=0.00001, timeSamples=1000, timeZero=0):
	#create a zero matrix that will be populated to become the overlap matrix.  make it N by M, where N is the number of energy values, and M is the number of time values.
	overlapMatrix = np.zeros((energySamples, timeSamples))

	#create an array representative of the time vector
	timeVectorNotRegistered = np.linspace(timeMin, timeMax, timeSamples)*NANOSECONDS_PER_SECOND
	timeVector = timeVectorNotRegistered - timeZero #subtract time zero.  After this, negative values come before the light pulse, positive values represent time after the light pulse.
	#compute time steps between adjacent time bins in the time vector
	timeSpacing = NANOSECONDS_PER_SECOND*(timeMax - timeMin)/(timeSamples - 1)

	#creating the energy vector needs some care.  An energy of 0 causes the ToF to be infinite and causes errors down the road.  It is also meaningless to have energy histogram bins that cannot be measured from the time of flight.  For example, a maximum accessible ToF of ~500 nanoseconds implies electron energy of ~2 eV.  Having an energy vector that includes energies below the measurable cutoff axis makes the program more difficult to implement, but is also not worthwhile.  The energy vector thus does not necessarily comply with the user-supplied value.
	timeMaxAccessible = timeVector[-1]
	energyMinAccessible = convertTimeToEnergy(timeMaxAccessible)
	if(energyMin <= energyMinAccessible):
		#override the user supplied minimum with the lowest accessible energy
		#create an array representative of the energy vector, with the over-written energy minimum
		energyVector = np.linspace(energyMinAccessible, energyMax, energySamples)
		#calculate the energy grid spacing
		energySpacing = (energyMax - energyMinAccessible)/(energySamples - 1)
	else:
		#the user supplied minimum energy is within the system's measurement parameters and can be used as supplied
		#create an array representative of the energy vector.
		energyVector = np.linspace(energyMin, energyMax, energySamples)
		#compute energy steps between adjacent energy bins in the time vector
		energySpacing = (energyMax - energyMin)/(energySamples - 1)

	#fill in the overlapMatrix one row (one energy value) at a time.  Do it for the number of energy values available.
	for n in range(energySamples):
		
		#first, set the energy boundaries that should be integrated across to populate the current energy bin within the histogram.  The energy value in the energy vector is the center of the energy bins, but since actual energy values are continuous, the true bounds should be in between energy bins in the vector.
		if(n == 0):
			#handle the special case that this is the first iteration of the loop.
			lowerBoundE = energyVector[n]
			upperBoundE = energyVector[n] + energySpacing/2
		elif(n == (energySamples - 1)):
			#handle the special case that this is the last iteration of the loop
			lowerBoundE = energyVector[n] - energySpacing/2
			upperBoundE = energyVector[n]
		else:
			#this iteration is not a boundary case.
			lowerBoundE = energyVector[n] - energySpacing/2
			upperBoundE = energyVector[n] + energySpacing/2

		#lower and upper energy bounds are established.  Use the lower energy bound to calculate the longer time bound (longer time of flight) and the upper energy bound to calculate the shorter time bound for the current row of the overlap matrix
		longerBoundT = convertEnergyToTime(lowerBoundE)
		shorterBoundT = convertEnergyToTime(upperBoundE)

		#at this point, the time bounds have been found.  For time bins that are fully within these bounds, all of their population should contribute to the energy bin (overlapMatrix entry should be set to 1).  For time bins that are not fully within the boundaries, the time bin should be broken up into ratios to estimate how much of the time bin should go into any specific energy bin.  Sum of ratios should be 1.
		#performing the nitty-gritty of this calculation is ugly and sub-divided into method 'calculateRow' to make this method more manageable to interpret.
		overlapMatrix[n, :] = calculateRow(shorterBoundT, longerBoundT, timeVector)


	#overlapMatrix should be created and fully populated after the completion of the for loop, and can be returned to the calling function
	return overlapMatrix, energyVector


#the convertEnergyToTime takes an input energy, and returns a time of flight equivalent for a particle of that energy.  The setup parameters should be set at the top of this file.  This method allows for changes to the time of flight to energy conversion equation
def convertEnergyToTime(energy):
	if(energy <= 0):
		print("ERROR: the conversion from a particle energy to a time of flight was fed a non-positive energy value.  The structure in TOFtoEnergyConversion_lib only functions for positive, non-zero energies.")
		quit()
	else:
		#supplied energy is valid.  can proceed to calculate time.
		#CHANGES TO THIS FORMULA MUST BE MIRRORED IN 'convertTimeToEnergy'
		timeOfFlight = COMBINED_CONSTANT/sqrt(energy)

	return timeOfFlight

#in the event that a time of flight is supplied and an associated energy is desired, this calculation can be done here.  Should be the inverse of 'convertEnergyToTime'
def convertTimeToEnergy(timeOfFlight):
	#perform the inverse calculation done in 'convertEnergyToTime'
	#CHANGES TO THIS FORMULA MUST BE MIRRORED IN 'convertEnergyToTime'
	energy = pow(COMBINED_CONSTANT, 2)/pow(timeOfFlight, 2)

	return energy


#calculate an individual row of an overlap matrix, given the shorter and longer boundaries of the row, and the time axis.
def calculateRow(shorterBoundT, longerBoundT, timeVector):
	#calculate and store the number of elements in the timeVector.
	numTimes = len(timeVector)
	#calculate the time spacing between bins in the timeVector
	timeSpacing = (timeVector[-1] - timeVector[0])/(numTimes - 1)

	#initialize the row that will be returned as a row of zeros, to be populated as we go.
	calculatedRow = np.zeros_like(timeVector)

	#find the index at which the shorter time boundary crosses the timeVector.  This index will be used to start populating calculatedRow.  Note that numpy.searchsorted requires timeVector to be sorted.  searchsorted also finds the index at which the searched value can be inserted to maintain the sort, not the index that is nearest.
	shorterBoundInsertIndex = np.searchsorted(timeVector, shorterBoundT)

	#calculate the total quantity of bins that are spanned between the two time boundaries.  This will serve as a 'bank' that countains the amount of population to disperse into calculatedRow
	sumOfRowEntriesBank = (longerBoundT - shorterBoundT)/timeSpacing

	#find where to begin populating the row.  After finding where to start, extend row population to upper time boundary.
	if((timeVector[shorterBoundInsertIndex] - timeSpacing/2) >= shorterBoundT):
		#the population must begin at (shorterBoundInsertIndex - 1)
		#calculate the max amount that is permisible to insert at the starting bin.  This is the value that will almost certainly be inserted unless longerBoundT falls within the same bin.  This calculation is the offset in time between the shorter boundary and the cutoff in the row index divided by the time spacing.  It is the fraction of bin that is occupied between the time boundary and end of current calculatedRow bin
		maxAmountToInsertHere = ((timeVector[shorterBoundInsertIndex] - timeSpacing/2) - shorterBoundT)/timeSpacing
		#check for the exception that the long cutoff time is also in this region of calculatedRow bin.
		if(sumOfRowEntriesBank <= maxAmountToInsertHere):
			#if both boundaries are within here, only populate the bin until the bank is exhausted
			calculatedRow[shorterBoundInsertIndex-1] = sumOfRowEntriesBank
			sumOfRowEntriesBank -= sumOfRowEntriesBank
		else:
			#populate this row entry with the maximal amount allowable (the spacing between the boundary and the transition value between row indices)
			calculatedRow[shorterBoundInsertIndex-1] = maxAmountToInsertHere
			sumOfRowEntriesBank -= maxAmountToInsertHere

		#while there is more population left in the bank, keep iterating indices until the bank is exhausted
		indexNow = shorterBoundInsertIndex
		while(sumOfRowEntriesBank > 0):
			if(sumOfRowEntriesBank >= 1):
				#the long time cutoff boundary will not fall within this index, proceed to fill the entire bin.
				calculatedRow[indexNow] = 1
				sumOfRowEntriesBank -= 1
				indexNow += 1
			else:
				#the long cutoff boundary will fall within this index span.  this will be the final bin populated with whatever population (less than 1) left in the bank.
				if(indexNow < numTimes):
					calculatedRow[indexNow] = sumOfRowEntriesBank
					sumOfRowEntriesBank -= sumOfRowEntriesBank
				else:
					sumOfRowEntriesBank -= sumOfRowEntriesBank


	else:
		#the population begins at shorterBoundInsertIndex

		#
		maxAmountToInsertHere = ((timeVector[shorterBoundInsertIndex] + timeSpacing/2) - shorterBoundT)/timeSpacing
		#check for the exception that the long cutoff time is also in this region of calculatedRow bin.
		if(sumOfRowEntriesBank <= maxAmountToInsertHere):
			#if both boundaries are within here, only populate the bin until the bank is exhausted
			calculatedRow[shorterBoundInsertIndex] = sumOfRowEntriesBank
			sumOfRowEntriesBank -= sumOfRowEntriesBank
		else:
			#populate this row entry with the maximal amount allowable (the spacing between the boundary and the transition value between row indices)
			calculatedRow[shorterBoundInsertIndex] = maxAmountToInsertHere
			sumOfRowEntriesBank -= maxAmountToInsertHere


		#while there is more population left in the bank, keep iterating indices until the bank is exhausted
		indexNow = shorterBoundInsertIndex + 1
		while(sumOfRowEntriesBank > 0):
			if(sumOfRowEntriesBank >= 1):
				#the long time cutoff boundary will not fall within this index, proceed to fill the entire bin.
				calculatedRow[indexNow] = 1
				sumOfRowEntriesBank -= 1
				indexNow += 1
			else:
				#the long cutoff boundary will fall within this index span.  this will be the final bin populated with whatever population (less than 1) left in the bank.
				calculatedRow[indexNow] = sumOfRowEntriesBank
				sumOfRowEntriesBank -= sumOfRowEntriesBank


	#calculatedRow should now be completely filled.
	return calculatedRow