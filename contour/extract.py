#!/usr/bin/python

import numpy as np
import random
import scipy.misc as sm

contour = []
data = [l.strip() for l in open("data.dat")]
spaces = [i for i in range(len(data)) if data[i]=='']

contour.append(data[:spaces[0]])
for s in range(len(spaces)-1):
    contour.append(data[spaces[s]+1:spaces[s+1]])
#contour.append(data[spaces[-1]:])

#for c in contour:
#    print c

print "Total:",len(contour)


imgcontour = np.zeros([512,512,3])

for c in contour:
    rcolor = random.randint(100,200)
    gcolor = random.randint(100,200)
    bcolor = random.randint(100,200)

    for point in c:
        px,py = point.split(" ")
        imgcontour[py,px] = [rcolor,gcolor,bcolor]

sm.imsave("imgcontour.png",imgcontour)
