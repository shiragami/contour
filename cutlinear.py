#!/usr/bin/python

import numpy as np
import random
import scipy.misc as sm

# Bresenham's Line Algorithm
# http://www.roguebasin.com/index.php?title=Bresenham%27s_Line_Algorithm#Python
# Input: point tuple(y,x)
def draw_line(p1, p2):

    # Setup initial conditions
    y1, x1 = p1
    y2, x2 = p2
    dx = x2 - x1
    dy = y2 - y1
 
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
    dx = x2 - x1
    dy = y2 - y1
 
    # Calculate error
    error = int(dx / 2.0)
    ystep = 1 if y1 < y2 else -1
 
    # Iterate over bounding box generating points between start and end
    y = y1
    points = []
    for x in range(x1, x2 + 1):
        coord = (y, x) if is_steep else (x, y)
        points.append(coord)
        error -= abs(dy)
        if error < 0:
            y += ystep
            error += dx
 
    # Reverse the list if the coordinates were swapped
    if swapped:
        points.reverse()
    return points


# Init image

img = np.zeros([100,100,3])

# Create two random points
x1,y1 = random.randint(0,99),random.randint(0,99)
x2,y2 = random.randint(0,99),random.randint(0,99)


line = draw_line((y1,x1),(y2,x2))
for p in line:
    #print p
    img[p[1],p[0]] = [200,0,200]

img[y1,x1] = [0,200,200]
img[y2,x2] = [0,200,200]

# Create linear lines between these two
"""
if x1 == x2:
    print "Alamak"
elif x2 > x1:
    m = float(y2-y1)/float(x2-x1)
    c = y1 - m*x1
    for x in range(x1+1,x2):
        print x,x*m + c
        y = int(x*m + c)
        img[y,x] = [200,0,200]
        
else:
    for x in range(x2+1,x1):
        print x
"""

sm.imsave("imglinear.png",img)
