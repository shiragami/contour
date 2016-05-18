#!/usr/bin/python

# Snippet for contour tracing based on Moore-Neighbor algorithm
# http://www.imageprocessingplace.com/downloads_V3/root_downloads/tutorials/contour_tracing_Abeer_George_Ghuneim/moore.html
# Works on binary image. Background is False.

import numpy as np
import scipy.misc as sm
from scipy.spatial import ConvexHull
import random
import cutlinear
import Moore
import sys

DEPTH_THRESHOLD = 4.0
SCORE_THRESHOLD = 0.6
imgcon = np.zeros([100,100,3])

count = 0

def drawcontour(contour,c):
    imgc = np.zeros([100,100,3])
    fname = "imgcontour%s.png" % "{0:02d}".format(c)

    for y,x in contour:
        imgc[y,x] = [200,100,200]

    sm.imsave(fname,imgc)

    return

# Split contour from a given 2 points 
def splitcontour(contour,p1,p2):
    # Draw the line
    line = cutlinear.draw_line(p1,p2)

    # Find index of point in contour
    s1,s2 = contour.index(p1),contour.index(p2)

    # Split and stitch

    if s2 > s1:
        c1 = contour[s1+1:s2] + line[::-1]
        c2 = contour[:s1] + line[:] + contour[s2+1:]
    else:
        c1 = contour[s2+1:s1] + line[:]
        c2 = contour[:s2] + line[::-1] + contour[s1+1:]

    return c1,c2


def splitconcave(contour,lcontour=[]):
    global count

    # Find the convex hull that enclosed the contour
    hull = ConvexHull(contour)
    hv = sorted(hull.vertices) # Fuck this bug

    # Create the vertex pairs
    segments = [contour[hv[v]:hv[v+1]+1] for v in range(len(hv)-1)] + [contour[hv[-1]:] + contour[:hv[0]+1]]

    consegments = []

    for segment in segments:
        #print len(segment)
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

        imgcon[y2,x2] = [200,50,50] 
        imgcon[y1,x1] = [200,50,50] 

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
            theta = -theta if dy/dx*(x0-x1) + y1 > y0 else theta
#            print y0,x0
#            print "angle",theta
            consegments.append((points,theta))
        
    # Color em
    for (points,theta) in consegments:
        for (y0,x0,r) in points:
            imgcon[y0,x0] = [50,200,200]

    minscore = SCORE_THRESHOLD

    # Todo:theta is wrong. Check muki

    # Match the consegments for possible cut
    for i in range(len(consegments)):
        for j in range(i+1,len(consegments)):
            conseg1,theta1 = consegments[i]
            conseg2,theta2 = consegments[j]

            # Calculate the angle score
            ascore = np.abs(theta1+theta2)/(2.*np.pi)
            #print theta1,theta2
            for y1,x1,d1 in conseg1:
                for y2,x2,d2 in conseg2:
                    dy,dx = float(y2-y1),float(x2-x1)
                    r = np.sqrt(dx**2 + dy**2)
                    lscore = r/(r+d1+d2)
                    score = (ascore+lscore)/2.
                    # Find point with lowest score
                    if score < minscore:
                        minscore = score
                        p1,p2 = (y1,x1),(y2,x2)
                       #print p1,p2,ascore,score

    if minscore < SCORE_THRESHOLD:
        print "Score",minscore
        # Color em
        rcolor,gcolor,bcolor = random.randint(50,150),random.randint(50,150),random.randint(50,150)
        imgcon[p1[0],p1[1]] = [rcolor,gcolor,bcolor] 
        imgcon[p2[0],p2[1]] = [rcolor,gcolor,bcolor]       

        # Draw the cutting line
        line = cutlinear.draw_line(p1,p2)
        for p in line:
            imgcon[p[0],p[1]] = [200*score,0,200*score]


        # Split contour into two
        c1,c2 = splitcontour(contour,p1,p2)

        #drawcontour(c1,count)
        #count+=1    
        #drawcontour(c2,count)
        #count+=1    

        # Recursive call
        splitconcave(c1,lcontour)
        splitconcave(c2,lcontour)
    else:
        lcontour.append(contour)
        return
    
    return lcontour    

# Main function starts here


# Read image
imgbin = sm.imread("sample/sample.png",flatten=True) < 10
sm.imsave("binary.png",imgbin)

contour = Moore.contour_trace(imgbin)
for py,px in contour:
    imgcon[py,px] = [200,200,200]

contours = splitconcave(contour)

for c,contour in enumerate(contours):
    drawcontour(contour,c)

# Color em
#for segment in segments:
#    rcolor,gcolor,bcolor = random.randint(50,150),random.randint(50,150),random.randint(50,150)
#    for y0,x0 in segment[1:-1]:
#        imgcon[y0,x0] = [rcolor,gcolor,bcolor]

#for v in hv:
#    y0,x0 = contour[v]
#sm.imsave("imgcon.png",imgcon)

        
sm.imsave("imgcon.png",imgcon)
