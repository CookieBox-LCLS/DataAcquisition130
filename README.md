# DataAcquisition130
this repository is for software developed to acquire eToF data using the prototype setup in laser lab 130.

The goal of this repository is to create a program that acquires data from the prototyping hardware in lab 130, saves it, and provides feedback via GUI to the user performing the acquisition.  The vision for the program is to have a master loop which directs the workings of the code by calling methods.  The methods are to be imported from individual libraries associated with different hardware, such that the method names within the main loop do not change, but the functions that are imported in their names are swapped out as the acquisition hardware evolves.

# File descriptions
V1_flowchart.png is a flowchart intended to visually describe the inner workings of the data acquisition GUI used in the prototyping setup.