from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtWidgets,QtGui
from PyQt5.QtWidgets import QWidget,QApplication,QLabel
import sys
from runMain import XiaoFangClient


class RunClient(QWidget):
    def __init__(self):
        super(RunClient,self).__init__()
        self.setWindowTitle('消防报警客户端')
        self.setGeometry(100,100,800,800)
        self.titleLabel=QLabel(self)
        self.titleLabel.setGeometry(250,10,300,100)
        self.titleLabel.setText("消防客户端")
        self.runMessageWindow=QtWidgets.QTextEdit(self)
        self.runMessageWindow.setGeometry(50,100,700,670)
        self.runMessageWindow.setReadOnly(True)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.runMessageWindow.setFont(font)
        font.setPointSize(35)
        self.titleLabel.setFont(font)
        self.xfclient=XiaoFangClient()
        self.xfclient.appendRunMsg.connect(self.appendRunMsg)
        self.xfclient.run()

    def appendRunMsg(self,msg):
        self.runMessageWindow.append(msg)



if __name__ == '__main__':
    app=QApplication(sys.argv)
    runGui=RunClient()
    runGui.show()
    sys.exit(app.exec_())