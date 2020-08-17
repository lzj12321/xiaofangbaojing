import socket
import YamlTool
import gpio
import logging
from PyQt5.QtCore import *
from PyQt5 import QtNetwork
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import pyqtSignal
from datetime import datetime
from logger import Logger
import time


class XiaoFangServer(QObject):
    appendRunMsg=pyqtSignal(str)
    workshopOfflineAlarm=pyqtSignal(str)

    def __init__(self):
        super(XiaoFangServer, self).__init__()
        self.workshopOfflineAlarm.connect(self.workshopOffline)
        self.detectOfflineTime=0
        self.isEnableAlarm=True
        pass

    def serverIni(self):
        self.connectedWorkshopSock={}
        self.serverSocket=QtNetwork.QTcpServer()
        if self.serverSocket.listen(QtNetwork.QHostAddress.Any,self.serverPort):
            self.serverSocket.newConnection.connect(self.newConnection)
            self.addRunMessage('null',"服务器初始化成功！")
        else:
            self.addRunMessage('null',"服务器初始化失败！")
            exit(0)
        pass

    def ioIni(self):
        self.gpioTool=gpio.Rap_GPIO()

        for io in self.workShopAlarmIO.values():
            self.gpioTool.setIOInputMode(io)
            self.gpioTool.setIOPullUp(io)
            #self.gpioTool.setIOInputMode(io)
            #self.gpioTool.setIOOutputMode(io)
            #self.gpioTool.setIOStatus(io, True)
            
            
        self.gpioTool.setIOPullUp(self.alarmIO)
        self.closeAlarmHorn()
        pass

    def timerIni(self):
        self.checkAlarmTimer=QTimer()
        self.checkAlarmTimer.setInterval(self.checkAlarmInterval)
        self.checkAlarmTimer.timeout.connect(self.checkAlarmTimerTimeout)
        self.checkAlarmTimer.start()

        self.checkConnectionTimer=QTimer()

        self.checkConnectionTimer.setInterval(self.heartBeatInterval)
        self.checkConnectionTimer.timeout.connect(self.checkConnectionTimerTimeout)
        self.checkConnectionTimer.start()

        self.checkSelfTestTimer=QTimer()
        self.checkSelfTestTimer.setInterval(self.checkSelfTestInterval)
        self.checkSelfTestTimer.timeout.connect(self.checkSelfTest)
        self.checkSelfTestTimer.start()


    def paramIni(self):
        configureFilePath="configure.yaml"
        confirmConfigureFile=QFile(configureFilePath)
        if not confirmConfigureFile.exists():
            QMessageBox.critical(self,'Critical','配置文件丢失！')
            exit(0)

        self.yamlTool=YamlTool.Yaml_Tool()
        self.params=self.yamlTool.getValue(configureFilePath)
        
        
        self.securityStaffsNumber=[]
        for number in self.params['securityStaffs'].keys():
            print(self.params['securityStaffs'][number])
            self.securityStaffsNumber.append(str(self.params['securityStaffs'][number]))
            

        self.serverIP=self.params['server']['ip']
        self.serverPort=self.params["server"]["port"]

        self.alarmIO=self.params['alarmParam']['alarmIO']
        self.startAlarmMsg=self.params['alarmParam']['startAlarmMsg']
        self.stopAlarmMsg=self.params['alarmParam']['stopAlarmMsg']
        # print('stop alarm msg:'+self.stopAlarmMsg)
        self.activateAlarmState=self.params['alarmParam']['activateAlarm']
        self.closeAlarmState=self.params['alarmParam']['closeAlarm']

        self.workShopAlarmIO={}
        self.workShopIP={}
        self.workshopHeartbeatCheckFailedTime={}
        for workshop in self.params['workshop']:
            self.workShopAlarmIO[workshop]=self.params['workshop'][workshop]['io']
            self.workShopIP[workshop]=self.params['workshop'][workshop]['ip']
            self.workshopHeartbeatCheckFailedTime[workshop]=0

        self.workShopConnectionCheckState={}
        self.workshopCheckSendAlarmMsg={}
        self.workshopDetectedAlarmTime={}
        
        self.uncheck='Uncheck'
        self.checked='checked'
        self.waitCheck='wait check'
        self.checkMsg='ack check'
        self.checkReceivedAlarmMsg='ack received alarm msg'
        #self.heartBeatCheckFailedTime=0

        for workshop in self.params['workshop']:
            self.workShopConnectionCheckState[workshop]='Uncheck'
            self.workshopCheckSendAlarmMsg[workshop]=False
            #print('workshop:'+workshop)
            self.workshopDetectedAlarmTime[workshop]=0
            
        self.checkAlarmInterval=self.params['timer']['checkAlarmInterval']
        self.heartBeatInterval=self.params['timer']['heartBeatInterval']
        self.checkSelfTestInterval=self.params['timer']['checkSelfTestInterval']
        self.cameraSelfTestInterval=self.params['selfTest']['cameraSelfTestInterval']
        
        self.camSelfTestInterval=self.params['timer']['camSelfTestInterval']
        self.camRetrySelfTestInterval=self.params['timer']['camRetrySelfTestInterval']
        

        self.currAlarmWorkshops=[]
        self.lastAlarmIOState={}
        self.isPushedStopAlarmButton={}
        self.isSelfTest={}
        self.checkIsReceivedAlarmMsg={}
        for workshop in self.workShopIP.keys():
            self.lastAlarmIOState[workshop]=self.closeAlarmState
            self.isPushedStopAlarmButton[workshop]=False
            self.isSelfTest[workshop]=False
            self.checkIsReceivedAlarmMsg[workshop]=False

    def checkConnectionTimerTimeout(self):
        dayOfWeek = datetime.now().isoweekday() ###返回数字1-7代表周一到周日
        if dayOfWeek!=7:
            self.isEnableAlarm=True
        for workshop in list(self.connectedWorkshopSock.keys()):
            if self.workShopConnectionCheckState[workshop] == self.uncheck:
                self.sendCheckSignal(workshop)
                self.workShopConnectionCheckState[workshop] = self.waitCheck
            elif self.workShopConnectionCheckState[workshop] == self.waitCheck:
                self.addRunMessage(workshop,workshop+' heartbeat check failed!')
                #self.heartBeatCheckFailedTime+=1
                self.workshopHeartbeatCheckFailedTime[workshop]+=1
                self.sendCheckSignal(workshop)
                self.workShopConnectionCheckState[workshop] = self.waitCheck
                if self.workshopHeartbeatCheckFailedTime[workshop]>6:
                    self.workShopConnectionCheckState[workshop] = self.uncheck
                    self.disconnectWorkshopFromServer(workshop)
                    self.workshopHeartbeatCheckFailedTime[workshop]=0
                    #self.addRunMessage(workshop+' heartbeat checkfailed time bigger than 10')
                # print('check connection time out!')
            elif self.workShopConnectionCheckState[workshop] == self.checked:
                self.sendCheckSignal(workshop)
                self.workShopConnectionCheckState[workshop] = self.waitCheck
                self.workshopHeartbeatCheckFailedTime[workshop]=0
        pass

    def sendCheckSignal(self,workshop):
        #print('send check msg to '+workshop)
        self.sendMsgToWorkshop(self.checkMsg,workshop)
        pass

    def disconnectWorkshopFromServer(self,workshop):
        self.removeClientSocket(workshop)
        pass
    
    def outputLog(self,workshop,msg):
        #time=QDate.currentDate().toString('yyyy-MM-dd')+str('.log')
        logFile =workshop+' alarmLog/'+QDate.currentDate().toString('yyyy-MM-dd')+str('.log')
        #logger=Logger(logFile,level='info')
        logger=Logger()
        #print('logFile:'+logFile)
        logger.outputLog(logFile,msg)

    def addRunMessage(self,workshop='null',msg='null'):
        currTime=QDateTime.currentDateTime().toString('yyyy-MM-dd hh:mm:ss')
        if workshop!='null' and self.isLogDirExists(workshop):
            self.outputLog(workshop,msg)
        elif workshop!='null':
            pass
        msg=currTime+":"+msg
        self.appendRunMsg.emit(str(msg))
            #self.appendRunMsg.emit(workshop + '栋记录文件夹创建失败，请手动创建！')
        pass

    def run(self):
        print('param ini')
        self.paramIni()
        print('server ini')
        self.serverIni()
        print('io ini')
        self.ioIni()
        print('timer ini')
        self.timerIni()
        pass

    def processMsgFromClient(self,msg,workshop):
        #print(workshop+':'+msg)
        self.workShopConnectionCheckState[workshop]=self.checked
        if msg.find(':')>0:
            validMsg=msg.split(':')[1]
        else:
            validMsg=msg
        if validMsg==self.stopAlarmMsg:
            self.addRunMessage(workshop,'收到'+workshop+'栋:'+validMsg)
            if workshop in self.currAlarmWorkshops:
                self.lastAlarmIOState[workshop]=self.closeAlarmState
                self.removeAlarmWorkshop(workshop)
        elif validMsg==self.startAlarmMsg:
            self.sendMsgToWorkshop(self.checkReceivedAlarmMsg,workshop)
            self.addRunMessage(workshop,'收到'+workshop+'栋热敏相机报警信号')
            if not self.isEnableAlarm:
                return
            self.addAlarmWorkShop(workshop)
            self.workshopCheckSendAlarmMsg[workshop]=True
        elif validMsg==self.checkMsg:
            self.processCheckConnectionMsg(workshop)
        elif validMsg==self.checkReceivedAlarmMsg:
            self.addRunMessage(workshop,workshop+' 收到:'+validMsg)
            self.workshopCheckSendAlarmMsg[workshop]=True
        else:
            self.addRunMessage(workshop,workshop+'栋收到一个未知信号：'+validMsg)
        pass
    
    def processStartAlamrMsg(self):
        
        pass

    def processCheckConnectionMsg(self,workshop):
        self.workShopConnectionCheckState[workshop]=self.checked
        pass

    def removeClientSocket(self,workshop):
        if workshop in self.connectedWorkshopSock.keys():
            self.connectedWorkshopSock.pop(workshop)
        pass

    def addClientSocket(self,workshop,sock):
        _socket=socket.Socket()
        _socket.setSocket(sock)
        _socket.setDescriptor(workshop)
        _socket.receivedMsg.connect(self.receivedMsgFromWorkShop)
        _socket.disconnectedServer.connect(self.workshopDisconnectedFromServer)
        if workshop in self.connectedWorkshopSock.keys():
            self.connectedWorkshopSock[workshop].close()
        self.connectedWorkshopSock[workshop] = _socket
        pass

    def activateAlarmHorn(self):
        #self.addRunMessage('null','activateAlarmHorn')
        #print('activateAlarmHorn')
        self.gpioTool.setIOStatus(self.alarmIO,self.activateAlarmState)
        pass

    def closeAlarmHorn(self):
        #self.addRunMessage('null','closeAlarmHorn')
        self.gpioTool.setIOStatus(self.alarmIO,self.closeAlarmState)
        pass

    def addAlarmWorkShop(self,workShop):
        #self.addRunMessage(workShop,workShop+'栋检测到报警信号！')
        #self.sendMsgToWorkshop(self.startAlarmMsg,workShop)
        
        if self.isEnableAlarm:
            self.activateAlarmHorn()
        if workShop not in self.currAlarmWorkshops:
            self.workshopCheckSendAlarmMsg[workShop]=False
            self.currAlarmWorkshops.append(workShop)
        pass

    def newConnection(self):
        newSock=self.serverSocket.nextPendingConnection()
        newSockIp = newSock.peerAddress().toString()
        newSockIp = newSockIp.split(':')[-1]
        if newSockIp in self.workShopIP.values():
            for workshop in self.workShopIP.keys():
                if self.workShopIP[workshop] == newSockIp:
                    self.addClientSocket(workshop, newSock)
                    self.detectOfflineTime=0
                    self.addRunMessage(workshop,workshop+"栋已连接服务器！")
        else:
            newSock.close()
            self.addRunMessage('null','未知IP连接服务器！ '+newSockIp)
        pass

    def receivedMsgFromWorkShop(self,workshop):
        msg=self.connectedWorkshopSock[workshop].readMsg()
        msg=msg.replace("\n","")
        self.processMsgFromClient(msg,workshop)
        pass

    def workshopDisconnectedFromServer(self,workshop):
        self.removeClientSocket(workshop)
        self.addRunMessage(workshop,workshop+"栋从服务器断开连接！")
        pass

    def checkAlarmTimerTimeout(self):
        if not self.isEnableAlarm:
            return
        for workshop in self.workShopAlarmIO.keys():
            currAlarmIOStatus=self.gpioTool.getIOStatus(self.workShopAlarmIO[workshop])
            if not currAlarmIOStatus:
                self.workshopDetectedAlarmTime[workshop]+=1
                #self.addRunMessage(workshop,'detected alarm time:'+str(self.workshopDetectedAlarmTime[workshop]))
            else:
                self.workshopDetectedAlarmTime[workshop]=0
            #print('workshopDetectedAlarmTime '+workshop+':'+str(self.workshopDetectedAlarmTime[workshop]))
            if self.workshopDetectedAlarmTime[workshop]>15:
                self.addRunMessage(workshop,workshop+'栋检测到移动报警信号！')
                self.addAlarmWorkShop(workshop)
                self.workshopDetectedAlarmTime[workshop]=0

        if len(self.currAlarmWorkshops)>0:
            self.activateAlarmHorn()
        else:
            self.closeAlarmHorn()


        for workshop in self.currAlarmWorkshops:
            if workshop not in self.workshopCheckSendAlarmMsg.keys():
                self.addRunMessage('null',' a error alarm workshop!')
            else:
                if not self.workshopCheckSendAlarmMsg[workshop]:
                    self.sendMsgToWorkshop(self.startAlarmMsg,workshop)
        
        for workshop in self.workShopIP.keys():
            self.isPushedStopAlarmButton[workshop]=False
        pass

    def sendMsgToWorkshop(self,msg,workshop):
        if workshop in self.connectedWorkshopSock.keys():
            self.connectedWorkshopSock[workshop].sendMsg(msg)
            if msg!=self.checkMsg:
                self.addRunMessage(workshop,'向'+workshop+'栋，发送数据:'+msg)
        else:
            self.addRunMessage(workshop,'向'+workshop+'栋，发送数据失败!')
        pass
    
    def workshopOffline(self,offlineWorkshop):
        self.detectOfflineTime+=1
        self.addRunMessage(offlineWorkshop,offlineWorkshop+"栋未连接服务器!")
        if self.detectOfflineTime>6:
           #self.addRunMessage(offlineWorkshop,offlineWorkshop+' detect offline time>3')
            #exit(0)
            pass
        self.activateAlarmHorn()
        startAlarmTime=QDateTime.currentDateTime()
        while True:
            if startAlarmTime.addSecs(1)<=QDateTime.currentDateTime():
                break
        if len(self.currAlarmWorkshops)==0:
            self.closeAlarmHorn()
        pass

    def isLogDirExists(self,workshop):
        logDirPath=workshop+' alarmLog'
        logDir=QDir(logDirPath)
        if not logDir.exists():
            if not logDir.mkdir(logDirPath):
                return False
        return True
        pass
    
    def removeAlarmWorkshop(self,workshop):
        self.workshopDetectedAlarmTime[workshop]=0
        if workshop in self.currAlarmWorkshops:
            self.currAlarmWorkshops.remove(workshop)
            self.addRunMessage(workshop,workshop+' 解除报警!')
        self.isPushedStopAlarmButton[workshop]=True
        
        if len(self.currAlarmWorkshops)>0 and self.isEnableAlarm:
            self.activateAlarmHorn()
        else:
            self.closeAlarmHorn()


    def checkSelfTest(self):
        for workshop in self.workShopAlarmIO.keys():
            if workshop not in self.connectedWorkshopSock.keys():
                self.workshopOfflineAlarm.emit(workshop)
        return
        
        currTime=QDateTime.currentDateTime().toString('hh:mm')
        #print('currTime:'+currTime)
        self.selfTestParam=self.params['selfTest']
        for workshop in self.selfTestParam['workshops'].keys():
            if currTime==self.selfTestParam['workshops'][workshop]['selfTestTime'] and not self.isSelfTest[workshop]:
                self.startWorkshopCamSelfTest(workshop)
        pass

    def workshopCamSelfTest(self,workshop):
        pass
        #1033947

    def startWorkshopCamSelfTest(self,workshop):
        self.isSelfTest[workshop] = True
        #selfTestInterval=self.selfTestParam['workshops'][workshop]['selfTestInterval']
        retrySelfTestInterval=self.selfTestParam['retryInterval']
        maxRetryTime=self.selfTestParam['maxRetryTime']

        #print(selfTestInterval)
        #print(retrySelfTestInterval)
        #print(maxRetryTime)
        #print(self.cameraSelfTestInterval)
        

        for cam in self.selfTestParam['workshops'][workshop]['selfTestCameras'].keys():
            print('start self test '+workshop+' '+cam)
            camSelfTestResult=False
            currTime=QDateTime.currentDateTime()
            for i in range(0,maxRetryTime,1):
                ioState=self.gpioTool.getIOStatus(self.workShopAlarmIO[workshop])
                if ioState:
                    time.sleep(retrySelfTestInterval)
                else:
                    camSelfTestResult=True
            #print(currTime.addSecs(self.cameraSelfTestInterval)>=QDateTime.currentDateTime())
            if camSelfTestResult:
                self.addRunMessage(workshop,cam + ' self test success!')
                print(cam + ' self test success!')
            else:
                self.addRunMessage(workshop,cam + ' self test fail!')
                print(cam + ' self test fail!')
                self.activateAlarmHorn()
                time.sleep(1)
                self.closeAlarmHorn()
            while currTime.addSecs(self.cameraSelfTestInterval)>=QDateTime.currentDateTime():
                pass
                #if currTime.addSecs(self.cameraSelfTestInterval)<=QDateTime.currentDateTime():
                 #   break
        pass
    
    def closeAlarm(self,number):
        if number not in self.securityStaffsNumber:
            self.addRunMessage('null','工号错误!')
            return
        self.params['alarmData']['dayAlarmTime']+=1
        self.yamlTool.saveParam('configure.yaml',self.params)
        print(number+' closeAlarmHorn')
        #self.addRunMessage('E',number+' close alarm!')
        self.closeAlarmHorn()
        for alarmWorkshop in self.currAlarmWorkshops:
            self.workshopCheckSendAlarmMsg[alarmWorkshop]=False
            self.isPushedStopAlarmButton[alarmWorkshop]=True
            self.workshopDetectedAlarmTime[alarmWorkshop]=0
            self.lastAlarmIOState[alarmWorkshop]=self.closeAlarmState
            #print(alarmWorkshop+' close alarm')
            self.addRunMessage(alarmWorkshop,number+' close alarm!')
            self.removeAlarmWorkshop(alarmWorkshop)
            self.sendMsgToWorkshop(self.stopAlarmMsg,alarmWorkshop)
        pass
    
    def disableAlarm(self,number):
        dayOfWeek = datetime.now().isoweekday() ###返回数字1-7代表周一到周日
        if dayOfWeek!=7:
            self.addRunMessage('null','只能关闭礼拜天的全天报警!')
            return
        if number not in self.securityStaffsNumber:
            self.addRunMessage('null','工号错误!')
            return
        print(number+' disable AlarmHorn')
        self.isEnableAlarm=False
        self.addRunMessage('E',number+' disable alarm!')
        #self.addRunMessage('E',number+' disable alarm!')
        self.closeAlarmHorn()
        for alarmWorkshop in self.currAlarmWorkshops:
            self.workshopCheckSendAlarmMsg[alarmWorkshop]=False
            self.isPushedStopAlarmButton[alarmWorkshop]=True
            self.lastAlarmIOState[alarmWorkshop]=self.closeAlarmState
            print(alarmWorkshop+' close alarm')
            self.removeAlarmWorkshop(alarmWorkshop)
            self.sendMsgToWorkshop(self.stopAlarmMsg,alarmWorkshop)
        pass
