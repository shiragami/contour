#!/usr/bin/python
import numpy as np
import scipy.misc as sm
from scipy.ndimage.morphology import binary_fill_holes
import sys

class Contour:
    def __init__(self,contour):

        self.contour = contour

        # Find the contour bounding box
        px = [p[0] for p in contour]
        py = [p[1] for p in contour]
        self.box = (np.min(px),np.min(py),np.max(px),np.max(py))

        # Create the binary image of enclosed contour
        self.img = np.zeros([self.box[3]-self.box[1]+1,self.box[2]-self.box[0]+1],dtype=np.bool)
        for px,py in self.contour:
            self.img[py-self.box[1],px-self.box[0]] = True
        self.img = binary_fill_holes(self.img)

        self.area = np.sum(self.img)

        self.child = []
        self.valid = True

# Check if bounding box of contour1 is enclosed by bounding box of contour2
def check_box_enclosed(box1,box2):
    x1,y1,x2,y2 = box1  
    j1,i1,j2,i2 = box2

    if x1 > j1 and x2 < j2 and y1 > i1 and y2 < i2:
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

Ncontours = len(contours)
for i in range(Ncontours-1):
    ci = contours[i]
    for j in range(Ncontours-1,i,-1):
        cj = contours[j]
        if check_box_enclosed(ci.box,cj.box):
            # Crop boxj
            px,py = ci.box[0]-cj.box[0],ci.box[1]-cj.box[1]
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
        for px,py in contour.contour:
            img[py,px] = 255
        for child in contour.child:
            for px,py in child.contour:
                img[py,px] = 128

sm.imsave("imgcontour2.png",img)

sys.exit()




#b = find_bound_box(contour[score[2][0]])
#sm.imsave("imgbox.png",imgcontour[b[0]:b[2]+1,b[1]:b[3]+1]) # Todo! fix bounding box in segment.py

# Find the bounding box for each contour
box = []
for c in contour:
    box.append(find_bound_box(c))


for i in range(len(contour)):
    # Mark box 1 with contour1
    imgb1 = np.zeros([box[i][3]-box[i][1]+1,box[i][2]-box[i][0]+1],dtype=np.bool)
    points = [(px-box[i][0],py-box[i][1]) for px,py in contour[i]]
    for px,py in points:
        imgb1[py,px] = True
        
    imgb1 = binary_fill_holes(imgb1)
    sm.imsave("imgbin.png",imgb1)

    for j in range(i+1,len(contour)):
        # Skip if contour1 and contour2 bouding boxes are not overlapped
        if not check_box_overlap(box[i],box[j]):
            continue
        # Further check each point in contour1 if overlapped with contour2
        points = [(px,py) for px,py in contour[j] if px > box[i][0] and px < box[i][2] and py > box[i][1] and py < box[i][3]]
        for px,py in points:
            if imgb1[py-box[i][1],px-box[i][0]]:
                print i,j
                break
