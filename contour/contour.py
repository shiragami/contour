#!/usr/bin/python
import subprocess
import numpy as np
from scipy.ndimage.morphology import binary_fill_holes
from scipy.ndimage.filters import gaussian_filter

class Contour:
    def __init__(self,contour):
        self.contour = contour
        self.length  = len(contour)

        # Set the contour location and shape
        px = [p[1] for p in contour]
        py = [p[0] for p in contour]

        self.x,self.y = np.min(px),np.min(py)
        self.x2,self.y2 = np.max(px),np.max(py)

        self.height = self.y2 - self.y + 1
        self.width  = self.x2 - self.x + 1

        self.img = None
        self.area = 0

        self.child = []
        self.valid = True
        self.score = 0
   
    # Create the binary image of enclosed contour
    def fill_holes(self):
        self.img = np.zeros([self.height,self.width],dtype=np.bool)
        for py,px in self.contour:
            self.img[py-self.y,px-self.x] = True
        self.img = binary_fill_holes(self.img)
        self.area = np.sum(self.img)

# Function to trace contour on given grayscale image
def trace(img):
    # Todo: Pass the image buffer through Python wrapper
    # Write image as uint8
    x = np.array(gaussian_filter(img,sigma=1.0),'uint8')
    fo = open("img.raw",'wb')
    x.tofile(fo)
    fo.close()

    size = img.shape

    cmd = ["./trace","img.raw",str(size[0]),str(size[1])]
    p = subprocess.call(cmd,stdout=subprocess.PIPE)
    return load_contours("contour.dat")

# Function to load contour from dat file
# Return a list of contour class
def load_contours(filename):
    contours = []
    data = [l.strip() for l in open(filename)]
    for d in data:
        con = d.split(',')[:-1]
        con = [map(int,x.split()) for x in con]
        c = Contour(con)
        contours.append(c)
    return contours

