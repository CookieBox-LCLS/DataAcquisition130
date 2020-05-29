##############################
#this library is here to house a time of flight to energy conversion.  The user is required to specify a time axis (bounds and numElements) in units of nanoseconds, an energy axis (bounds and numElements) in units of eV, and a time zero.  The step size for both axis can be found from the bounds and the number of elements desired).  The result is an overlap matrix that the time-based histogram can be multiplied by to produce an energy histogram.  Say the time axis has m elements, and the user specifies an n-element energy axis.  The overlap matrix is an n X m matrix.
##############################

import numpy as np

#set constants of the time of flight spectrometer
FLIGHT_LENGTH = 0.4 #in meters
MASS = 9.1e-31 #in kg
JOULE_PER_EV = 1.6e-19 #conversion value from 1 eV to Joule
NANOSECONDS_PER_SECOND = 1e9 #conversion value from 1 sec to ns
#COMBINED_CONSTANT is calculated here to minimize the number of arithmethic operations performed later.  It represents the constant to be divided by sqrt(Energy) to return time of flight in nanoseconds for an ideal particle on an ideal ToF trajectory.
COMBINED_CONSTANT = (FLIGHT_LENGTH*sqrt(MASS)/SQRT(2*JOULE_PER_EV))*NANOSECONDS_PER_SECOND


#calculate the overlap matrix which can be used to multiply a time-axis, to convert the ToF histogram into an energy histogram.  Returns an N (number of energy bins) by M (number of time bins) matrix.
#To get an energy histogram, take the overlap matrix and matrix multiply it by the time vector (value 0 of time vector is SHORTEST time of flight available, can be before time zero, final value is LONGEST time of flight available), to produce an energy vector, where the first element is the lowest energy (energyMin), and the last entry is the largest energy (energyMax) converted to.
def calculateOverlapMatrixTOFtoEnergy(energyMin=0, energyMax=30, energySamples=100, timeMin = 0, timeMax=0.00001, timeSamples=1000, timeZero=0):
	#create a zero matrix that will be populated to become the overlap matrix.  make it N by M, where N is the number of energy values, and M is the number of time values.
	overlapMatrix = np.zeros((energySamples, timeSamples))

	#create an array representative of the time vector
	timeVectorNotRegistered = np.linspace(timeMin, timeMax, timeSamples)
	timeVector = timeVectorNotRegistered - timeZero #subtract time zero.  After this, negative values come before the light pulse, positive values represent time after the light pulse.
	#compute time steps between adjacent time bins in the time vector
	timeSpacing = (timeMax - timeMin)/(timeSamples - 1)

	#create an array representative of the energy vector.
	energyVector = np.linspace(energyMin, energyMax, energySamples)
	#compute energy steps between adjacent energy bins in the time vector
	energySpacing = (energyMax - energyMin)/(energySamples - 1)

	#fill in the overlapMatrix one row (one energy value) at a time.  Do it for the number of energy values available.
	for n in range(energySamples):
		
		#first, set the energy boundaries that should be integrated across to populate the current energy bin within the histogram.  The energy value in the energy vector is the center of the energy bins, but since actual energy values are continuous, the true bounds should be in between energy bins in the vector.
		if(n == 0):
			#handle the special case that this is the first iteration of the loop.
			if(energyVector[n] == 0):
				#The lowest energy value supplied may be zero.  This needs to handled specially because a particle with energy zero has infinite time of flight.
				#for this case, all longer times of flight have to be included.  This is effectively the same as setting a lowest considered energy that is inclusive of the longest time bin
				
				#infer a lower energy value that would include this longest time in the conversion.
				timeMaxAccessible = timeVector[end] + timeSpacing
				lowerBoundE = convertTimeToEnergy(timeMaxAccessible)
				upperBoundE = energyVector[n] + energySpacing/2
			else:
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


	pass




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
