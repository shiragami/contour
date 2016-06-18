#!/usr/bin/python
import numpy as np
import scipy.misc as sm
from scipy.ndimage.morphology import binary_fill_holes
import sys
import contour as cont


# Load contour
contours = cont.load_contours("contour_nonoverlap.dat")
"""
data = [l.strip() for l in open("contour_nonoverlap.dat")]
for d in data:
    con = d.split(',')[:-1]
    con = [map(int,x.split()) for x in con]
    c = Contour(con)
    c.fill_holes()
    contours.append(c)
"""
for contour in contours:
    contour.fill_holes()


# Sort contour by area
contours = sorted(contours,key=lambda x:x.area)

# Main function
for n,contour in enumerate(contours):
    fname = "out/" + "{0:04d}".format(n) + ".png"
#    sm.imsave(fname,contour.img)

# Group enclosed contours together 
Ncontours = len(contours)
for i in range(Ncontours-1):
    ci = contours[i]
    for j in range(Ncontours-1,i,-1):
        cj = contours[j]
        if cont.check_box_enclosed(ci,cj):
            # Crop boxj
            py,px = ci.y - cj.y , ci.x - cj.x
            ch,cw = ci.img.shape
            imgtmp = cj.img[py:py+ch,px:px+cw]

            # Calculate ci.img U imgtmp
            if np.sum(ci.img & imgtmp) > 0:
                cj.child.append(ci)
                continue

#img = sm.imread("tile2.png")
img = np.zeros([1024,1024])
       
for contour in contours:
    if bool(contour.child):
        for py,px in contour.contour:
            img[py,px] = 255
        for child in contour.child:
            for py,px in child.contour:
                img[py,px] = 128

sm.imsave("imgcontour2.png",img)
