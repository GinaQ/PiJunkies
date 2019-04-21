# Import libraries (board and busio are for i2c) 
import board
import busio
import os                       # To play .wav files
from digitalio import DigitalInOut

import adafruit_character_lcd.character_lcd_rgb_i2c as character_lcd
from gpiozero import Button, Buzzer, MotionSensor
import RPi.GPIO as GPIO

from time import sleep          # To easily use sleep function
from time import time           # To measure time in seconds
from datetime import datetime   # To get current date and time
from twilio.rest import Client

# Modify this if you have a different sized Character LCD
lcd_columns = 16
lcd_rows = 2

# Initialize I2C bus 
i2c = busio.I2C(board.SCL, board.SDA)

# Initialize the LCD class
lcd = character_lcd.Character_LCD_RGB_I2C(i2c, lcd_columns, lcd_rows)

#set GPIO pin mode: name pins by names with BCM
GPIO.setmode(GPIO.BCM)
#set warnings not shown
GPIO.setwarnings(False)
#27 runs ccw and 22 runs clockwise
GPIO.setup(27, GPIO.OUT)
GPIO.setup(22, GPIO.OUT)
#Variable to hold lock/unlock status
doorStatus = True   #Door is unlocked

#RPi pin configuration
buzzer = Buzzer(19)
pir = MotionSensor(17)
#camera = PiCamera()

# Replace button with door sensor and doorbell
magnet = Button(21)
bell = Button(16)

# Your Account Sid and Auth Token from twilio.com/console
account_sid = 'AC03ab292b02a407be38d94098e0252c10'
auth_token = 'bcb388623480b20f4c518b889fd7493a'
client = Client(account_sid, auth_token)

# Audio files
on          = "alarmOn.wav"
off         = "alarmOff.wav"
select      = "select.wav"
welcome     = "welcome.wav"
armed       = "armed.wav"
disarmed    = "disarmed.wav"
doorbell    = "chime.wav"
#door        = "door.wav"
Liam        = "liam.wav"
police      = "police.wav"
watching    = "watching.wav"

# Color variables
red = [100, 0, 0]
green = [0, 100, 0]
white = [100, 100, 100]
backlight_off = [0, 0, 0]

# Text variables
armedMsg = "Alarm is on"
disarmedMsg = "Alarm is off"
selectMsg = "Press select\nto turn on."
motionMsg = "Motion Detected!"
bellMsg = "Doorbell\nactivated"
doorMsg = "Door opened"

#control variables
armed = False
sensorTriggered = False
lcd.clear()
lcd.color = white
start = time()
#camera.rotation = 180
buzzer.off()
nfcId = ['0x37', '0x1f', '0xee', '0x64']

def alarm_on():
    # To change the initialized variable above, must redefine it here as 'global'
    global armed
    armed = True
    lcd.clear()
    lcd.color = green
    lcd.message = armedMsg
    os.system('aplay ' + on)
    # Give user time to leave the home
    sleep(5)
    if (doorStatus == False):
        operate_door()
    
def alarm_off():
    global armed
    global sensorTriggered
    armed = False
    sensorTriggered = False
    start = time()
    buzzer.off()
    lcd.clear()
    lcd.color = white
    lcd.message = disarmedMsg
    os.system('aplay ' + off)
    lcd.message = selectMsg
    os.system('aplay ' + select)
    if (doorStatus):
        operate_door()
    
def sensors_triggered(sensor):
    global sensorTriggered
    sensorTriggered = True
    lcd.clear()
    lcd.color = red
    body = " "
    if sensor == 'motion':
        start = time()
        lcd.message = motionMsg
        os.system('aplay ' + watching)
        lcd.clear()
        lcd.color = green
        lcd.message = armedMsg
        sensorTriggered = False
        body = "Motion alarm triggered "
    elif sensor == 'magnet':
        sleep(3)
        lcd.message = doorMsg
        buzzer.blink()  #insert audio output code
        os.system('aplay ' + police)
        body = "Door opened! "
    elif sensor == 'bell':
        #start = time()
        os.system('aplay ' + doorbell)
        lcd.message = bellMsg
        print("Pressed bell")
        lcd.clear()
        lcd.color = green
        lcd.message = armedMsg
        sensorTriggered = False
        body = "Doorbell activated "
    message = client.messages \
    .create(
         body = body + '\nLive Stream: http://192.168.1.78:8081\nGoogleDrive: https://drive.google.com/drive/folders/1l5BQu9MZiZZD0nlHf0SJ6OIMtkOCMieK',
         from_='+14055462490',
         to='+14056420612',
    )

    print(message.sid)

def operate_door():
    global doorStatus
    if (doorStatus):
        GPIO.output(27, GPIO.HIGH)
        sleep(3.257)    #(3.257)
        GPIO.output(27, GPIO.LOW)
        doorStatus = False
    else:
        GPIO.output(22, GPIO.HIGH)
        sleep(3.257)    #(3.257)
        GPIO.output(22, GPIO.LOW)
        doorStatus = True

def verify_code():
    #code is set to UP, UP, DOWN, DOWN
    done = True
    while done:
        lcd.clear()
        lcd.message = "Enter code"
        sleep(2)
        if (lcd.up_button):
            lcd.clear()
            lcd.message= "up pressed"
            sleep(2)
            if (lcd.up_button):
                lcd.clear()
                lcd.message = "up pressed"
                sleep(2)
                if (lcd.down_button):
                    lcd.clear()
                    lcd.message = "down pressed"
                    sleep(2)
                    if (lcd.down_button):
                        lcd.clear()
                        lcd.message = "down pressed"
                        done = False
                        return True
        done = False
        return False

operate_door()
os.system('aplay ' + welcome)
lcd.message = selectMsg
os.system('aplay ' + select)
nfcuid = None

while True:
    try:
        if (lcd.select_button == True):
            print("select pressed")
            verified = verify_code()
            if(verified):
                end = time()
                elapsed = end - start
                if armed:
                    alarm_off()
                else:
                    alarm_on()
                
        # Define actions that occur if the alarm is on
        if armed:
            end = time()
            elapsed = end - start
            # If alarm has not yet been triggered, check the sensors
            if (sensorTriggered == False):
                if (magnet.is_pressed == False):
                    sensors_triggered('magnet')
                elif bell.is_pressed:
                    sensors_triggered('bell')
                elif pir.motion_detected:
                    sensors_triggered('motion')
                    #if elapsed >= 10:
                     #   lcd.color = backlight_off
            # If door was triggered, it will continue to sound until user
            # turns it off
            else:
                if lcd.select_button:
                    alarm_off()
    except (KeyboardInterrupt, SystemExit):
        if (doorStatus == False):
            operate_door()
            lcd.display = False
            lcd.color = [0,0,0]
            exit()

    
