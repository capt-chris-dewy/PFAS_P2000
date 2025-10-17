from pymodbus.client import ModbusSerialClient
from threading import Event, Thread
import time

class Sensor:

  RES = 65535.0 #this number is only a float so that, when doing actual conversions from PLC data
                #things aren't rounded to integers
 
  LIST = []
   
  def __init__(self, name, client, mb_addr, VREF):    
    self.name = name
    self.client = client
    self.mb_addr = mb_addr #address for register containing 16-bit uint ADC value
    self.VREF = VREF #reference / "max voltage" that sensor could occupy -- for the P2000 analog module,
                     #                                                      this can be either 5 or 10V DC
    
    Sensor.LIST.append(self)
    
  def readADC(self):
    #example from READ_ANALOG_SERIAL_65535.py
    #Photo_ADC = laptop_client.read_holding_registers(PhotoresistorADC_MB_ADDR, count=1).registers[0]

    PLC_reply = self.client.read_holding_registers(self.mb_addr, count=1)
    ADC = PLC_reply.registers[0]
    return ADC

  def readVolts(self):
    thisADC = self.readADC()
    thisVoltage = thisADC * self.VREF / Sensor.RES
    return round(thisVoltage, 3)

class Encoder:

  def __init__(self, name, client, PPR, zero_mb, encoder_pos_mb):
    self.client = client
    self.name = name
    self.PPR = PPR
    self.zero_mb = zero_mb
    self.encoder_pos_mb = encoder_pos_mb
 
  #any zeroing of the motor should also zero the encoder, so the address for zeroing both is the same
  #this means that zeroing the position should probably only be implemented in only one of the two classes
  #could define a class that simply creates a motor-encoder pair with zeroing functionality...
  #sounds slightly painful tho

  def readEncoderPos(self):
    PLC_reply = self.client.read_holding_registers(self.encoder_pos_mb, count=1)
    encoder_pulses = PLC_reply.registers[0]
    encoder_degrees = round(encoder_pulses*(360.0/self.PPR), 2)
    return encoder_degrees
 

class Motor:

  LIST = []
  
  def __init__(self, name, client, PPR, EncoderOBJ, move_on_mb, move_complete_mb, zero_mb, target_pos_mb, 
               target_velo_mb, target_accel_mb, target_decel_mb):

    self.name = name
    self.client = client
    self.PPR = PPR
    self.EncoderOBJ = EncoderOBJ #if there is an encoder associated with the motor, you can pass it as an argument

    self.move_on_mb = move_on_mb
    self.move_complete_mb = move_complete_mb
    self.zero_mb = zero_mb
    
    self.target_pos_mb = target_pos_mb #post move, previous target position is current position according to motor
    
    #default target velocities / accelerations for larger moves i.e. not loops
    self.default_velo = 0
    self.default_accel = 0
    self.default_decel = 0
    
    self.loop_velo = 0
    self.loop_accel = 0
    self.loop_decel = 0
    
    self.target_velo_mb = target_velo_mb
    self.target_accel_mb = target_accel_mb
    self.target_decel_mb = target_decel_mb
  
    self.PAUSE_AUTO_FLAG = Event()
    self.KILLED_FLAG = False
    self.LOOP_COMPLETION_FLAG = False

    self.ABS_MOVE_COUNT = 0 #increment every time absolute_move function runs, which happens also repeatedly
                            #during the automated loop
  
    Motor.LIST.append(self)

  #should be 1 in its "natural state" in between moves --- 0 while the actual move is happening 
  def isMoveComplete(self):
    move_complete = self.client.read_coils(self.move_complete_mb, count=1).bits[0]
    return move_complete

  #setter functions for setting default velocity and acceleration during the larger moves
    
  def setDefaultVelo(self, new_default):
    self.default_velo = new_default
  
  def setDefaultAccel(self, new_default):
    self.default_accel = new_default
  
  def setDefaultDecel(self, new_default):
    self.default_decel = new_default
    
  #set kinematics for smaller incremental loop going from hole to hole

  def setLoopVelo(self, new_loop):
    self.loop_velo = new_loop
  
  def setLoopAccel(self, new_loop):
    self.loop_accel = new_loop
  
  def setLoopDecel(self, new_loop):
    self.loop_decel = new_loop

  #for actually setting these kinematics in the PLC via MODBUS

  def setVelo(self, target_velo):
    rounded_target = round(target_velo, 2) #to two decimal places
    rounded_target_mb = rounded_target*100
    print("target velo for move is: " + str(rounded_target))
    #print("sending: " + str(rounded_target_mb) + " 16-bit uint MB register to PLC")    

    self.client.write_register(self.target_velo_mb, rounded_target_mb)
  
  def setAccel(self, target_accel):
    rounded_target = round(target_accel, 2) #to two decimal places
    rounded_target_mb = rounded_target*100
    print("target accel for move is: " + str(rounded_target))
    #print("sending: " + str(rounded_target_mb) + " 16-bit uint MB register to PLC")    

    self.client.write_register(self.target_accel_mb, rounded_target_mb)
  
  def setDecel(self, target_decel):
    rounded_target = round(target_decel, 2) #to two decimal places
    rounded_target_mb = rounded_target*100
    print("target decel for move is: " + str(rounded_target))
    #print("sending: " + str(rounded_target_mb) + " 16-bit uint MB register to PLC")    

    self.client.write_register(self.target_decel_mb, rounded_target_mb)
  
  def absolute_move(self, target_angle):
    if target_angle < 0 or target_angle > 360:
      print("invalid position given: target angle for absolute move must be between 0 and 360 degrees")
      return
    
    rounded_target = round(target_angle, 2)  
    rounded_target_mb = int(rounded_target*100) #thought process: for 0.01 precision scaled to 0-65535 for data transfer
                                                #on a value 0-360, multiplying by 100 works fabulously
    
    #set scaled / modified input to function to target position modbus, converted back into actual angle by 
    #PLC software ladder code
    self.client.write_register(self.target_pos_mb, rounded_target_mb)
    
    #print("target pos mb: " + str(self.client.read_holding_registers(self.target_pos_mb)))
    
    #from previous moves, this coil may still be active -- turn it off just in case, every time
    self.client.write_coil(self.move_on_mb, False)   
    #then bit bang to start actual motion
    self.client.write_coil(self.move_on_mb, True)  

    self.ABS_MOVE_COUNT = self.ABS_MOVE_COUNT + 1
    print("move count: " + str(self.ABS_MOVE_COUNT))
  def setAutoFlag(self):
    #sets the flag to be true so that any "wait" statement encountered by the thread will be ignored
    self.PAUSE_AUTO_FLAG.set()
  
  def resetAutoFlag(self):
    #reset the flag so that the thread pauses at the involved wait statements
    self.PAUSE_AUTO_FLAG.clear()
  
  def loopFixedSpacing(self, spacing):
    
    self.setVelo(self.loop_velo) # deg /s 
    self.setAccel(self.loop_accel) # deg /s^2
    self.setDecel(self.loop_decel) # deg /s^2

    current_target = 0
    i = 0
    
    self.LOOP_COMPLETION_FLAG = False #since the loop was last complete and you're starting fresh, let's do this

    while True:
      current_target = spacing*(i+1)
  
      if current_target > 360.0:
        break

      print("next target position is: " + str(current_target))
      self.absolute_move(current_target)
      
      #while True:
      #  is_motion_complete = self.isMoveComplete()
      #  
      #  if is_motion_complete == True:
      #    break
      
      i = i + 1
 
      self.PAUSE_AUTO_FLAG.wait() #should operate as normal if flag is "set", but when "reset" will pause the thread

      if self.KILLED_FLAG == True: #reset parameters so that when thread starts back up it can go back to zero
        self.KILLED_FLAG = False #reset for the next thread run for this motor before killing this one
        return
       
    print("iterations / number of moves = " + str(i))  
  
    self.LOOP_COMPLETION_FLAG = True
    
    #return to normal values
    self.setVelo(self.default_velo) # deg /s 
    self.setAccel(self.default_accel) # deg /s^2
    self.setDecel(self.default_decel) # deg /s^2

  def zeroMotorEncoder(self): 
    self.client.write_coil(self.zero_mb, True)
    #back to zero so that we don't accidentally set the next position to zero as well (giving you, the reader, a thumbs up)
    self.client.write_coil(self.zero_mb, False)
    
