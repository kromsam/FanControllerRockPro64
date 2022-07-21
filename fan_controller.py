import os
import importlib
import sys
import datetime
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--min", help="Fan will only go on above set temperature. Default: 40C")
parser.add_argument("--max", help="Temperature from which fan speed will be maximum. Default: 60C")
parser.add_argument("-l", "--log", nargs='?', default="fan_controller.log", help="Log to file. Default: 'fan_controller.log'.")
parser.add_argument("-f", "--force", type=check100Range, metavar="[0-100]", help="Set a static fan speed, values from 0-100.")
parser.add_argument("--minpwm", type=check100Range, metavar="[0-100]", help="Set minimum fan speed. Default: 24% (fanPWM: 60).")
args = parser.parse_args()

pathPWM = "/sys/devices/platform/pwm-fan/hwmon/hwmon2/pwm1"
pathTEMP = "/sys/class/thermal/thermal_zone0/temp"
maxPWM = 255

if args.log:
    pathLOG = args.log
else:
    pathLOG = sys.path[0] + "fan_controller.log"

if args.min is not None:
    tempMin = args.min
else:
    tempMin = 40

if args.max is not None:
    tempMax = args.max
else:
    tempMax = 60

if tempMin > tempMax:
    exit("Minimum temperature can't be higher than maximum temperature.")

if args.minpwm is not None:
    # validate!
    minPWM = percentToPWM(args.minPWM)
else:
    minPWM = 60

def getTemp():
    with  open(pathTEMP, 'r') as f:
        temp = int(f.read().replace('\n',''))
        return temp
def getPWM():
    with open(pathPWM,'r') as f:
        return f.readlines()[0].replace('\n','')

def logNow():
    with open(pathLOG,'a') as f:
        f.write("temp: "+str(getTemp())+ " fanPWM: "+str(getPWM())+" date: "+ str(datetime.datetime.now()) + "\n")
def tempToPWM(t = getTemp() / 1000):
    if t >= tempMax:
        return maxPWM
    elif t < tempMin:
        return 0
    else:
        # return ((t / tempMin) - 1) * maxPWM
        return maxPWM / (tempMax - tempMin) * (t - tempMin)
def percentToPWM(p):
    return round(p / 100 * maxPWM)
def pwmToPercent(p):
    return round(p / maxPWM * 100)

def writeFanPWM(pwm):
    print( "Current CPU temperature: " + str(getTemp()/1000)+"C")
    try:
        value = int(pwm)
    except ValueError:
        raise
    if value < 0 or value > maxPWM:
        raise ValueError("Expected 0 <= value <= " + maxPWM + ", got value = " + format(value))
    else:
        with open(pathPWM, "w") as f:
            if pwm < minPWM and pwm > 0:
                f.write(str(minPWM))
                print("Fan set to minimum fan speed: " + str(pwmToPercent(minPWM)) + "% (fanPWM: " + str(minPWM) + ")")
            else:
                f.write(str(pwm))
                print("Fan set to: " + str(pwmToPercent(pwm)) + "% (fanPWM: " + str(pwm) + ")")

def check100Range(arg):
    try:
        value = int(arg)
    except ValueError as err:
       raise argparse.ArgumentTypeError(str(err))
    if value < 0 or value > 100:
        message = "Expected 0 <= value <= 100, got value = {}".format(value)
        raise argparse.ArgumentTypeError(message)
    return value

if not len(sys.argv) > 1:
    writeFanPWM(tempToPWM())
elif args.force is not None:
    writeFanPWM(percentToPWM(args.force))
elif args.log:
    logNow()