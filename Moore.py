#!/usr/bin/python

# Snippet for contour tracing based on Moore-Neighbor algorithm
# http://www.imageprocessingplace.com/downloads_V3/root_downloads/tutorials/contour_tracing_Abeer_George_Ghuneim/moore.html
# Works on binary image. Background is False.

import numpy as np
import scipy.misc as sm
from scipy.spatial import ConvexHull
import sys
import random
import cutlinear

def shiftneighbour(my,mx,c):
    # Shift neighbourhood starting position
    mx = mx[c+5:]+mx[:c+5]
    my = my[c+5:]+my[:c+5]
    return my,mx

# Create clockwise neighbourhood, starts with north-west
mx = [-1,0,1,1,1,0,-1,-1]
my = [1,1,1,0,-1,-1,-1,0]


# Read binary image
#imgraw = np.memmap("img.raw",shape=(128,128),dtype=np.uint8,mode='r')
imgraw = sm.imread("sample/sample.png",flatten=True)
imgraw = imgraw < 10
sm.imsave("binary.png",imgraw)

print imgraw.shape
imgH,imgW = imgraw.shape
imgcon = np.zeros([imgH,imgW,3])


# Define maximum step
maxstep = 500

# Find starting point
s = False
for i in range(imgH):
    for j in range(imgW):
        if imgraw[i,j]:
            sy,sx = i,j
            s = True
            break
    if s:
        break

imgcon[sy,sx] = [200,200,200]
#print sy,sx

# Init main algorithm
py,px = sy,sx
wy,wx = sy,sx

# Stopping criterion
stop = False
step = 1
contour = [(sy,sx)]

while(step<maxstep and not stop):
    for c in range(8):
        # Rotate around p, clockwise
        cx = px + mx[c]
        cy = py + my[c]

        if not imgraw[cy,cx]:
            # Background;advance
            wy,wx = cy,cx
        else:
            # Foreground;backtrack 
#            imgcon[py,px] = True
            py,px = wy,wx
            contour.append((py,px))
            imgcon[py,px] = [200,200,200]
#            print py,px,step
    
            # Check if cx and cy returns to seed, with same direction as first step
            if cx == sx and cy == sy and mx[c] == -1 and my[c] == 1:
                stop = True

            # Shift neighbour when backtrack
            my,mx = shiftneighbour(my,mx,c)
            step = step + 1
            break



# Concave splitting starts here

# Find the convex hull that enclosed the contour
hull = ConvexHull(contour)
hv = hull.vertices

# Shift contour so that contour[0] matches vertices[0]
contour = contour[hv[0]:] + contour[:hv[0]] # Shift contour

# Create the vertex pairs
segments = [contour[hv[v]-hv[0]:hv[v+1]-hv[0]+1] for v in range(len(hv)-1)] + [contour[hv[-1]-hv[0]:]+[(contour[0])]]

consegments = []
for segment in segments:
    # Assign end-points
    if segment[0][0] < segment[-1][0]:
        (y1,x1),(y2,x2) = segment[0],segment[-1]
    else:
        (y1,x1),(y2,x2) = segment[-1],segment[0]

    # Calculate denominator
    dy,dx = float(y2-y1),float(x2-x1)
    dd = np.sqrt(dx**2 + dy**2)

    # Flag to determine if current segment is concave/vex or not
    flag = False

    imgcon[y2,x2] = [200,50,50] 
    imgcon[y1,x1] = [200,50,50] 

    points = []

    for (y0,x0) in segment[1:-1]:
        # Calculate the distance between the point and vector
        r = np.abs(dx*(y1-y0) - dy*(x1-x0))/dd

        # Skip if depth is not sufficient
        if r < 4.:
            continue

        flag = True
        points.append((y0,x0,r))

    if flag:
        # Calculate the angle 
        theta = np.arctan2(dy/dd,dx/dd)
        consegments.append((points,theta))
    
# Color em
for (points,theta) in consegments:
    for (y0,x0,r) in points:
        imgcon[y0,x0] = [50,200,200]

SCORE_THRESHOLD = 0.7

# Match the consegments for possible cross-cut
for i in range(len(consegments)):
    for j in range(i+1,len(consegments)):
        conseg1,theta1 = consegments[i]
        conseg2,theta2 = consegments[j]

        # Calculate the angle score
        ascore = np.abs(theta1+theta2)/(2.*np.pi)
        scoremin = SCORE_THRESHOLD

        for y1,x1,d1 in conseg1:
            for y2,x2,d2 in conseg2:
                dy,dx = float(y2-y1),float(x2-x1)
                r = np.sqrt(dx**2 + dy**2)
                lscore = r/(r+d1+d2)
                score = (ascore+lscore)/2.
                # Find point with lowest score
                if score < scoremin:
                    scoremin = score
                    p1,p2 = (y1,x1),(y2,x2)
                    #print p1,p2,ascore,score
        
        # Todo: if score is enough
        if score < SCORE_THRESHOLD:
            print "Score",score
            # Color em
            rcolor,gcolor,bcolor = random.randint(50,150),random.randint(50,150),random.randint(50,150)
            imgcon[p1[0],p1[1]] = [rcolor,gcolor,bcolor] 
            imgcon[p2[0],p2[1]] = [rcolor,gcolor,bcolor]       

            # Draw the cutting line
            line = cutlinear.draw_line(p1,p2)
            for p in line:
                imgcon[p[1],p[0]] = [200*score,0,200*score]
        
sm.imsave("imgcon.png",imgcon)
