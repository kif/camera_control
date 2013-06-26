#!/usr/bin/python

import matplotlib
matplotlib.use("qt4agg")

import sys, os
#try:
#    import Lima
#except ImportError:
sys.path.insert(0, os.path.join(os.environ["HOME"], "workspace", "Lima", "install"))
import Lima
print Lima
from Lima import Core, Basler
from PyQt4 import QtGui, QtCore

from matplotlib.backends.backend_qt4agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt4agg import NavigationToolbar2QTAgg as NavigationToolbar

import matplotlib.pyplot as plt
import time
import random
import sys
import numpy as np

sys.stdout.flush()

class Window(QtGui.QDialog):
    def __init__(self, parent=None, ip="169.254.101.195"):
        super(Window, self).__init__(parent)

        # a figure instance to plot on
        self.figure = plt.figure()
        self.camera = None
        #x0,y0 value:
        self.x0 = 0
        self.y0 = 0
        self.ip = ip
        #global variable:
        self.image_nb = None
        self.valeurmoy = None
        self.diffx = 0
        self.diffy = 0
        self.acq = None
        self.polarity = 1
        self.n = 0
        self.valeurmoyx = 0
        self.valeurmoyy = 0
        self.colunmmoy = 0
        self.rowmoy = 0

        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvas = FigureCanvas(self.figure)

        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        self.ax = None
        self.img = None
        self.sp2 = None
        self.sp3 = None
        self.column = None
        self.row = None

        self.timer = QtCore.QTimer()
#        self.timer.setInterval(15)
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.my_show)
        self.timer.start(15)


        # Just some button connected to `plot` method
        self.buttonplus = QtGui.QPushButton('+')
        self.buttonplus.clicked.connect(self.plus)

        # Just some button connected to `plot` method
        self.buttonmoins = QtGui.QPushButton('-')
        self.buttonmoins.clicked.connect(self.moins)

        # Just some button connected to `plot` method
        self.buttonzero = QtGui.QPushButton('Memorise zero')
        self.buttonzero.clicked.connect(self.zero)

        # Just some button connected to `plot` method
        self.buttonmesure = QtGui.QPushButton('Mesure')
        self.buttonmesure.clicked.connect(self.mesure)

        # Just some button connected to `plot` method
        self.buttonpolarity_positive = QtGui.QPushButton('Polarity postisive')
        self.buttonpolarity_positive.clicked.connect(self.polarity_positive)

        # Just some button connected to `plot` method
        self.buttonpolarity_negative = QtGui.QPushButton('Polarity negative')
        self.buttonpolarity_negative.clicked.connect(self.polarity_negative)

        # set the grid layout
        layout = QtGui.QGridLayout()
        #layout.addWidget(self.toolbar)
        layout.addWidget(self.buttonplus, 0, 0)
        layout.addWidget(self.buttonmoins, 1, 0)
        layout.addWidget(self.buttonzero, 0, 1)
        layout.addWidget(self.buttonmesure, 1, 1)
        layout.addWidget(self.buttonpolarity_positive, 0, 2)
        layout.addWidget(self.buttonpolarity_negative, 1, 2)

        #set the formular layout
        formlayout = QtGui.QFormLayout()
        self.editavgframe = QtGui.QLineEdit("")
        #self.editavgframe.connect.returnPressed()
        self.editk = QtGui.QLineEdit("")
        #self.editavgframe.connect.returnPressed()
        self.editexpotime = QtGui.QLineEdit("")
        #self.editavgframe.connect.returnPressed()
        formlayout.addRow("Average frames number", self.editavgframe)
        formlayout.addRow("Optique constante", self.editk)
        formlayout.addRow("Exposition time", self.editexpotime)

        #set text layout:
        """self.textx0=str(self.x0)
        self.texty0=str(self.y0)
        self.textdiffx=str(self.diffx)
        self.textdiffy=str(self.diffy)
        
        x0=QtGui.QLabel.setText(self.textx0)
        y0=QtGui.QLabel.setText(self.textx0)
        diffx=QtGui.QLabel.setText(self.textx0)
        diffy=QtGui.QLabel.setText(self.textx0)
        """
        self.textx0 = QtGui.QLineEdit(str(self.x0))
        self.texty0 = QtGui.QLineEdit(str(self.y0))
        self.textdiffx = QtGui.QLineEdit(str(self.diffx))
        self.textdiffy = QtGui.QLineEdit(str(self.diffx))
        textlayout = QtGui.QFormLayout()
        textlayout.addRow("x0=", self.textx0)
        textlayout.addRow("y0=", self.texty0)
        textlayout.addRow("diffx=", self.textdiffx)
        textlayout.addRow("diffy=", self.textdiffy)

        #set the final layout
        finallayout = QtGui.QGridLayout()
        finallayout.addLayout(formlayout, 3, 0)
        finallayout.addLayout(layout, 3, 1)
        finallayout.addWidget(self.canvas, 0, 0, 3, 3)
        finallayout.addLayout(textlayout, 0, 4)
        finallayout.addWidget(self.toolbar, 4, 0)
        self.setLayout(finallayout)

        #set user config
        if self.editk.text() != "":
            self.k = float(self.editk.text())
        else:
            self.k = 1
        if self.editavgframe.text() != "":
            self.avgframe = int(self.editavgframe.text())
        else:
            self.avgframe = 100

        if self.editexpotime.text() != "":
            self.expotime = float(self.editexpotime.text())

        else:
            self.expotime = 0.1

    def init_cam(self):
        self.__cam = Basler.Camera(self.ip)
        self.__i = Basler.Interface(self.__cam)
        c = Core.CtControl(self.__i)
        a = c.acquisition()
        extOp = c.externalOperation()
        self.__bpmHandler = extOp.addOp(Core.BPM, "MyBpm", 0)
        self.bpmMgr = self.__bpmHandler.getManager()
        try:
            self.__i.setAutoGain(0)
            self.__i.setGain(0)
        except :
            print("AutoGain not available in this version")
        a.setAcqNbFrames(100)
        a.setAcqExpoTime(self.expotime)
        c.prepareAcq()

        c.startAcq()

        self.camera = c
        self.acq = a

        while c.getStatus().ImageCounters.LastImageAcquired < 0:
            time.sleep(0.1)
            print("waiting for camera")
        print c.ReadImage().frameNumber
        print "camera ready"


    def zero(self):
        self.image_nb = self.camera.getStatus().ImageCounters.LastImageAcquired
        if self.polarity == 1:
            self.bpmResult = self.bpmMgr.getResult(1, self.image_nb)
            print '(%f,%f)' % (self.bpmResult.beam_center_x, self.bpmResult.beam_center_y),
            print  'valeur du pixel max = ' , self.bpmResult.max_pixel_value,
            self.x0, self.y0 = self.bpmResult.beam_center_x, self.bpmResult.beam_center_y
        if self.polarity == 0:
            reverseimg = c.ReadImage().buffer.max - c.ReadImage().buffer


    def mesure(self):
        print("in mesure")
        while self.camera.getStatus().AcquisitionStatus != Core.AcqReady :
            self.image_nb = self.camera.getStatus().ImageCounters.LastImageAcquired
            self.my_show()
            if self.polarity == 1:
                self.bpmResult = self.bpmMgr.getResult(1, self.image_nb)
                print '(%f,%f)' % ((self.x0 - self.bpmResult.beam_center_x) * self.k, (self.y0 - self.bpmResult.beam_center_y) * self.k),
                print  'valeur du pixel max = ' , self.bpmResult.max_pixel_value,
                self.diffx = (self.x0 - self.bpmResult.beam_center_x) * self.k
                self.diffy = (self.y0 - self.bpmResult.beam_center_y) * self.k
        #permet de d'avoir des plots moyennes:
                self.valeurmoyx = self.valeurmoyx + self.diffx
                self.valeurmoyy = self.valeurmoyy + self.diffy
                self.rowmoy = self.rowmoy + self.camera.ReadImage().buffer.sum(axis=1)
                self.colunmmoy = self.colunmmoy + self.camera.ReadImage().buffer.sum(axis=0)
                self.n = +1
                if self.n == self.avgframe:
                    i = 0
                    self.valeurmoyx = self.valeurmoyx / (n + 1)
                    self.valeurmoyy = self.valeurmoyy / (n + 1)
                    self.colunmmoy = self.colunmmoy / (n + 1)
                    self.rowmoy = self.rowmoy / (n + 1)
                    np.save("colunm", i, ".npy", self.colunmmoy)
                    np.save("row", i, ".npy", self.rowmoy)
                    i = +1
                    self.n = 0
                    print("xmoy=", self.valeurmoyx, "ymoy=", self.valeurmoyy)
                    self.valeurmoyx = 0
                    self.valeurmoyy = 0
                    self.colunmmoy = 0
                    self.rowmoy = 0
            if self.polarity == 0:
                reverseimg = c.ReadImage().buffer.max - c.ReadImage().buffer


    def plus(self):
        self.expotime = self.expotime + (self.expotime / 100)
        self.acq.setAcqExpoTime(self.expotime)
        print self.expotime

    def moins(self):
        self.expotime = self.expotime - (self.expotime / 100)
        self.acq.setAcqExpoTime(self.expotime)
        print self.expotime

    def polarity_positive(self):
        self.polarity = 1
        print self.polarity


    def polarity_negative(self):
        self.polarity = 0
        print self.polarity


    def acquisition(self):
        self.ax = self.figure.add_subplot(221)
        self.img = self.ax.imshow(self.camera.ReadImage().buffer)

        self.sp2 = self.figure.add_subplot(222)
        self.column, = self.sp2.plot(self.camera.ReadImage().buffer.sum(axis=0))
        plt.title('column')

        self.sp3 = self.figure.add_subplot(223)
        self.row, = self.sp3.plot(self.camera.ReadImage().buffer.sum(axis=1))
        plt.title('row')
        self.figure.show()


    def my_show(self):
        self.img.set_array(self.camera.ReadImage().buffer)
        self.column.set_ydata(self.camera.ReadImage().buffer.sum(axis=0))
        self.row.set_ydata(self.camera.ReadImage().buffer.sum(axis=1))

        # refresh canvas
        self.canvas.draw()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    if len(sys.argv) > 1:
        main = Window(ip=sys.argv[1])
    else:
        main = Window()
    main.init_cam()

    #main.image_nb = main.camera.getStatus().ImageCounters.LastImageAcquired
    #while main.image_nb<-1:
    #	wait=True
    main.acquisition()
    main.my_show()

    main.show()
    sys.exit(app.exec_())
