import sys
import RPi.GPIO as GPIO
import time

class Rap_GPIO:
    def __init__(self):
        #GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        pass

    def getIOStatus(self,io):
        #GPIO.setmode(GPIO.BCM)
        #self.setIOInputMode(io)
        
        return GPIO.input(io)
        pass

    def setIOStatus(self,io,state):
        #GPIO.setmode(GPIO.BCM)
        #print('set '+str(io)+' state '+str(state))
        self.setIOOutputMode(io)
        GPIO.output(io,state)
        pass

    def setIOInputMode(self,io):
        #GPIO.setmode(GPIO.BCM)
        GPIO.setup(io, GPIO.IN)
        pass

    def setIOOutputMode(self,io):
        #GPIO.setmode(GPIO.BCM)
        GPIO.setup(io, GPIO.OUT)
        pass

    def setIOPullUp(self,io):
        #GPIO.setmode(GPIO.BCM)
        GPIO.setup(io, GPIO.IN, pull_up_down=GPIO.PUD_UP)
        pass

    def setIOPullDown(self,io):
        #GPIO.setmode(GPIO.BCM)
        GPIO.setup(io, GPIO.IN, pull_up_down=GPIO.DOWN)
        pass

if __name__=='__main__':
    io=17
    testGpio=Rap_GPIO()
    testGpio.setIOPullUp(io)
    time.sleep(5)
    #testGpio.setIOInputMode(io)
    print(testGpio.getIOStatus(io))    
    time.sleep(0.5)

    print(testGpio.getIOStatus(io))
    time.sleep(0.5)

    print(testGpio.getIOStatus(io))
    time.sleep(0.5)

    print(testGpio.getIOStatus(io))
    #for i in range(1,10,1):
    #   testGpio.setIOOutputMode(i)
    #    print(testGpio.getIOStatus(i))
