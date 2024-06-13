import RPi.GPIO as GPIO
import math
import os
from datetime import datetime
from time import sleep

import paho.mqtt.client as mqtt

# MQTT broker details
broker_address = "REDACTED"
broker_port = 1883
username = "mqtt-user"
password = "REDACTED"

ir_codes = {
    "off": "11100010011010011011001001000000000000000000001001100000000010000000000000000000000000000000000000000000100000011",
    "16": "11100010011010011011001001000000000000000001001001100000011110000000000000000000000000000000000000000000111010011",
    "17": "11100010011010011011001001000000000000000001001001100000001110000000000000000000000000000000000000000000101010011",
    "18": "11100010011010011011001001000000000000000001001001100000010110000000000000000000000000000000000000000000110010011",
    "19": "11100010011010011011001001000000000000000001001001100000000110000000000000000000000000000000000000000000100010011",
    "20": "11100010011010011011001001000000000000000001001001100000011010000000000000000000000000000000000000000000111100011",
    "21": "11100010011010011011001001000000000000000001001001100000001010000000000000000000000000000000000000000000101100011",
    "22": "11100010011010011011001001000000000000000001001001100000010010000000000000000000000000000000000000000000110100011",
    "23": "11100010011010011011001001000000000000000001001001100000000010000000000000000000000000000000000000000000100100011",
    "24": "11100010011010011011001001000000000000000001001001100000011100000000000000000000000000000000000000000000111000011",
    "25": "11100010011010011011001001000000000000000001001001100000001100000000000000000000000000000000000000000000101000011",
    "26": "11100010011010011011001001000000000000000001001001100000010100000000000000000000000000000000000000000000110000011",
    "27": "11100010011010011011001001000000000000000001001001100000000100000000000000000000000000000000000000000000100000011",
    "28": "11100010011010011011001001000000000000000001001001100000011000000000000000000000000000000000000000000000111111101",
    "29": "11100010011010011011001001000000000000000001001001100000001000000000000000000000000000000000000000000000101111101",
    "30": "11100010011010011011001001000000000000000001001001100000010000000000000000000000000000000000000000000000110111101",
    "31": "11100010011010011011001001000000000000000001001001100000000000000000000000000000000000000000000000000000100111101",
}

# This is for revision 1 of the Raspberry Pi, Model B
# This pin is also referred to as GPIO23
INPUT_WIRE = 16

SHORT = 600
MEDIUM = 1500
LONG = 24000
LONGEST = 30000

LAST_RECIEVED = datetime.now()
LAST_COMMAND = ""

GPIO.setmode(GPIO.BOARD)
GPIO.setup(INPUT_WIRE, GPIO.IN)

# We authorize in MQTT but to only send the event on the IR event
client = mqtt.Client()
client.username_pw_set(username, password)
client.connect(broker_address, broker_port)

while True:
    value = 1
    # Loop until we read a 0
    while value:
        value = GPIO.input(INPUT_WIRE)

    # Grab the start time of the command
    startTime = datetime.now()

    # Used to buffer the command pulses
    command = []

    # The end of the "command" happens when we read more than
    # a certain number of 1s (1 is off for my IR receiver)
    numOnes = 0

    # Used to keep track of transitions from 1 to 0
    previousVal = 0

    while True:
        if value != previousVal:
            # The value has changed, so calculate the length of this run
            now = datetime.now()
            pulseLength = now - startTime
            startTime = now

            command.append((previousVal, pulseLength.microseconds))

        if value:
            numOnes = numOnes + 1
        else:
            numOnes = 0

        # 10000 is arbitrary, adjust as necessary
        if numOnes > 10000:
            break
        previousVal = value
        value = GPIO.input(INPUT_WIRE)

    binaryString = "".join(map(lambda x: "1" if x[1] > 900 else "0", filter(lambda x: x[0] == 1, command)))
    if (binaryString == "11100010011010011011001000100000000000000000000100000010000000000000000010000000000000000000000000000000010100000" or binaryString == "11110001001101001101100100010000000000000000000010000001000000000000000001000000000000000000000000000000001010000"):
        print("== Header string! ==")
        continue
    else:
        print(binaryString)

    # Parse the string to match it with the IR codes
    #print(binaryString[43])
    if binaryString in ir_codes.values():
        for key, value in ir_codes.items():
            if value == binaryString:
                print("Received IR code for " + key + " degrees")
                # Check if it is in the last 10 seconds to avoid duplicate commands
                # Also check if it is the same command as the last one
                #if (datetime.now() - LAST_RECIEVED).seconds < 10:
                #    print("Duplicate command. Ignoring")
                #    break
                LAST_RECIEVED = datetime.now()
                LAST_COMMAND = key
                # Wait for a couple of seconds before sending the MQTT message
                #sleep(2)
                # If it is "off", send the mode command
                # If it is "cool", send the temperature command
                if key == "off":
                    client.publish("ac_unit/mode/state", "off")
                else:
                    client.publish("ac_unit/mode/state", "cool")
                    client.publish("ac_unit/temperature/state", key)
                break
    elif len(binaryString) > 43 and binaryString[43] == "0":
        print("AC set off")
        client.publish("ac_unit/mode/state", "off")
    else:
        print("IR code not found in the list")
