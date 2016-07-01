#!/usr/bin/python
import contour as cont
import numpy as np
import scipy.misc as sm
import sys

fptive = open("positive.dat",'w')
fntive = open("negative.dat",'w')

for n in range(1,6):
    # Load contour
    contours = cont.load_contours("./samples/contour%s.txt"%n)

    # Load marked contour
    marked = [l.strip() for l in open("./samples/marked%s.txt"%n)]
    img = sm.imread("./samples/tile%s.png"%n)

    # Load stain component
    imgH = 255 - np.memmap("./samples/stain/tile%s_H.raw"%n,dtype=np.uint8,shape=(1024,1024),mode='r')
    imgE = 255 - np.memmap("./samples/stain/tile%s_E.raw"%n,dtype=np.uint8,shape=(1024,1024),mode='r')

    # Get color features
    for c,contour in enumerate(contours):
        contour.fill_holes()
        imgcrop = img[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
        imgcropR = np.ma.array(imgcrop[:,:,0],mask = np.invert(contour.img))
        imgcropG = np.ma.array(imgcrop[:,:,1],mask = np.invert(contour.img))
        imgcropB = np.ma.array(imgcrop[:,:,2],mask = np.invert(contour.img))

        imgcrop = imgH[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
        imgcropH = np.ma.array(imgcrop,mask = np.invert(contour.img))

        imgcrop = imgE[contour.y:contour.y+contour.height,contour.x:contour.x+contour.width]
        imgcropE = np.ma.array(imgcrop,mask = np.invert(contour.img))

        if str(c) in marked:
            fntive.write("%s %s\n" % (np.mean(imgcropH)/255.,np.mean(imgcropE)/255.))
        else:
            fptive.write("%s %s\n" % (np.mean(imgcropH)/255.,np.mean(imgcropE)/255.))
        

fptive.close()
fntive.close()

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
