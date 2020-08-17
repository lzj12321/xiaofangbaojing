import YamlTool
import gpio
from PyQt5.QtCore import *
from PyQt5 import QtNetwork
from PyQt5.QtNetwork import QTcpSocket
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import pyqtSignal,QDir
from time import sleep
import logging
from logger import Logger


class XiaoFangClient(QObject):
    appendRunMsg=pyqtSignal(str)
    def __init__(self):
        super(XiaoFangClient, self).__init__()
        pass
    
    def bindServerIni(self):
        self.bindServer=QtNetwork.QTcpServer()
        if not self.bindServer.listen(QtNetwork.QHostAddress.Any,8866):
            exit(0)

    def networkIni(self):
        self.sock=QTcpSocket()
        self.sock.connectToHost(self.serverIP,self.serverPort)
        if self.sock.waitForConnected(250):
            self.sock.disconnected.connect(self.disconnectFromServer)
            self.sock.readyRead.connect(self.receiveMsgFromServer)
            self.addRunMessage("连接服务器成功！")
        else:
            self.addRunMessage("连接服务器失败，关闭程序，等待重新开启！")
            exit(0)
        pass

    def ioIni(self):
        self.gpioTool=gpio.Rap_GPIO()

        self.gpioTool.setIOPullUp(self.alarmIO)
        self.gpioTool.setIOStatus(self.alarmIO, self.closeAlarmState)
        
        for camera in self.params['cameras']:
            cameraAlarmIO=self.params['cameras'][camera]['cameraAlarmIO']
            self.gpioTool.setIOPullUp(cameraAlarmIO)
            self.gpioTool.setIOStatus(cameraAlarmIO, self.cameraNormalState)

        self.gpioTool.setIOPullUp(self.buttonIO)
        pass

    def timerIni(self):
        self.checkButtonTimer=QTimer()
        self.checkButtonTimer.setInterval(self.checkButtonInterval)
        self.checkButtonTimer.timeout.connect(self.checkButtonTimerTimeout)
        self.checkButtonTimer.timeout.connect(self.checkCameraState)
        self.checkButtonTimer.start()

        self.checkConnectionTimer=QTimer()
        self.checkConnectionTimer.setInterval(self.checkConnectionInterval)
        self.checkConnectionTimer.timeout.connect(self.checkConnectionTimerTimeout)
        self.checkConnectionTimer.start()
        pass

    def paramIni(self):
        configureFilePath="configure.yaml"
        confirmConfigureFile=QFile(configureFilePath)
        if not confirmConfigureFile.exists():
            QMessageBox.critical(self,'Critical','配置文件丢失！')
            exit(0)

        self.yamlTool=YamlTool.Yaml_Tool()
        self.params=self.yamlTool.getValue(configureFilePath)

        self.serverIP=self.params['server']['ip']
        self.serverPort=self.params["server"]["port"]

        self.alarmIO=self.params['alarmParam']['alarmIO']
        self.startAlarmMsg=self.params['alarmParam']['startAlarmMsg']
        self.stopAlarmMsg=self.params['alarmParam']['stopAlarmMsg']
        self.ackConnectMsg='ack check'
        self.checkReceivedAlarmMsg = 'ack received alarm msg'
        

        self.activateAlarmState=self.params['alarmParam']['activateAlarm']
        self.closeAlarmState=self.params['alarmParam']['closeAlarm']

        self.buttonIO=self.params['button']['io']

        self.workshopDescriptor=self.params['workshop']['descriptor']

        self.checkButtonInterval=self.params['timer']['checkButtonInterval']
        self.checkConnectionInterval=self.params['timer']['checkConnectionInterval']
        self.lastButtonState=True
        
        self.isCheckConnection=False
        self.heartBeatCheckFailedTime=0
        
        self.isReceivedAlarmMsg=False
        
        self.cameraAlarmIO={}
        self.cameraPreAlarmState={}
        self.cameraAlarmState=self.params['alarmParam']['cameraAlarmState']
        self.cameraNormalState=self.params['alarmParam']['cameraNormalState']

        for camera in self.params['cameras']:
            self.cameraAlarmIO[camera]=self.params['cameras'][camera]['cameraAlarmIO']
            self.cameraPreAlarmState[camera]=self.cameraNormalState

    def addRunMessage(self,msg):
        # print(msg)
        # print('test')
        if self.isLogDirExists():
            self.outputLog(msg)
        else:
            self.appendRunMsg.emit('创建记录文件夹失败，请手动创建！')
        currTime=QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
        msg=currTime+":"+msg
        self.appendRunMsg.emit(str(msg))
        pass

    def outputLog(self,msg):
        #time=QDate.currentDate().toString('yyyy-MM-dd')+str('.log')
        logFile ='alarmLog/'+QDate.currentDate().toString('yyyy-MM-dd')+str('.log')
        #logger=Logger(logFile,level='info')
        logger=Logger()
        #print('logFile:'+logFile)
        logger.outputLog(logFile,msg)

    def run(self):
        self.bindServerIni()
        print('param ini')
        self.paramIni()
        print('network ini')
        self.networkIni()
        print('io ini')
        self.ioIni()
        print('timer ini')
        self.timerIni()
        print('initialize success!')
        pass

    def processMsgFromServer(self,msg):
        msg=msg.replace("\n","")
        #print(msg)
        # self.addRunMessage("从服务器接收到数据："+msg)
        if msg==self.stopAlarmMsg:
            for camera in self.cameraPreAlarmState:
                self.cameraPreAlarmState[camera]=self.cameraNormalState
            self.isReceivedAlarmMsg=False
            self.closeAlarmHorn()
        elif msg==self.startAlarmMsg:
            self.sendMsgToServer(self.checkReceivedAlarmMsg)
            self.addRunMessage('移动侦测报警!')
            self.activateAlarmHorn()
        elif msg==self.checkReceivedAlarmMsg:
            self.isReceivedAlarmMsg=True
            print('checkReceivedAlarmMsg')
            #self.addRunMessage('从服务器收到一个未知信号：'+msg)
        elif msg!=self.ackConnectMsg:
            self.addRunMessage('从服务器收到一个未知信号：'+msg)
            
        self.processCheckConnectMsg()
        pass

    def activateAlarmHorn(self):
        #print('activateAlarmHorn')
        self.gpioTool.setIOStatus(self.alarmIO,self.activateAlarmState)
        #self.checkButtonTimer.start()
        pass

    def closeAlarmHorn(self):
        print('closeAlarmHorn')
        self.gpioTool.setIOStatus(self.alarmIO,self.closeAlarmState)
        #self.checkButtonTimer.stop()
        pass

    def disconnectFromServer(self):
        self.sock.close()
        self.addRunMessage("从服务器断开连接，关闭程序，等待重新开启！")
        exit(0)
        pass

    def receiveMsgFromServer(self):
        msg=str(self.sock.readLine(),encoding='utf-8')
        self.processMsgFromServer(msg)
        pass

    def sendMsgToServer(self,msg):
        sendMsg=self.workshopDescriptor+":"+msg+"\n"
        self.sock.write(sendMsg.encode('utf-8'))
        self.sock.flush()
        pass

    def checkButtonTimerTimeout(self):
        currButtonIoState=self.gpioTool.getIOStatus(self.buttonIO)
        if not (self.lastButtonState or currButtonIoState):
            self.isReceivedAlarmMsg=False
            self.addRunMessage('pushed button')
            self.closeAlarmHorn()
            self.sendMsgToServer(self.stopAlarmMsg)
            self.addRunMessage('send stop alarm message')
            self.lastButtonState=True
        else:
            self.lastButtonState=currButtonIoState
        pass

    def checkConnectionTimerTimeout(self):
        #print('checkConnectionTimerTimeout')
        #print('self.isCheckConnection:'+str(self.isCheckConnection))
        if not self.isCheckConnection:
            self.heartBeatCheckFailedTime+=1
            self.addRunMessage('心跳包检测失败!')
            if self.heartBeatCheckFailedTime>10:
                self.addRunMessage('心跳包检测失败超过10次!关闭程序，等待重新开启！')
                self.disconnectFromServer()
                exit(0)
        else:
            self.heartBeatCheckFailedTime=0
            self.isCheckConnection=False
        pass

    def processCheckConnectMsg(self):
        #print('processCheckConnectMsg')
        self.isCheckConnection=True
        self.sendMsgToServer(self.ackConnectMsg)
        # self.checkConnectionTimer.stop()
        # self.checkConnectionTimer.start(self.checkConnectionInterval)
        pass

    def isLogDirExists(self):
        logDirPath='alarmLog'
        logDir=QDir(logDirPath)
        if not logDir.exists():
            if not logDir.mkdir(logDirPath):
                return False
        return True

    def checkCameraState(self):
       # _currHour=int(QDateTime.currentDateTime().toString('hh'))
       # if _currHour>6 and _currHour<23:
        #    return
        #print(_currHour)
        for camera in self.cameraAlarmIO.keys():
            cameraState=self.gpioTool.getIOStatus(self.cameraAlarmIO[camera])
            if cameraState==self.cameraAlarmState:
                #print(camera+' state:'+str(cameraState))
                pass
            if cameraState==self.cameraAlarmState and self.cameraPreAlarmState[camera]==self.cameraAlarmState:
                self.addRunMessage('热敏相机报警!')
                if not self.isReceivedAlarmMsg:
                    currTime=QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
                    #print(currTime+':sendMsgToServer')
                    #self.addRunMessage(currTime+' sendMsgToServer!')
                    self.sendMsgToServer(self.startAlarmMsg)
                self.cameraPreAlarmState[camera]=self.cameraNormalState
                self.activateAlarmHorn()
            else:
                self.cameraPreAlarmState[camera]=cameraState
        pass
