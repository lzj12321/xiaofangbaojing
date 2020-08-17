from PyQt5.QtCore import *
from PyQt5.QtWidgets import QMessageBox
from PyQt5 import QtWidgets
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel,QPushButton,QLineEdit
import sys
from runMain import XiaoFangServer


class RunServer(QWidget):
    def __init__(self):
        super(RunServer,self).__init__()
        self.setWindowTitle('消防报警服务器')
        self.setGeometry(100,100,800,800)
        self.titleLabel=QLabel(self)
        self.titleLabel.setGeometry(110,10,300,100)
        self.titleLabel.setText("消防服务器")
        self.runMessageWindow=QtWidgets.QTextEdit(self)
        self.runMessageWindow.setGeometry(50,100,700,670)
        self.runMessageWindow.setReadOnly(True)
        #self.testButton=QPushButton(self)
        #self.testButton.setGeometry(150,10,100,100)
        font = QtGui.QFont()
        font.setPointSize(15)
        font.setBold(True)
        font.setWeight(75)
        self.runMessageWindow.setFont(font)
        font.setPointSize(35)
        self.titleLabel.setFont(font)
        self.closeAlarmButton=QPushButton(self)
        self.closeAlarmButton.setGeometry(510,50,100,50)
        self.closeAlarmButton.setText('关闭报警')
        
        self.disableAlarmButton=QPushButton(self)
        self.disableAlarmButton.setGeometry(610,50,140,50)
        self.disableAlarmButton.setText('关闭当天报警')
        
        self.lineedit=QLineEdit(self)
        self.lineedit.setGeometry(360,50,150,50)
        self.lineedit.setPlaceholderText('请输入工号')
        # self.resize(300,300)
        self.xfserver=XiaoFangServer()
        self.xfserver.appendRunMsg.connect(self.appendRunMsg)
        self.closeAlarmButton.clicked.connect(self.buttonCloseAlarm)
        self.disableAlarmButton.clicked.connect(self.disableAlarmButtonPushed)
        #self.testButton.clicked.connect(self.xfserver.testSendAlarmMsg)
        self.xfserver.run()

    def appendRunMsg(self,msg):
        self.runMessageWindow.append(msg)
        
    def buttonCloseAlarm(self):
        number=self.lineedit.text()
        if number=='':
            return
        self.xfserver.closeAlarm(number)
        self.lineedit.clear()
        pass
    
    def disableAlarmButtonPushed(self):
        number=self.lineedit.text()
        if number=='':
            return
        self.xfserver.disableAlarm(number)
        self.lineedit.clear()



if __name__ == '__main__':
    app=QApplication(sys.argv)
    runGui=RunServer()
    runGui.show()
    sys.exit(app.exec_())