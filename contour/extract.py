#!/usr/bin/python

import contour as cont
import numpy as np
import random
import scipy as sp
import scipy.misc as sm
import skimage.filters
import sys
from scipy.ndimage.filters import gaussian_filter

# Read image
imgRGB = sm.imread("tile3.png")
img = imgRGB[:,:,0]
size = img.shape

# Run contour tracing
contours = cont.trace(img)
#contours = cont.load_contours(".contour.dat")

# Contour evaluation
print "Contour evaluation"
imgsobel = skimage.filters.sobel(img/255.)  # Apply sobel filter to image

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
contours = cont.remove_overlapping_contour(contours,size)

# Fill holes
for contour in contours:
    contour.fill_holes()

# Sort contour by area
contours = sorted(contours,key=lambda x:x.area,reverse=True)

print "Grouping contours"

# Group enclosed contours together 
# Select only largest child for speed
Ncontours = len(contours)
for i in range(Ncontours-1):
    ci = contours[i]
    # Skip contour that already has parent
    if not ci.flag:
        continue 
    for j in range(i+1,Ncontours):
        cj = contours[j]
        if cont.check_box_enclosed(cj,ci):
            # Crop boxi
            py,px = cj.y-ci.y,cj.x-ci.x
            ch,cw = cj.img.shape
            imgtmp = ci.img[py:py+ch,px:px+cw]

            # Calculate cj.img U imgtmp
            if np.sum(cj.img & imgtmp) > 0:
                if ci.child is None:
                    ci.child = cj
                # Flag contour - has parent
                cj.flag = False


# Select the most suitable contour from group
pcontours = [c for c in contours if c.child is not None]
contours = []
for contour in pcontours:
    # Try to split parent
    scontours = cont.split_concave([contour])
    if len(scontours) == 1:
        # Case no split. Select either parent/child, which has better circularity.
        # My assumption: Nuclei region has many contours groupe together. Need to pick the suitable one.

        # Calculate circularity
        cparent = float(contour.area)/float(contour.length**2)
        cchild  = float(contour.child.area)/float(contour.child.length**2)

        if cparent > cchild:
            contours.append(contour)
        else:
            contours.append(contour.child)
    else:
        for scontour in scontours:
            scontour.fill_holes()
            cchild  = float(scontour.area)/float(scontour.length**2)
            if cchild > 0.06:
                contours.append(scontour)
            
#print "Contour optimization"
# Remove small contours
contours = [c for c in contours if c.length > 100]
#contours = cont.optimize_contour(contours)

# Select contours with the right color features
for contour in contours:
    imgcrop = imgRGB[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
    imgcropR = np.ma.array(imgcrop[:,:,0],mask = np.invert(contour.img))
    imgcropB = np.ma.array(imgcrop[:,:,2],mask = np.invert(contour.img))
    #if np.mean(imgcropR) > np.mean(imgcropB):
    if np.mean(imgcropR) > 100:
        contour.flag = False
    else:
        contour.flag = True


# Draw contour
sm.imsave("imgcontour.png",cont.draw_contour(contours,imgRGB))

# Dump contour
cont.dump_contour("contour_final.txt",contours)

# Dump label
cont.dump_label("imglabel.bin",contours,size)
