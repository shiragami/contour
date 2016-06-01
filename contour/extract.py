#!/usr/bin/python

import numpy as np
import scipy as sp
import scipy.misc as sm
import skimage.filters
import random
import sys
import subprocess
from scipy.ndimage.morphology import binary_fill_holes

# Read image
img = sm.imread("tile2.png",flatten=True)
#img = sm.imread("tile2.png")
#img = img[:,:,0]
size = img.shape

# Todo: Pass the image buffer through Python wrapper
# Write image as uint8
x = np.array(img,'uint8')
fo = open("img.raw",'wb')
x.tofile(fo)
fo.close()

# Normalize image for sobel filter
img = img/255.

imgcontour = np.zeros([size[0],size[1],3])
imgmark = np.zeros([size[0],size[1]],dtype=np.bool)

# Run tracing program
#cmd = ["./trace","img.raw",str(size[0]),str(size[1])]
#p = subprocess.call(cmd,stdout=subprocess.PIPE)


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

contour = []

#print "Total:",len(contour)


# Load contour
data = [l.strip() for l in open("contour.dat")]
for d in data:
    con = d.split(',')[:-1]
    con = [map(int,x.split()) for x in con]
    contour.append(con)



# Evaluate contour
"""
for con in contour[:]:
    l = len(con)
    px = np.array([int(c[0]) for c in con])
    py = np.array([int(c[1]) for c in con])
    xmin,xmax = min(px),max(px)
    ymin,ymax = min(py),max(py)
    
    py = py - ymin
    px = px - xmin

    print xmin,xmax,ymin,ymax
    imgbin = np.zeros([ymax-ymin+1,xmax-xmin+1],dtype=np.bool)

    for p in range(len(con)):
        imgbin[py[p],px[p]] = True

    imgbin = binary_fill_holes(imgbin)
    sm.imsave("imgbin.png",imgbin)

    imgcrop = img[ymin:ymax+1,xmin:xmax+1]
    sm.imsave("imgcrop.png",imgcrop)
"""

# Apply sobel filter to image
imgsobel = skimage.filters.sobel(img)

# Calculate mean gradient for each contour
score = [[i,0] for i in range(len(contour))]

for c,con in enumerate(contour):
    gsum = 0.
    for py,px in con:
        gsum = gsum + imgsobel[py,px]
    gmean = gsum/float(len(con))

    gfit = 0.
    for py,px in con:
        window = imgsobel[py-1:py+2,px-1:px+2]
        mx,my = np.unravel_index(np.argmax(window),window.shape) # Do not change this line
        if my==1 and mx==1:
            gfit +=1.
    gfit = gfit/float(len(con))

    score[c][1] = gfit*gmean

# Sort score
score = sorted(score,key=lambda x:x[1],reverse=True)

print len(contour)

# Mark contour
f = open("contour_nonoverlap.dat",'w')
for s in score:
    flag = contourNotOverlap(contour[s[0]])
    if flag:
        drawContour(contour[s[0]])
        for py,px in contour[s[0]]:
            f.write("%s %s," % (py,px))
        f.write("\n")
f.close()

#sm.imsave("imgsobel.png",imgsobel)
sm.imsave("imgcontour.png",imgcontour)
sm.imsave("imgmark.png",imgmark)
