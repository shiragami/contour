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

# Run contour tracing
#contours = contour.trace(img)
contours = contour.load_contours("contour.dat")

# Normalize image for sobel filter
img = img/255.

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




# Load contour
"""
data = [l.strip() for l in open("contour.dat")]
for d in data:
    con = d.split(',')[:-1]
    con = [map(int,x.split()) for x in con]
    contour.append(con)
    #c = Contour(con)
    #c.fill_holes()
    #contours.append(c)
print "Total:",len(contour)
"""

for contour in contours:
    print contour.x


sys.exit()

# Contour evaluation

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
