import logging
from logging import handlers
from PyQt5.QtCore import *

class Logger(object):
    level_relations = {
        'debug':logging.DEBUG,
        'info':logging.INFO,
        'warning':logging.WARNING,
        'error':logging.ERROR,
        'crit':logging.CRITICAL
    }#日志级别关系映射

#    def __init__(self,filename,level='info',when='D',backCount=3,fmt='%(asctime)s - %(message)s'):
 #       self.logger = logging.getLogger(filename)
  #      format_str = logging.Formatter(fmt)#设置日志格式
   #     self.logger.setLevel(self.level_relations.get(level))#设置日志级别
    #    sh = logging.StreamHandler()#往屏幕上输出
     #   sh.setFormatter(format_str) #设置屏幕上显示的格式
      #  th = handlers.TimedRotatingFileHandler(filename=filename,when=when,backupCount=backCount,encoding='utf-8')#往文件里写入#指定间隔时间自动生成文件的处理器
      #  th.setFormatter(format_str)#设置文件里写入的格式
      #  self.logger.addHandler(sh) #把对象加到logger里
      #  self.logger.addHandler(th)
        
    def outputLog(self,logFile,log):
        fmt='%(asctime)s - %(message)s'
        level='info'
        logger = logging.getLogger(logFile)
        format_str = logging.Formatter(fmt)#设置日志格式
        logger.setLevel(self.level_relations.get(level))#设置日志级别
        if not logger.handlers:
            sh = logging.StreamHandler()#往屏幕上输出
            sh.setFormatter(format_str) #设置屏幕上显示的格式
            th = handlers.TimedRotatingFileHandler(filename=logFile,when='D',backupCount=3,encoding='utf-8')#往文件里写入#指定间隔时间自动生成文件的处理器
            th.setFormatter(format_str)#设置文件里写入的格式
            logger.addHandler(sh) #把对象加到logger里
            logger.addHandler(th)
        logger.info(log)
        
if __name__ == '__main__':
    time=QDate.currentDate().toString('yyyy-MM-dd')+str('.log')
    log = Logger(time,level='info')
    log.outputLog(time,'test output log!')
    #log.logger.info('test output log!')