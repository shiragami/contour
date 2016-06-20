#!/usr/bin/python
import numpy as np
import subprocess
import sys
from scipy.ndimage.filters import gaussian_filter
from scipy.ndimage.morphology import binary_fill_holes,distance_transform_cdt
from scipy.spatial import ConvexHull

# Concave splitting parameters
DEPTH_THRESHOLD = 5.0
SCORE_THRESHOLD = 0.7

# Contour optimization parameter
DISTANCE_THRESHOLD = 7

class Contour:
    def __init__(self,contour):
        self.contour = contour
        self.length  = len(contour)

        # Set the contour location and shape
        px = [p[1] for p in contour]
        py = [p[0] for p in contour]

        self.x,self.y = np.min(px),np.min(py)
        self.x2,self.y2 = np.max(px),np.max(py)

        self.height = self.y2 - self.y + 1
        self.width  = self.x2 - self.x + 1

        self.img = None
        self.area = 0

        self.child = None
        self.score = 0
        self.flag = True
   
    # Create the binary image of enclosed contour
    def fill_holes(self):
        self.img = np.zeros([self.height,self.width],dtype=np.bool)
        for py,px in self.contour:
            self.img[py-self.y,px-self.x] = True
        self.img = binary_fill_holes(self.img)
        self.area = np.sum(self.img)

# Function to trace contour on given grayscale image
def trace(img):
    # Todo: Pass the image buffer through Python wrapper
    # Write image as uint8
    x = np.array(gaussian_filter(img,sigma=1.0),'uint8')
    fo = open("img.raw",'wb')
    x.tofile(fo)
    fo.close()

    size = img.shape

    cmd = ["./trace","img.raw",str(size[0]),str(size[1])]
    p = subprocess.call(cmd,stdout=subprocess.PIPE)
    return load_contours("contour.dat")

# Function to load contour from dat file
# Return a list of contour class
def load_contours(filename):
    contours = []
    data = [l.strip() for l in open(filename)]
    for d in data:
        con = d.split(',')[:-1]
        con = [tuple(map(int,x.split())) for x in con]
        c = Contour(con)
        contours.append(c)
    return contours

# Check if bounding box of contour1 is enclosed by bounding box of contour2
def check_box_enclosed(c1,c2):
    if c1.x > c2.x and c1.x2 < c2.x2 and c1.y > c2.y and c1.y2 < c2.y2:
        return True
    else:
        return False

# Bresenham's Line Algorithm
# http://www.roguebasin.com/index.php?title=Bresenham%27s_Line_Algorithm#Python
# Input: point list(y,x)
def draw_line(p1, p2):
    # Setup initial conditions
    y1,x1 = p1
    y2,x2 = p2
    dx,dy = x2-x1 , y2-y1
 
    # Determine how steep the line is
    is_steep = abs(dy) > abs(dx)
 
    # Rotate line
    if is_steep:
        x1, y1 = y1, x1
        x2, y2 = y2, x2
 
    # Swap start and end points if necessary and store swap state
    swapped = False
    if x1 > x2:
        x1, x2 = x2, x1
        y1, y2 = y2, y1
        swapped = True
 
    # Recalculate differentials
    dx,dy = x2-x1, y2-y1
 
    # Calculate error
    error = int(dx/2.0)
    ystep = 1 if y1 < y2 else -1
 
    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (x, y) if is_steep else (y, x)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx
 
    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points

# Recursive function to split contours
# This function is called by split_concave
def split(contour,lcontour=[],pa=None,pb=None):
    # Prevent convex error
    if len(contour) < 3:
        return []

    # Find the convex hull that enclosed the contour
    hull = ConvexHull(contour)
    hv = sorted(hull.vertices) # Fuck this bug

    # Create the vertex pairs
    segments = [contour[hv[v]:hv[v+1]+1] for v in range(len(hv)-1)] + [contour[hv[-1]:] + contour[:hv[0]+1]]

    consegments = []

    for segment in segments:
        # Assign end-points. x2 must > x1
        if segment[0][0] < segment[-1][0]:
            (y1,x1),(y2,x2) = segment[0],segment[-1]
        else:
            (y1,x1),(y2,x2) = segment[-1],segment[0]

        # Calculate denominator
        dy,dx = float(y2-y1),float(x2-x1)
        dd = np.sqrt(dx**2 + dy**2)

        # Flag to determine if current segment is concave/vex or not
        flag = False
        points = []

        for (y0,x0) in segment[1:-1]:
            # Calculate the distance between the point and vector
            r = np.abs(dx*(y1-y0) - dy*(x1-x0))/dd

            # Skip if depth is not sufficient
            if r < DEPTH_THRESHOLD:
                continue

            flag = True
            points.append((y0,x0,r))

        if flag:
            # Calculate the angle 
            theta = np.arctan2(dy,dx)
            theta = -theta if dy*(x0-x1) + y1*dx > y0*dx else theta
            consegments.append((points,theta))
        
    minscore = SCORE_THRESHOLD

    # Match the consegments for possible cut
    for i in range(len(consegments)):
        for j in range(i+1,len(consegments)):
            conseg1,theta1 = consegments[i]
            conseg2,theta2 = consegments[j]

            # Calculate the angle score
            ascore = np.abs(theta1+theta2)/(2.*np.pi)
            for y1,x1,d1 in conseg1:
                for y2,x2,d2 in conseg2:
                    dy,dx = float(y2-y1),float(x2-x1)
                    r = np.sqrt(dx**2 + dy**2)
                    lscore = r/(r+d1+d2)
                    score = (ascore+lscore)/2.

                    # Update the lowest score
                    if score < minscore:
                        minscore = score
                        p1,p2 = (y1,x1),(y2,x2)

    if minscore < SCORE_THRESHOLD:
        # Prevent infinite recursion
        if p1==pa and p2==pb:
            return []

        # Split contour into two parts #
        # Draw the cutting line
        line = draw_line(p1,p2)
        
        # Find index of point in contour
        s1,s2 = contour.index(p1),contour.index(p2)
        
        # Split and stitch
        if s2 > s1:
            c1 = contour[s1+1:s2] + line[::-1]
            c2 = contour[:s1] + line[:] + contour[s2+1:]
        else:
            c1 = contour[s2+1:s1] + line[:]
            c2 = contour[:s2] + line[::-1] + contour[s1+1:]

        # Recursive call
        split(c1,lcontour,p1,p2)
        split(c2,lcontour,p1,p2)
    else:
        # Stop if no split candidates
        lcontour.append(Contour(contour))
        return []
    
    return lcontour    

# Main function for concave splitting
# Input : List of contours
# Output: List of splitted contours
def split_concave(contours):
    newcontours=[]
    for contour in contours:
        scontours = split(contour.contour,lcontour=[])
        if bool(scontours):
            newcontours = newcontours + scontours
        else:
            newcontours.append(contour)
    return newcontours

# Function to remove filament/bump from contours
# Input: List of contour class. (Holes filled)
def optimize_contour(contours):
    for contour in contours:
        # Compute the chamfer distance transform
        imgpad = np.zeros([contour.height+2,contour.width+2],dtype=np.bool)
        imgpad[1:contour.height+1,1:contour.width+1] = contour.img
        imgdis = distance_transform_cdt(imgpad,metric='taxicab')

        for d in range(DISTANCE_THRESHOLD-1,0,-1):
            for i in range(1,contour.height+1):
                for j in range(1,contour.width+1):
                    d0 = imgdis[i][j]
                    if d0 != d:
                        continue
                    d1 = imgdis[i+1,j]
                    d2 = imgdis[i,j+1]
                    d3 = imgdis[i-1,j]
                    d4 = imgdis[i,j-1]

                    if d1 <= d and d2 <= d and d3 <=d and d4 <=d:
                        imgdis[i][j] = d-1

            for i in range(contour.height+2):
                for j in range(contour.width+2):
                    if imgdis[i][j] <= 0:
                        imgpad[i][j] = False
        contour.img = imgpad[1:contour.height+1,1:contour.width+1]
    return contours

# Dump a list of contour to file
def dump_contour(filename,contours):
    fo = open(filename,'w')
    for contour in contours:
        for p in contour.contour:
            fo.write("%s %s," % p)
        fo.write("\n")
    fo.close()

