from PyQt5 import QtNetwork
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtCore import *
from  PyQt5.QtNetwork import QTcpSocket

class Socket(QObject):
    receivedMsg=pyqtSignal(str)
    disconnectedServer=pyqtSignal(str)

    def __init__(self):
        super(Socket,self).__init__()
        pass

    def setSocket(self,sock):
        # print('set socket start')

        self.sock=sock
        self.sock.disconnected.connect(self.disconnectedFromServer)
        self.sock.readyRead.connect(self.receivedMsgFromServer)
        # print('set socket end')

    def setDescriptor(self,descriptor):
        self.descriptor=descriptor

    def readMsg(self):
        #print('read msg111111111')
        msg=str(self.sock.readLine(),encoding='utf-8')
        #print('received msg:'+msg)
        return msg

    def sendMsg(self,msg):
        #print('sent msg:'+msg)
        msg+='\n'
        self.sock.write(msg.encode('utf-8'))
        self.sock.flush()

    def disconnectedFromServer(self):
        # print('test disconnect')
        self.disconnectedServer.emit(self.descriptor)
        # print('test disconnect1111111111111')

    def receivedMsgFromServer(self):
        self.receivedMsg.emit(self.descriptor)
        
    def close(self):
        self.sock.close()



