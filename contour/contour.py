#!/usr/bin/python
import numpy as np
import subprocess
import sys
import random
from scipy.ndimage.filters import gaussian_filter
from scipy.ndimage.morphology import binary_fill_holes,distance_transform_cdt
from scipy.spatial import ConvexHull
import scipy.misc as sm

# Concave splitting parameters
DEPTH_THRESHOLD = 5.0
SCORE_THRESHOLD = 0.7
DIAMETER_RATIO = 0.5

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

        self.child = []
        self.parent = None
        self.score = 0
        self.flag = True

        self.gy = np.mean(py)
        self.gx = np.mean(px)

        self.tag = 0

    # Create the binary image of enclosed contour
    def fill(self):
        self.img = np.zeros([self.height,self.width],dtype=np.bool)
        for py,px in self.contour:
            self.img[py-self.y,px-self.x] = True
        self.img = binary_fill_holes(self.img)
        self.area = np.sum(self.img)
    
    def downscale(self,scale):
        newcontour = []
        for py,px in self.contour:
            point = (py/scale,px/scale)
            if point not in newcontour:
                newcontour.append(point)
        self.contour = newcontour
        self.length  = len(newcontour)

        self.gx,self.gy = self.gx/float(scale),self.gy/float(scale)
        self.x,self.y = self.x/scale,self.y/scale
        self.height = self.y2 - self.y + 1
        self.width  = self.x2 - self.x + 1

        self.fill()

        return

# Function to trace contour on given grayscale image
def trace(img,minlen=100,maxlen=700):
    # Todo: Pass the image buffer through Python wrapper
    # Write image as uint8
    x = np.array(gaussian_filter(img,sigma=1.0),'uint8')
    fo = open(".img.raw",'wb')
    x.tofile(fo)
    fo.close()

    size = img.shape

    cmd = ["/home/tk2/Desktop/nucleisegmentation/contour/trace",".img.raw",str(size[0]),str(size[1]),str(minlen),str(maxlen)]
    p = subprocess.call(cmd,stdout=subprocess.PIPE)
    return load(".contour.dat")

# Function to load contour from dat file
# Return a list of contour class
def load(filename):
    contours = []
    datas = [l.strip() for l in open(filename)]
    
    header = datas[0]
    tagged = False
    # Check if header exist
    if header[0] == '#':
        header = header[1:].split(" ") 
        length = int(header[0])
        tagged = True if header[1]=='1' else False

        if tagged:
            tags  = datas[length+1:]
            datas = datas[1:length+1]

            if len(datas) != len(tags):
                print "Tag mismatch %s %s"  % (len(datas),len(tags))
                sys.exit()
        else:
            datas = datas[1:]


    for d,data in enumerate(datas):
        if len(data) == 0:
            continue
        con = data.split(',')[:-1]
        con = [tuple(map(int,x.split())) for x in con]
        c = Contour(con)
        if tagged:
            c.tag = tags[d]
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

        # Draw the cutting line
        line = draw_line(p1,p2)

        # Cutting line thresholding
        if len(line)*np.pi > DIAMETER_RATIO*len(contour):
            if len(consegments) != 2: # Split anyway if there's only 2 curve points
                lcontour.append(Contour(contour))
                return []

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
def dump_contour(filename,contours,tag=False):

    # Remove zero contour
    # I use len instead of contour.length for safety
    contours = [c for c in contours if len(c.contour)!=0]

    fo = open(filename,'w')

    # Write header
    t = 1 if tag else 0
    header = "#%s %s\n" % (len(contours),t)
    fo.write(header)

    for contour in contours:
        for p in contour.contour:
            fo.write("%s %s," % p)
        fo.write("\n")

    if tag:
        for contour in contours:
            fo.write("%s\n" % contour.tag) 

    fo.close()

# Remove overlapping contours based on score
def remove_overlapping_contour(contours,size):
    imgmark = np.zeros([size[0],size[1]],dtype=np.bool)

    for contour in contours:
        flag = True
        for py,px in contour.contour:
            # Break if a single point is already used
            if imgmark[py,px]:
                flag = False
                break
        if flag:
            # Mark contour
            for py,px in contour.contour:
                imgmark[py,px] = True
        else:
            contour.flag = False

    # Filter out overlapped contours
    return [c for c in contours if c.flag]

# Function to draw contour on RGB image
def draw_contour(contours,imgRGB,color=None):
    imgRGB = imgRGB[:,:,:]
    # If color not specified use best contrast
    if color is None:
        pr,pg,pb = np.mean(imgRGB[:,:,0]),np.mean(imgRGB[:,:,1]),np.mean(imgRGB[:,:,2])
        for contour in contours:
            for py,px in contour.contour:
                imgRGB[py,px] = [255-pr,255-pg,255-pb]
    elif color == 'random':
        for contour in contours:
            pr,pg,pb = random.randint(75,100),random.randint(75,100),random.randint(75,100)
            for py,px in contour.contour:
                imgRGB[py,px] = [pr,pg,pb]
    else:
        for contour in contours:
            for py,px in contour.contour:
                imgRGB[py,px] = color
                
    return imgRGB

# Function to stitch non-connected contours
def stitch(contour):
    scontour = contour + [contour[0]] # Connect head to tail
    contour = []

    NPOINT = len(scontour)
    for p in range(NPOINT-1):
        p1,p2 = scontour[p],scontour[p+1]

        if p1[0]==p2[0] and p1[1]==p2[1]:
            continue

        if abs(p1[0]-p2[0])>1 or abs(p1[1]-p2[1])>1:
            line = draw_line(p1,p2)
            contour  = contour + line[:-1]
        else:
            contour  = contour + [p1]

    return contour


# Dump the contours as label image
# Useful for manual tagging later
# Not to be confused with contour.tag
def dump_label(filename,contours,size):
    imglabel = np.zeros(size,dtype=np.int32)

    # Label hack
    for c,contour in enumerate(contours):
        # Set overlapping region to zero
        imglabel[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width] *= ~contour.img
        # Append new label
        imglabel[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width] += (contour.img)*(c+1)

    fo = open(filename,'wb')
    imglabel.tofile(fo)
    fo.close()

# Function to calculate contour uniformity?
def calc_std(contour):
    sy = np.array([c[0] for c in contour.contour])
    sx = np.array([c[1] for c in contour.contour])
    
    sy = (sy-contour.gy)**2
    sx = (sx-contour.gx)**2

    dd = np.sqrt(sy + sx)

    std = np.std(dd)/np.mean(dd)
    return 
