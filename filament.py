#!/usr/bin/python

import numpy as np
import scipy.misc as sm
import scipy.ndimage.morphology

# Read input image
imgbin = sm.imread("sample/sample6.png",flatten=True) < 10
print imgbin.shape
# Compute the chamfer distance transform
imgdis = scipy.ndimage.morphology.distance_transform_cdt(imgbin,metric='taxicab')

DISTANCE_THRESHOLD = 4
for d in range(DISTANCE_THRESHOLD-1,0,-1):
    for i in range(100):
        for j in range(100):
            d0 = imgdis[i][j]
            if d0 != d:
                continue
            d1 = imgdis[i+1,j]
            d2 = imgdis[i,j+1]
            d3 = imgdis[i-1,j]
            d4 = imgdis[i,j-1]

            if d1 <= d and d2 <= d and d3 <=d and d4 <=d:
                imgdis[i][j] = d-1

    for i in range(100):
        for j in range(100):
            if imgdis[i][j] <= 0:
                imgbin[i][j] = 0

sm.imsave("imgdis.png",imgdis)
sm.imsave("imgbin2.png",imgbin)
