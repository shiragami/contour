#!/usr/bin/python
# Function to split concave
# Input: contour
# Output: list of splitted contour

import contour as cont
import numpy as np
import random
import scipy.misc as sm
import sys
from scipy.spatial import ConvexHull

DEPTH_THRESHOLD = 5.0
SCORE_THRESHOLD = 0.7

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
# Return a list of contour
def split_concave(contour,lcontour=[],pa=None,pb=None):
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
        split_concave(c1,lcontour,p1,p2)
        split_concave(c2,lcontour,p1,p2)
    else:
        # Stop if no split candidates
        lcontour.append(cont.Contour(contour))
        return []
    
    return lcontour    

# Main function starts here

imgcon = np.zeros([1024,1024,3])
contours = cont.load_contours("contour_nonoverlap.dat")

newcontours=[]
for contour in contours:
    scontours = cont.split_concave(contour.contour,lcontour=[])
    if bool(scontours):
        rcolor,gcolor,bcolor = random.randint(50,150),random.randint(50,150),random.randint(50,150)
        newcontours = newcontours + scontours
        for scontour in scontours:
            for py,px in scontour.contour:
                 imgcon[py,px] = [rcolor,gcolor,bcolor]
    else:
        newcontours.append(contour)
        for py,px in contour.contour:
             imgcon[py,px] = [100,100,100]

for contour in newcontours:
    print contour.x


sm.imsave("imgcon.png",imgcon)
