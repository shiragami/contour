#!/usr/bin/python

import contour as cont
import numpy as np
import random
import scipy as sp
import scipy.misc as sm
import skimage.filters
import sys
from scipy.ndimage.filters import gaussian_filter
from skimage.filters import gaussian

# Read image
#fname = sys.argv[1]

fname = "/home/tk2/Desktop/sotsuron/holo/D2/rgb_5.png"

imgRGB = sm.imread(fname)
#imgRGB = sm.imresize(imgRGB,(512,512))
#imgRGB = sm.imread("samples2/%s_rgb.png"%n)
#img = imgRGB[:,:,0]
print fname
#img = np.memmap(fname,dtype=np.uint8,shape=(1024,1024),mode='r')

img = sm.imread(fname,flatten=True)
img = sm.imresize(img,(512,512))
imgRGB = sm.imresize(imgRGB,(512,512))
size = img.shape

# Load stain component
#imgH = 255 - np.memmap("./samples/stain/tile%s_H.raw"%n,dtype=np.uint8,shape=(1024,1024),mode='r')
#imgE = 255 - np.memmap("./samples/stain/tile%s_E.raw"%n,dtype=np.uint8,shape=(1024,1024),mode='r')

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
    contour.score = gmean # edit

# Sort contours based on score
#contours = sorted(contours,key=lambda x:x.score,reverse=True)
#sm.imsave("imgcontour2.png",cont.draw_contour(contours,imgRGB))

print "Removing overlapping contour"


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

# start edit
contours = [c for c in contours if c.child is not None]
contours = sorted(contours,key=lambda x:x.score,reverse=True)
contours = cont.remove_overlapping_contour(contours,size)
print "length",len(contours)
#cont.dump_contour("contour.txt",contours)
#sys.exit()
# end edit

"""
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
        contours.append(contour) # Edited to skip splitting
        continue

        for scontour in scontours:
            scontour.fill_holes()
            cchild  = float(scontour.area)/float(scontour.length**2)
            if cchild > 0.04:
                contours.append(scontour)

"""
         
#print "Contour optimization"
# Remove small contours
contours = [c for c in contours if c.length > 100]
#contours = cont.optimize_contour(contours)

# Select contours with the right color features
"""
for contour in contours:
    imgcrop = imgH[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
    imgcropH = np.ma.array(imgcrop,mask = np.invert(contour.img))

    imgcrop = imgE[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
    imgcropE = np.ma.array(imgcrop,mask = np.invert(contour.img))
    
    uH = np.mean(imgcropH)/255.
    uE = np.mean(imgcropE)/255.
    contour.flag = True if uH > 0.56 and uE < 0.5 else False
contours = [c for c in contours if c.flag]
"""

"""
for contour in contours:
    imgcrop = imgRGB[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
    imgcropR = np.ma.array(imgcrop[:,:,0],mask = np.invert(contour.img))
    imgcropB = np.ma.array(imgcrop[:,:,2],mask = np.invert(contour.img))
    #if np.mean(imgcropR) > np.mean(imgcropB):
    if np.mean(imgcropR) > 100:
        contour.flag = False
    else:
        contour.flag = True
"""

# Draw contour
sm.imsave("imgcontour.png",cont.draw_contour(contours,imgRGB))

# Dump contour
cont.dump_contour("contour_final.txt",contours)

# Dump label
cont.dump_label("imglabel.bin",contours,size)
