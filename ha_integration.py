import os
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

def call_irsend(code):
    os.system("./irsend " + code)


current_temperature = 21.0
current_power_state = "off"

# AC unit details
ac_unit_topic = "homeassistant/climate/ac_unit/climate"
ac_unit_config = {
    "name": "AC Unit",
    "command_topic": "ac_unit/set",
    "temperature_command_topic": "ac_unit/temperature/set",
    "temperature_state_topic": "ac_unit/temperature/state",
    "power_command_topic": "ac_unit/power/set",
    "power_state_topic": "ac_unit/power/state",
    "mode_command_topic": "ac_unit/mode/set",
    "mode_state_topic": "ac_unit/mode/state",
    "temperature_unit": "C",
    "min_temp": 16.0,
    "max_temp": 31.0,
    "precision": 1.0,
}

# MQTT client setup
client = mqtt.Client()

def on_connect(client, userdata, flags, rc):
    print("Connected to MQTT broker with result code " + str(rc))
    client.subscribe(ac_unit_config["temperature_command_topic"])
    client.subscribe(ac_unit_config["power_command_topic"])
    client.subscribe(ac_unit_config["mode_command_topic"])

def on_message(client, userdata, msg):
    global current_temperature
    global current_power_state
    if msg.topic == ac_unit_config["temperature_command_topic"]:
        current_temperature = float(msg.payload)
        # Check if the state is "cool"
        if current_power_state == "off":
            print("AC unit is off. Won't set temperature")
            return
        # Send temperature to the AC unit using irsend program
        print("Setting temperature to " + str(current_temperature))
        # Get the IR code to send for the temperature
        ir_code = ir_codes[str(int(current_temperature))]
        call_irsend(ir_code)
        # Publish the temperature state
        client.publish(ac_unit_config["temperature_state_topic"], current_temperature)
    elif msg.topic == ac_unit_config["mode_command_topic"]:
        current_power_state = str(msg.payload, "utf-8")
        print("Setting mode to " + current_power_state)
        # If it is "off", send the off IR code
        # If it is "cool", send the last temperature IR code
        if current_power_state == "off":
            call_irsend(ir_codes["off"])
        elif current_power_state == "cool":
            call_irsend(ir_codes[str(int(current_temperature))])
        # Publish the mode state
        client.publish(ac_unit_config["mode_state_topic"], current_power_state)
        client.publish(ac_unit_config["temperature_state_topic"], current_temperature)

client.on_connect = on_connect
client.on_message = on_message

# Connect to MQTT broker
client.username_pw_set(username, password)
client.connect(broker_address, broker_port, 60)

# Set the initial state of the AC unit
call_irsend(ir_codes["off"])
client.publish(ac_unit_config["mode_state_topic"], "off")
client.publish(ac_unit_config["temperature_state_topic"], current_temperature)


# Start MQTT loop
client.loop_forever()
