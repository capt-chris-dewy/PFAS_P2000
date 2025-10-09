from pymodbus.client import ModbusSerialClient
import time

import P2000_Comms

#GOAL
# read analog sensors attached to PLC Analog Input module via a class implemented in P2000Comms.py

P2_622_baudrate = 19200
P2_622_node_address = 1 
P2_622_parity = 'O' #default for ModbusSerialClient is 'N' ==> none
P2_622_databits = 8 #might mean 8 bits sent per byte (7 is an option and likely for ASCII)
P2_622_stopbits = 1

this_client = ModbusSerialClient("/dev/ttyUSB0", parity=P2_622_parity) #only parameter that differs from default

Photo1 = P2000_Comms.Sensor("Photo1", this_client, 4, 5.0)
Photo2 = P2000_Comms.Sensor("Photo2", this_client, 5, 5.0)
Photo3 = P2000_Comms.Sensor("Photo3", this_client, 6, 5.0)

# Encoder instance definition:
#def __init__(self, name, client, PPR, zero_mb, encoder_pos_mb):

#remember: zero-based addressing, address in Python = address in PLC - 1, ignoring the first digit in PLC-Land for MB data type
Encoder1 = P2000_Comms.Encoder("Mr. Roboto", this_client, 4096, 2, 16)

# Motor instance definition:
# def __init__(self, name, client, PPR, move_on_mb, move_complete_mb, zero_mb, target_pos_mb, 
#              target_velo_mb, target_accel_mb, target_decel_mb):

Motor1 = P2000_Comms.Motor("Mac Demotor", this_client, 5000, Encoder1, 0, 2, 1, 10, 11, 12, 13) #other name ideas: Motorola

#function for checking user input for angular position, velocity, acceleration for motor move command in PLC-ville

def check_string_float(input_string):
  try:
    float(input_string)
    return True

  except ValueError:
    return False

#max_target_velo = 90 #deg/s
#max_target_accel = 90 #deg/s^2
#max_target_decel = 90 #deg/s^2

target_velo = 45 #deg/s
target_accel = 45 #deg/s^2
target_decel = 45 #deg/s^2

Motor1.setVelo(target_velo)
Motor1.setAccel(target_accel)
Motor1.setDecel(target_decel)


Motor1.zeroMotorEncoder()

Motor1.loopFixedSpacing(45) #motor moves on 30 degree intervals at a time, let's see how it goes
