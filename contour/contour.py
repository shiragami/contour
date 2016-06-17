#!/usr/bin/python
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
