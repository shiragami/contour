#!/usr/bin/python

import numpy as np
import scipy as sp
import scipy.misc as sm
import skimage.filters
import random
import sys
from scipy.ndimage.filters import gaussian_filter
import contour as cont

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
#contours = cont.trace(img)
contours = cont.load_contours("contour.dat")

# Contour evaluation
print "Contour evaluation"
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

print "Removing overlapping contour"
# Mark contour
# Todo: Convert this part into a function
for contour in contours:
    if contourNotOverlap(contour.contour):
        drawContour(contour.contour)
    else:
        contour.flag = False

# Filter out overlapped contours
contours = [c for c in contours if c.flag]

# Contour splitting
print "Splitting contours"
contours = cont.split_concave(contours)

# Fill holes
for contour in contours:
    contour.fill_holes()

# Sort contour by area
contours = sorted(contours,key=lambda x:x.area)

print "Grouping contours"

# Group enclosed contours together 
Ncontours = len(contours)
for i in range(Ncontours-1):
    ci = contours[i]
    for j in range(Ncontours-1,i,-1):
        cj = contours[j]
        if cont.check_box_enclosed(ci,cj):
            # Crop boxj
            py,px = ci.y-cj.y,ci.x-cj.x
            ch,cw = ci.img.shape
            imgtmp = cj.img[py:py+ch,px:px+cw]

            # Calculate ci.img U imgtmp
            if np.sum(ci.img & imgtmp) > 0:
                cj.child.append(ci)
                break

img = np.zeros([1024,1024,3])
       
# Filter out contours with no child
contours = [c for c in contours if bool(c.child)]

for contour in contours:
#    if bool(contour.child):
#        if contour.score < np.max([c.score for c in contour.child]):
#            continue

    rcolor,gcolor,bcolor = random.randint(50,150),random.randint(50,150),random.randint(50,150)
    for py,px in contour.contour:
        img[py,px] = [rcolor,gcolor,bcolor]
    """
    for child in contour.child:
        print " ",child.score
        for py,px in child.contour:
            img[py,px] = [128,128,128]
    """
sm.imsave("imgcontour2.png",img)

#sm.imsave("imgsobel.png",imgsobel)
sm.imsave("imgcontour.png",imgcontour)
sm.imsave("imgmark.png",imgmark)
