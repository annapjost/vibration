from ij import IJ, ImagePlus, ImageStack
from ij import WindowManager as WM
from ij.gui import Plot as Plot
from ij.gui import PlotWindow as PlotWindow
from ij.io import OpenDialog
from ij.measure import ResultsTable
from fiji.util.gui import GenericDialogPlus
from ij.gui import GenericDialog
from os import path
import math

def getNoiseTolerance():
    gd = GenericDialogPlus('set parameters')
    gd.addStringField('noise tolerance: ', None)
    gd.showDialog()
    noise = gd.getNextString()
    return noise

def dialog(title, field):
    gd = GenericDialogPlus(title)
    gd.addStringField(field, None)
    gd.showDialog()
    output = gd.getNextString()
    return output

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

def getCal(imp):
    imp = IJ.getImage()
    cal = imp.getCalibration()
    if cal.unit == 'pixel':
        return False
    else:
        scale = cal.pixelWidth*1000
        return scale            
        
def findApproveMaxima(imp):
    gd = GenericDialogPlus('noise tolerance')
    gd.addStringField('starting noise tolerance: ', None)
    gd.showDialog()
    noise = gd.getNextString()
    IJ.run("Find Maxima...", "noise=" + str(noise) + " output=[Point Selection] exclude")
    approved = False
    while approved == False:
        gd = GenericDialog('confirm noise tolerance')
        gd.addMessage('are you happy with maxima?')
        gd.enableYesNoCancel()
        gd.showDialog()
        if gd.wasOKed():
            return noise
            approved = True
        elif gd.wasCanceled():
            print "canceled"
            return False
        else:
            gd = GenericDialogPlus('enter new noise tolerance')
            gd.addStringField('new noise tolerance: ', str(noise))
            gd.showDialog()
            noise = gd.getNextString()
            IJ.run("Find Maxima...", "noise=" + str(noise) + " output=[Point Selection] exclude")

def findAndFit(noise, scale):      #might not be a bad idea to have optional inputs here as tags...
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
    
    
    for slice in range(stacksize):
        #set working slice
        imp.setSlice(slice)
        #do the fit for the working slice
        IJ.run("GaussFit OnSpot", "shape=Circle fitmode=[Levenberg Marquard] rectangle=4 pixel=" + str(scale) + " max=500 cpcf=1 base=100")
        # use the function that will loop through the results table and grab all the values
        #values are returned as lists.  
        (XCs, YCs, numpoints) = getResultsXCsYCs()
        #now, we add the list of point values to the timepoint lists.  each of these lists
        # will contain an entry for each timepoint, containing a list of X or Y values
        # for each point.
        xtimepoints.append(XCs)
        ytimepoints.append(YCs)
        
    return xtimepoints, ytimepoints, numpoints
     

# define some necessary math functions 

def average(x):
    average = sum(x)*1.0/len(x)
    return average

def stdev(s):
    avg = sum(s)*1.0/len(s)
    variance = map(lambda x: (x-avg)**2, s)
    return math.sqrt(average(variance))
    

#noise = getNoiseTolerance()

imp = IJ.getImage()

scale = getCal(imp)
if scale == False:
    gd = GenericDialogPlus('set scale')
    gd.addStringField('pixel size (nm): ', None)
    gd.showDialog()
    scale = gd.getNextString()

noise = findApproveMaxima(imp)
xtimepoints, ytimepoints, numpoints = findAndFit(noise, scale)
print numpoints

x = []
y = []

# plot all points
for i in xtimepoints:
    for j in range(numpoints):
        x.append(i[j])

for k in ytimepoints:
    for l in range(numpoints):
        y.append(k[l])

plot = Plot("summary", "xc", "yc", [], [])

#plot.setColor(Color.BLACK)
plot.addPoints(x, y, Plot.CIRCLE)
plot_window = plot.show()

# reorganize the lists:

allpointsx = []

for point in range(numpoints):
    points = []
    for time in range(len(xtimepoints)):
        current = xtimepoints[time]
        points.append(current[point])   
    allpointsx.append(points)
print allpointsx

allpointsy = []

for point in range(numpoints):
    points = []
    for time in range(len(ytimepoints)):
        current = ytimepoints[time]
        points.append(current[point])   
    allpointsy.append(points)    
print allpointsy

def plotPoint(allpointslist, xory, point):
    plot = Plot(xory + " position " + str(point), "timepoint", "position (nm)", [], [])
    plot.addPoints(range(len(allpointslist[point])), allpointslist[point], Plot.LINE)
    plot_window = plot.show()

plotPoint(allpointsx, "x", 1)
plotPoint(allpointsy, "y", 1)
#now, allpoints is a list of points.  each entry contains every timepoint for that point.

# do this a sort of crappy way for now - stdev in x and in y separately. 
xstdevs = []
ystdevs = [] 

for point in range(numpoints):
    std = stdev(allpointsx[point])
    xstdevs.append(std)
    
for point in range(numpoints):
    std = stdev(allpointsy[point])
    ystdevs.append(std)


avgxstdev = average(xstdevs)
avgystdev = average(ystdevs)

print avgxstdev
print avgystdev


#trying to make this work to measure distances from the centroid for each point over time...
'''
def distanceFromCentroid(x, y):
    centroid = [average(x), average(y)]
    xy = [ (b,c) for b in x for c in y]
    xdiffs = [ (b**2) for b in x ]
    ydiffs = [ (c**2) for c in y ]
    sums = [ (b**2 + c**2) for b in xdiffs for c in ydiffs ] 
    distances = [ sqrt(d) for d in sums ]
    distance = average(distances)
    return distance
        


averages = []

for point in range(numpoints):
    distances = []
    distance = distanceFromCentroid(allpointsx[point], allpointsy[point])
    distances.append(distance)
    avg = average(distance)
    averages.append(avg)
    
print averages
    
'''
    
    
    