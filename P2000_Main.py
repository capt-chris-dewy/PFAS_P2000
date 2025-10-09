#GUI + Program Control
import tkinter as tk
from queue import Empty, Queue
from threading import Event, Thread
import sys

#MODBUS + Timing Program Control (will probably outmode time.sleep() for other things above soon)
from pymodbus.client import ModbusSerialClient
import time

#custom modules
import P2000_Comms #my module for all of our PLC hardware
import TK_ekchew #u/ekchew on reddit's "safe" method of interacting with TKInter GUI using threads and queues
import TK_Objects #reusable GUI objects I wanted to include

#objects representing important hardware
#-----------------------------------------------------------------------------------------------------------------------------
P2_622_baudrate = 19200
P2_622_node_address = 1 
P2_622_parity = 'O' #default for ModbusSerialClient is 'N' ==> none
P2_622_databits = 8 #might mean 8 bits sent per byte (7 is an option and likely for ASCII)
P2_622_stopbits = 1

this_client = ModbusSerialClient("/dev/ttyUSB0", parity=P2_622_parity) #only parameter that differs from default

Sensor1 = P2000_Comms.Sensor("Photoresistor 1", this_client, 4, 5.0)
Sensor2 = P2000_Comms.Sensor("Photoresistor 2", this_client, 5, 5.0)
Sensor3 = P2000_Comms.Sensor("Photoresistor 3", this_client, 6, 5.0)

SensorArray = P2000_Comms.Sensor.LIST

#remember: zero-based addressing, address in Python = address in PLC - 1, ignoring the first digit in PLC-Land for MB data type
Encoder1 = P2000_Comms.Encoder("Mr. Roboto", this_client, 4096, 2, 16)
Motor1 = P2000_Comms.Motor("Mac Demotor", this_client, 5000, Encoder1, 0, 2, 1, 10, 11, 12, 13) #other name ideas: Motorola

AngleIncrement = 360/78.0

target_velo = 4 #deg/s
target_accel = 45 #deg/s^2
target_decel = 45 #deg/s^2

Motor1.setVelo(target_velo)
Motor1.setAccel(target_accel)
Motor1.setDecel(target_decel)

#initiating tkinter root
#-----------------------------------------------------------------------------------------------------------------------------
root = tk.Tk()
root.geometry("1200x800") #hoping these will automatically also change the dimensions of the application frame created below

#app class inherits from TKInter "frame" for grouping GUI objects
app = TK_ekchew.App(master=root)

#found out how to set the foreground / background post - object creation at this reference
#https://docs.python.org/3/library/tkinter.html#threading-model (Handy Reference, Setting Options) <-- gotta scroll down a ways


SenseFrame = TK_Objects.SensorFrame(app, SensorArray) # "master frame" is the app object, also needs array of sensor objects   
SpinnyWheelFrame = TK_Objects.MotorFrame(app, Motor1) 

#places orange rectangle of given dimensions on the center of the screen: perfection
#testFrame = tk.Frame(root, bg="orange", width=200, height=150)
#testFrame.place(relx=0.5, rely=0.5, anchor="center")

#main program:
#-----------------------------------------------------------------------------------------------------------------------------
def mainThread(): #originally a threadFn contained as a method in the "app" class in TK_ekchew.py 
  while True:
    app.make_gui_call(SenseFrame.updateValues) #updates entire GUI Object with new values based on array of sensor objects
    app.make_gui_call(SpinnyWheelFrame.encoderPosUpdate)

    #all of these work, even the auto activator! 
    #print(app.make_gui_call(SpinnyWheelFrame.getMoveActivator))         
    #print(app.make_gui_call(SpinnyWheelFrame.getZeroActivator))         
    #print(app.make_gui_call(SpinnyWheelFrame.getAutoActivator))         
    #print(app.make_gui_call(SpinnyWheelFrame.convertMotorEntry))             

    if app.make_gui_call(SpinnyWheelFrame.getMoveActivator) == True:
      if app.make_gui_call(SpinnyWheelFrame.convertMotorEntry) != None:
        #start a new thread, moving the motor to the position in the field
        targetPosition = app.make_gui_call(SpinnyWheelFrame.convertMotorEntry)
        move_abs_thread = Thread(target=Motor1.absolute_move, args=(targetPosition,))
        move_abs_thread.start()
 
        app.make_gui_call(SpinnyWheelFrame.setMoveActivator, False) #so that the move doesn't repeat itself each time
                                                                    #the loop runs
    
    if app.make_gui_call(SpinnyWheelFrame.getZeroActivator) == True:
      zeroing_thread = Thread(target=Motor1.zeroMotorEncoder)
      zeroing_thread.start()
      
      app.make_gui_call(SpinnyWheelFrame.setMotorEntry, 0.0) #so that the move doesn't repeat itself each time
      app.make_gui_call(SpinnyWheelFrame.setZeroActivator, False)
      
    if (app.make_gui_call(SpinnyWheelFrame.getAutoActivator) == True):
      autoplay_thread = Thread(target=Motor1.loopFixedSpacing, args=(AngleIncrement,))
      Motor1.setAutoFlag() #bit bang to get started up?
      Motor1.resetAutoFlag() 
      autoplay_thread.start()
      app.make_gui_call(SpinnyWheelFrame.setAutoActivator, False)         
    
    """
    if (app.make_gui_call(SpinnyWheelFrame.getAutoOngoing) == True and 
      app.make_gui_call(SpinnyWheelFrame.getAutoShutoff) == True and
      Motor1.PAUSE_AUTO_FLAG.is_set() == True): #pause thread after next move
      
      Motor1.resetAutoFlag() #pause thread after next move
      
    if (app.make_gui_call(SpinnyWheelFrame.getAutoOngoing) == True and 
      app.make_gui_call(SpinnyWheelFrame.getAutoShutoff) == False and
      Motor1.PAUSE_AUTO_FLAG.is_set() == False):
      
      Motor1.setAutoFlag() #resume thread
    """
    
    if (app.make_gui_call(SpinnyWheelFrame.getAutoOngoing) == True):
      print("is move complete? " + str(Motor1.isMoveComplete()))
      if(Motor1.isMoveComplete() == True):
        #very quick bit bang of the flag blocking each iteration of the loop -- basically the secondary thread controlling
        #the loop motion was allowed to iterate through its entire loop by the time the flag blocking its progress got 
        #reset here after another iteration of this loop -- not sure if my code is the most proper, but it works
        Motor1.setAutoFlag()
        Motor1.resetAutoFlag()
 
    if (app.make_gui_call(SpinnyWheelFrame.getAutoOngoing) == True and 
      Motor1.LOOP_COMPLETION_FLAG == True):

      app.make_gui_call(SpinnyWheelFrame.autoplay_button_text.set, "Play")
      app.make_gui_call(SpinnyWheelFrame.setAutoOngoing, False)

app.set_threadFn(mainThread)

#according to original reddit post, mainloop() of TKInter GUI should be started after the masterThread above
#should really put the hyperlink to the source here:
app.thread.start()
app.mainloop()
