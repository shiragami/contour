#!/usr/bin/python
import numpy as np
import scipy.misc as sm
from scipy.ndimage.morphology import binary_fill_holes
import sys

class Contour:
    def __init__(self,contour):
        self.contour = contour

        # Set the contour location and shape
        px = [p[1] for p in contour]
        py = [p[0] for p in contour]

        self.x,self.y = np.min(px),np.min(py)
        self.x2,self.y2 = np.max(px),np.max(py)

        self.height = self.y2 - self.y + 1
        self.width  = self.x2 - self.x + 1

        # Create the binary image of enclosed contour
        self.img = np.zeros([self.height,self.width],dtype=np.bool)
        for py,px in self.contour:
            self.img[py-self.y,px-self.x] = True
        self.img = binary_fill_holes(self.img)

        self.area = np.sum(self.img)

        self.child = []
        self.valid = True

# Check if bounding box of contour1 is enclosed by bounding box of contour2
def check_box_enclosed(c1,c2):
    if c1.x > c2.x and c1.x2 < c2.x2 and c1.y > c2.y and c1.y2 < c2.y2:
        return True
    else:
        return False

# Load contour
contours = []
data = [l.strip() for l in open("contour_nonoverlap.dat")]
for d in data:
    con = d.split(',')[:-1]
    con = [map(int,x.split()) for x in con]
    c = Contour(con)
    contours.append(c)

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
        if check_box_enclosed(ci,cj):
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
