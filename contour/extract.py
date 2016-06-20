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
#img = sm.imread("tile3.png",flatten=True)
img = sm.imread("tile3.png")
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
#print "Splitting contours"
#contours = cont.split_concave(contours)

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


img = np.zeros([1024,1024,3])
img = sm.imread("tile3.png")


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
    imgcrop = img[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
    imgcropR = np.ma.array(imgcrop[:,:,0],mask = np.invert(contour.img))
    imgcropB = np.ma.array(imgcrop[:,:,1],mask = np.invert(contour.img))
    #if np.mean(imgcropR) > np.mean(imgcropB):
    if np.mean(imgcropR) > 100:
        contour.flag = False
    else:
        contour.flag = True

imglabel = np.zeros([1024,1024],dtype=np.int32)

for c,contour in enumerate(contours):
    if contour.flag:
        rcolor,gcolor,bcolor = random.randint(50,75),random.randint(100,150),random.randint(100,150)
        for py,px in contour.contour:
            img[py,px] = [155,185,155]
    # Label hack
    imglabel[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width] = (contour.img)*(c+1)

# Dump contour
cont.dump_contour("contour_final.txt",contours)



sm.imsave("imgcontour2.png",img)
sm.imsave("imgcontour.png",imgcontour)

fo = open("imglabel.bin",'wb')
imglabel.tofile(fo)
fo.close()
        
sys.exit()      
# Filter out contours with no child
#contours = [c for c in contours if bool(c.child)]

# Remove filament/bump from contour

imgmask = np.zeros([1024,1024],dtype=np.bool)
for contour in contours:
    imgmask[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width] |= contour.img

img[imgmask] = [32,32,32]
for contour in contours:
    rcolor,gcolor,bcolor = random.randint(50,75),random.randint(100,150),random.randint(100,150)
    for py,px in contour.contour:
        img[py,px] = [rcolor,gcolor,bcolor]



sm.imsave("imgcontour2.png",img)

#sm.imsave("imgsobel.png",imgsobel)
#sm.imsave("imgmark.png",imgmark)
