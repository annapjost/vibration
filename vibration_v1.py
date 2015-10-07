from ij import IJ, ImagePlus, ImageStack
from ij import WindowManager as WM
from ij.gui import Plot as Plot
from ij.gui import PlotWindow as PlotWindow
from ij.io import OpenDialog
from ij.measure import ResultsTable
from fiji.util.gui import GenericDialogPlus
from os import path
from math import sqrt


def getResultsXCsYCs():
    '''grabs the XC and YC columns from the results table output from gaussfit_onspot plugin'''
    #grab the results table:
    rt = ResultsTable.getResultsTable()
    #initialize the lists for xcs and ycs:
    XCs = []
    YCs = []
    size = rt.size()
    # now loop through each row in the results table 
    for row in range(size):
        xc = rt.getValue("XC", row)
        yc = rt.getValue("YC", row)
        XCs.append(xc)
        YCs.append(yc)
    return (XCs, YCs, size)
    
#how big is it?  set whether to use slices or frames for looping, because sometimes
# these stacks are frames and sometimes slices.  
def isFrames(imp):
    """Determine whether the stack has >1 slices or >1 frames"""
    NSlices = imp.getNSlices()
    NFrames = imp.getNFrames()
    print "number of slices:", NSlices
    print "number of frames:", NFrames
    if NSlices == 1 and NFrames != 1:
        return True
    elif NSlices != 1 and NFrames == 1:
        return False
    else:
        print "stack dimension error!"
        

def findAndFit(noise, pxsize):      #might not be a bad idea to have optional inputs here as tags...
    imp = IJ.getImage()
    stack = imp.getImageStack()
    IJ.run("Find Maxima...", "noise=" + str(noise) + " output=[Point Selection] exclude")
    #add something here for the user to review the maxima? make interactive?
    # could also do some looping to make sure there are the right number of beads in 
    # the FOV (would have to add instructions for users to crop appropriately)
    if isFrames(imp):
        stacksize = imp.getNFrames()
    else:
        stacksize = imp.getNSlices()

    xtimepoints = []
    ytimepoints = []
    
    
    for i in range(stacksize):
        #get imageprocessor for the working slice
        ip = stack.getProcessor(i+1)
        #do the fit for the working slice
        IJ.run("GaussFit OnSpot", "shape=Circle fitmode=[Levenberg Marquard] rectangle=4 pixel=" + str(pxsize) + " max=500 cpcf=1 base=100")
        # use the function that will loop through the results table and grab all the values
        #values are returned as lists.  
        (XCs, YCs, numpoints) = getResultsXCsYCs()
        #now, we add the list of point values to the timepoint lists.  each of these lists
        # will contain an entry for each timepoint, containing a list of X or Y values
        # for each point.
        xtimepoints.append(XCs)
        ytimepoints.append(YCs)
        
    return xtimepoints, ytimepoints, numpoints
     

# now let's put it all together and report a standard deviation! 

#need to rethink what i actually want to report here - stdev doesn't work for 2d!
def stdev(s):
    average = sum(s)*1.0/len(s)
    variance = map(lambda x: (x-avg)**2, s)
    return math.sqrt(average(variance))


xtimepoints, ytimepoints, numpoints = findAndFit(10, 106)








        


    