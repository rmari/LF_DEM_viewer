#!/opt/local/bin/python
#coding=utf-8
from PySide.QtCore import *
from PySide.QtGui import *

import sys, os
self_path=os.path.dirname(os.path.abspath(sys.argv[0]))
sys.path.append(self_path+'/cython')
import LF_DEM_posfile_reading

class drawConfiguration(QWidget):
    speed=10

    def __init__(self, stream, parent=None):
        QWidget.__init__(self, parent)
        # setGeometry(x_pos, y_pos, width, height)
        
        self.setGeometry(400, 400, 850, 850)
        self.setWindowTitle('omer viewer')

        self.timer = QBasicTimer()
    
        self.pos_stream=LF_DEM_posfile_reading.Pos_Stream(stream)
        Box=[self.pos_stream.Lx(),self.pos_stream.Ly(), self.pos_stream.Lz()]
        self.setBox(Box)

        self.positions=dict()
#        self.connect(self.timer, SIGNAL("timeout()"), self.update)

    def start(self):
        self.timer.start(drawConfiguration.speed,self)



    def setBox(self, BoxSize):
        self.L=BoxSize

    def setConfiguration(self, pos, radius):
        self.positions=pos
        self.radius=radius

    def timerEvent(self, event):
        if event.timerId() == self.timer.timerId():
            self.pos_stream.get_snapshot()
#            self.setConfiguration(self.pos_stream.positions_copy(), self.pos_stream.radius_copy())
            self.update()
        else:
            QWidget.timerEvent(self, event)


    def paintEvent(self, event):

        paint = QPainter()
        paint.begin(self)

        # optional
        paint.setRenderHint(QPainter.Antialiasing)

        # make a white drawing background
        paint.setBrush(Qt.white)
        paint.drawRect(event.rect())

        # draw red circles
        paint.setPen(Qt.black)

        for i in self.pos_stream.range():
            radx = self.pos_stream.rad(i)*self.width()/self.L[0]
            rady = radx

            pointX=int((self.pos_stream.pos(i)[0]+0.5*self.L[0])*self.width()/self.L[0])
            pointY=int(-(self.pos_stream.pos(i)[2]-0.5*self.L[2])*self.height()/self.L[2])

            center = QPoint(pointX, pointY)

            paint.setBrush(Qt.yellow)
            paint.drawEllipse(center, radx, rady)

        paint.end()

def init():
    
    arg_nb=2
    if len(sys.argv) != arg_nb :
        print "   Utilisation: ", sys.argv[0], "INPUT_FILE"
        exit(1)
        
    input_stream=open(str(sys.argv[1]),"r")
    return input_stream


app = QApplication([])    

stream=init()
SimuViewer=drawConfiguration(stream)
SimuViewer.show()
SimuViewer.start()

app.exec_()
