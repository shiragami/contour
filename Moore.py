#!/usr/bin/python

# Snippet for contour tracing based on Moore-Neighbor algorithm
# http://www.imageprocessingplace.com/downloads_V3/root_downloads/tutorials/contour_tracing_Abeer_George_Ghuneim/moore.html
# Input binary image. Background is False.

import numpy as np
import scipy.misc as sm
import sys

def shiftneighbour(my,mx,c):
    # Shift neighbourhood starting position
    mx = mx[c+5:]+mx[:c+5]
    my = my[c+5:]+my[:c+5]
    return my,mx

def contour_trace(imgbin):
    # Create clockwise neighbourhood, starts with north-west
    mx = [-1,0,1,1,1,0,-1,-1]
    my = [1,1,1,0,-1,-1,-1,0]

    imgH,imgW = imgbin.shape
    #imgcon = np.zeros([imgH,imgW,3])

    # Define maximum step
    maxstep = 500

    # Find starting point
    s = False
    for i in range(imgH):
        for j in range(imgW):
            if imgbin[i,j]:
                sy,sx = i,j
                s = True
                break
        if s:
            break

    #imgcon[sy,sx] = [200,200,200]

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

            if not imgbin[cy,cx]:
                # Background;advance
                wy,wx = cy,cx
            else:
                # Foreground;backtrack 
                py,px = wy,wx
                contour.append((py,px))
                #imgcon[py,px] = [200,200,200]
        
                # Check if cx and cy returns to seed, with same direction as first step
                if cx == sx and cy == sy and mx[c] == -1 and my[c] == 1:
                    stop = True

                # Shift neighbour when backtrack
                my,mx = shiftneighbour(my,mx,c)
                step = step + 1
                break

    return contour
