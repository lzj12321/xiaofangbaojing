import sys
import RPi.GPIO as GPIO


class Rap_GPIO:
    def __init__(self):
        GPIO.setmode(GPIO.BCM)  # BMC或者BOARD模式
        pass

    def getIOStatus(self,io):
        #self.setIOInputMode(io)
        return GPIO.input(io)  # input()方法可以读取pinx引脚的值
        pass

    def setIOStatus(self,io,state):
        self.setIOOutputMode(io)
        GPIO.output(io,state)
        pass

    def setIOInputMode(self,io):
        GPIO.setup(io, GPIO.IN)
        pass

    def setIOOutputMode(self,io):
        GPIO.setup(io, GPIO.OUT)
        pass

    def setIOPullUp(self,io):
        GPIO.setup(io, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        pass

    def setIOPullDown(self,io):
        GPIO.setup(io, GPIO.IN, pull_up_down=GPIO.DOWN)
        pass

