#!/usr/bin/python

import numpy as np
import scipy as sp
import scipy.misc as sm
import skimage.filters
import random
import sys
from scipy.ndimage.morphology import binary_fill_holes
from scipy.ndimage.filters import gaussian_filter
import contour

# Read image
#img = sm.imread("tile2.png",flatten=True)
img = sm.imread("tile2.png")
img = img[:,:,0]
size = img.shape

imgcontour = np.zeros([size[0],size[1],3])
imgmark = np.zeros([size[0],size[1]],dtype=np.bool)

# Function to draw contour, marked drawn contour as used
def drawContour(contour):
    rcolor = random.randint(100,200)
    gcolor = random.randint(100,200)
    bcolor = random.randint(100,200)
    for py,px in contour:
        imgcontour[py,px] = [rcolor,gcolor,bcolor]
        imgmark[py,px] = True

    py,px = contour[0]
    imgcontour[py,px] = [rcolor-50,gcolor-50,bcolor-50]

    py,px = contour[-1]
    imgcontour[py,px] = [rcolor+50,gcolor+50,bcolor+50]
    
    return

# Function to check whether point is already used or not
def contourNotOverlap(contour):
    global imgmark
    imgtmp = np.zeros([size[0],size[1]],dtype=np.bool)
    for py,px in contour:
        # Break if a single point is already used
        if imgmark[py,px]:
            return False
        imgtmp[py,px] = True
    return True

# Run contour tracing
#contours = contour.trace(img)
contours = contour.load_contours("contour.dat")
# Contour evaluation

# Apply sobel filter to image
imgsobel = skimage.filters.sobel(img/255.)

for contour in contours:
    # Calculate mean gradient
    gsum = 0.
    for py,px in contour.contour:
        gsum = gsum + imgsobel[py,px]
    gmean = gsum/float(contour.length)

    # Calculate gradient fitting score
    gfit = 0.
    for py,px in contour.contour:
        window = imgsobel[py-1:py+2,px-1:px+2]
        mx,my = np.unravel_index(np.argmax(window),window.shape) # Do not change this line
        if my==1 and mx==1:
            gfit +=1.
    gfit = gfit/float(contour.length)
    contour.score = gfit*gmean

# Sort contours based on score
contours = sorted(contours,key=lambda x:x.score,reverse=True)

# Mark contour
f = open("contour_nonoverlap.dat",'w')
for contour in contours:
    if contourNotOverlap(contour.contour):
        drawContour(contour.contour)
        for py,px in contour.contour:
            f.write("%s %s," % (py,px))
        f.write("\n")
f.close()

#sm.imsave("imgsobel.png",imgsobel)
sm.imsave("imgcontour.png",imgcontour)
sm.imsave("imgmark.png",imgmark)
