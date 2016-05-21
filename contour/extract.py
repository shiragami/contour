#!/usr/bin/python

import numpy as np
import scipy as sp
import scipy.misc as sm
import skimage.filters
import random
import sys

# Read image
img = sm.imread("tile2.png",flatten=True)
size = img.shape

# Write image as uint8
x = np.array(img,'uint8')
fo = open("img.raw",'wb')
x.tofile(fo)
fo.close()

# Normalize image for sobel filter
img = img/255.

imgcontour = np.zeros([size[0],size[1],3])
imgmark = np.zeros([size[0],size[1]],dtype=np.bool)

def drawContour(contour):
    rcolor = random.randint(100,200)
    gcolor = random.randint(100,200)
    bcolor = random.randint(100,200)
    for px,py in contour:
        imgcontour[int(py),int(px)] = [rcolor,gcolor,bcolor]
        imgmark[int(py),int(px)] = True

    px,py = contour[0]
    imgcontour[int(py),int(px)] = [rcolor-50,gcolor-50,bcolor-50]

    px,py = contour[-1]
    imgcontour[int(py),int(px)] = [rcolor+50,gcolor+50,bcolor+50]
    
    return

# Function to check whether point is already used or not
def contourNotOverlap(contour):
    for px,py in contour:
        # Break if a single point is already used
        if imgmark[int(py),int(px)]:
            return False
    return True

contour = []
data = [l.strip() for l in open("data.dat")]
#spaces = [i for i in range(len(data)) if data[i]=='']

#contour.append(data[:spaces[0]+1])
#for s in range(len(spaces)-1):
#    contour.append(data[spaces[s]+1:spaces[s+1]])
#contour.append(data[spaces[-1]:])

#print contour

#print "Total:",len(contour)


# Load contour
data = [l.strip() for l in open("data.dat")]
for d in data:
    con = d.split(',')[:-1]
    con = [x.split() for x in con]
    contour.append(con)


#for c in contour[:10]:


# Evaluate contour


# Apply sobel filter to image
imgsobel = skimage.filters.sobel(img)
#print np.min(imgsobel),np.max(imgsobel)

# Calculate mean gradient for each contour
score = [[i,0] for i in range(len(contour))]

for c,con in enumerate(contour):
    gsum = 0.
    for px,py in con:
        gsum = gsum + imgsobel[int(py),int(px)]
    gmean = gsum/float(len(con))

    gfit = 0.
    for px,py in con:
        py,px = int(py),int(px)
        window = imgsobel[py-1:py+2,px-1:px+2]
        my,mx = np.unravel_index(np.argmax(window),window.shape)
        if my==1 and mx==1:
            gfit +=1.
    gfit = gfit/float(len(con))

    score[c][1] = gfit*gmean

# Sort score
score = sorted(score,key=lambda x:x[1],reverse=True)

# Mark contour
for s in score[:]:
    if contourNotOverlap(contour[s[0]]):
        drawContour(contour[s[0]])


#print imgmark

#sm.imsave("imgsobel.png",imgsobel)
sm.imsave("imgcontour.png",imgcontour)
