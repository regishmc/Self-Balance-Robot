#!/usr/bin/python
"""
*************************************************
* @Project: Self Balance  
* @Platform: Raspberry PI 2 B+ / Ubuntu / Qt                      
* @Description: User Interface - IMU Module
* @Owner: Guilherme Chinellato 
* @Email: guilhermechinellato@gmail.com                                                
*************************************************
"""

import sys
from PyQt4 import QtCore, QtGui
from mainWindow import * 
import socket
import threading
import Queue

queueLockUDPServer = threading.Lock()
workQueueUDPServer = Queue.LifoQueue(100)

class UDPServerThread(threading.Thread):
    def __init__(self, threadID, name, counter, UDP_IP="", UDP_PORT=5000):
        threading.Thread.__init__(self)
        self._stopevent = threading.Event()
        self._sleepperiod = 0.0
        
        self.threadID = threadID
        self.name = name
        self.counter = counter
        
        #UDP server config
        self.UDP_IP = UDP_IP 
        self.UDP_PORT = UDP_PORT  
    
    #Override method
    def run(self):
        #open socket through UDP/IP
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind((self.UDP_IP, self.UDP_PORT)) 

        while not self._stopevent.isSet():
            #Receiving UDP packets
            strData, addr = self.sock.recvfrom(128)
            print strData, addr
            self.data = self.parseData(strData)
            
            queueLockUDPServer.acquire()
            if not workQueueUDPServer.full():
                workQueueUDPServer.put(self.data) 
                queueLockUDPServer.release()
            else:
                queueLockUDPServer.release()           
            
            self._stopevent.wait(self._sleepperiod)
    
    #Override method  
    def join(self, timeout=None):
        #Stop the thread and wait for it to end
        self._stopevent.set()
        threading.Thread.join(self, timeout)
            
    def parseData(self, strData):
        #Check if message is completed    
        if strData.find("#") != -1:
            #Remove end char
            strData = strData.replace("#","")
            data = strData.split(",")
            return data
        else:
            print "Uncompleted UDP message."
            return -1

class mainWindow(QtGui.QMainWindow):
    def __init__(self, parent=None):
        QtGui.QMainWindow.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        
        #Button actions
        self.ui.pushButton.clicked.connect(self.pushButton_onClicked)  
        self.ui.pushButton_EnableUDPServer.clicked.connect(self.pushButton_enableServer_onClicked) 
        self.ui.pushButton_DisableUDPServer.clicked.connect(self.pushButton_disableServer_onClicked) 
        
    def pushButton_onClicked(self):  
        udpMsg = workQueueUDPServer.get() 
        self.ui.lineEdit_AccRawX.setText(str(udpMsg[2])) 
        self.ui.lineEdit_AccRawY.setText(str(workQueueUDPServer.qsize())) 
                
    def pushButton_enableServer_onClicked(self):           
        #Create and start UDP server thread
        self.serverThread = UDPServerThread(1, "UDP-Server", 1)
        self.serverThread.start()

    def pushButton_disableServer_onClicked(self): 
        #Kill UDP server thread 
        self.serverThread.join()

if __name__ == "__main__":
    app = QtGui.QApplication(sys.argv)
    myapp = mainWindow()
    myapp.show()             
    sys.exit(app.exec_())
    

 
    