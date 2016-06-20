#!/usr/bin/python
import contour as cont
import numpy as np
import scipy.misc as sm
import sys

# Load contour
contours = cont.load_contours("contour_final.txt")

# Load marked contour
marked = [l.strip() for l in open("marked.txt")]
img = sm.imread("tile3.png")

for c,contour in enumerate(contours):
    contour.fill_holes()
    imgcrop = img[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
    imgcropR = np.ma.array(imgcrop[:,:,0],mask = np.invert(contour.img))
    imgcropG = np.ma.array(imgcrop[:,:,1],mask = np.invert(contour.img))
    imgcropB = np.ma.array(imgcrop[:,:,2],mask = np.invert(contour.img))
    if str(c) not in marked:
        print np.mean(imgcropR),np.mean(imgcropB)

sys.exit()


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
