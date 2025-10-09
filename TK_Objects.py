import tkinter as tk
import P2000_Comms

class SensorFrame():
  def __init__(self, masterFrame, senseArray):
    self.masterFrame = masterFrame
    self.senseArray = senseArray 
    self.label_frame = tk.LabelFrame(self.masterFrame, text="Sensor Readings",font=("Arial", 28))
    #self.label_frame = tk.LabelFrame(self.masterFrame, text="Sensor Readings", padx=10, pady=10)
    self.label_frame.place(relx=0.075, rely=0.25, anchor="w") #placed at top left with some lil offsets
    #self.label_frame.pack(side="left", anchor="w") #aligns sensor frame to left of (master frame?) with contents
                                                   #"anchored" to the left / left-justified
    self.label_frame["bg"] = "yellow"
      
    self.sensor_titles = []
    self.sensor_values = [] 
    self.labels = [] #the variables where these are stored, write to these to change display
    self.labelTexts = []

    for i in range(len(self.senseArray)):
      self.sensor_titles.append(self.senseArray[i].name)
      self.sensor_values.append(0) #temporary placeholder, this array will get continuously updated I hope
      
      label_text_i = tk.StringVar()
      label_text_i.set(self.senseArray[i].name + " = " + str(0) + " V")
      
      self.labelTexts.append(label_text_i)
      
      label_i = tk.Label(self.label_frame, textvariable=(label_text_i), font=("Arial", 20)) 
      label_i.pack(padx=10, pady=10)
      label_i["bg"] = "yellow"
      self.labels.append(label_i)

  def updateValues(self):
    for i in range(len(self.senseArray)):
      self.sensor_values[i] = self.senseArray[i].readVolts() #update statement
      self.labelTexts[i].set(self.sensor_titles[i] + " = " + str(self.sensor_values[i]) + " V")
  
  #old version of the above function but I may have been on crack (turns out the new version works just fine)

  #def updateValues(self, sensorArray):
  #  for i in range(len(sensorArray)):
  #    for j in range(len(self.sensor_titles)):
  #      if self.sensor_titles[j] == sensorArray[i].name: #sensor at i in main file matches sensor at j in here
  #        self.sensor_values[j] = sensorArray[i].readVolts() #update statement
  #        self.labelTexts[j].set(self.sensor_titles[j] + " = " + self.sensor_values[j] + " V")
  #        break 
  
#may make multiple of these for different motors down the line, but these can definitely be created in the main
#file on an individual basis with individual customizations... for now just focusing on the wheel-turning

class MotorFrame(): #sounds way cooler than it is
  def __init__(self, masterFrame, MotorOBJ):
    self.masterFrame = masterFrame
    self.MotorOBJ = MotorOBJ

    self.autoplay_activate = False
    self.autoplay_ongoing = False
    self.autoplay_shutoff = False
    self.zero_activate = False
    self.motion_activate = False

    #all of the TKInter stuff... sorry for the mess!
    self.label_frame = tk.LabelFrame(self.masterFrame, text="Motor 1 (Wheel Motor)",font=("Arial", 28)) 
    self.label_frame.place(relx=0.925, rely=0.25, anchor="e") #placed at top left with some lil offsets
    self.label_frame["bg"] = "pink"
 
    self.autoplay_label_text = tk.StringVar()
    self.autoplay_label_text.set("Initiate Automated Testing --> ")
    self.autoplay_label = tk.Label(self.label_frame, textvariable=(self.autoplay_label_text), font=("Arial", 20))
    self.autoplay_label.grid(row = 0, column = 0, padx = 0, pady = 10)
    
    self.autoplay_button_text = tk.StringVar()
    self.autoplay_button_text.set("Play")
    self.autoplay = tk.Button(self.label_frame, textvariable=(self.autoplay_button_text), font=("Arial", 20), 
                              command=self.autoplay_toggle)
    self.autoplay.grid(row = 0, column = 1, padx=0, pady=15)
    
    self.entry1_label_text = tk.StringVar()
    self.entry1_label_text.set("Manual Motor Position = ")
    self.entry1_label = tk.Label(self.label_frame, textvariable=(self.entry1_label_text), font=("Arial", 20))
    self.entry1_label.grid(row = 1, column = 0, padx = 5, pady = 10)
    
    self.entry1 = tk.Entry(self.label_frame, font=("Arial", 20))
    self.entry1.grid(row = 1, column = 1)

    self.motor1_zerobutton = tk.Button(self.label_frame, text="Zero", font=("Arial", 16), command=self.zero_command)
    self.motor1_zerobutton.grid(row = 2, column = 0, padx=0, pady=15)
    
    self.entry1_moveabs = tk.Button(self.label_frame, text="Move", font=("Arial", 16), command=self.move_command)
    self.entry1_moveabs.grid(row = 2, column = 1, padx=0, pady=15)

    self.encoder_pos_text = tk.StringVar()
    self.encoder_pos_text.set("Encoder Pos = default value")
    self.encoder_pos_label = tk.Label(self.label_frame, textvariable=(self.encoder_pos_text), font=("Arial", 20))
    self.encoder_pos_label.grid(row = 3, column = 0, padx = 15, pady = 10)

  def check_string_float(self, input_string):
    try:
      float(input_string)
      return True

    except ValueError:
      return False  

  #goal: convert the text input into the entry field for new motor position into a data type usable by move function
  def convertMotorEntry(self):
    raw_text = self.entry1.get()
    if self.check_string_float(raw_text) == True and float(raw_text) >= 0.0 and float(raw_text) <= 360.0:
      return float(raw_text)       
    else:
      print("error: string in entry field could not be converted to a float, or float value is out of range (0-360 for wheel)") 
      return None
  
  def setMotorEntry(self, entry_nouveau):
    #hopefully there's no need to check if it's a float and converting back to a string is easy
    entry_string = ""
    if isinstance(entry_nouveau, str): #checking if the input is a string -- otherwise do the conversion
      entry_string = entry_nouveau
    else:
      entry_string = str(entry_nouveau)
    
    #clears current content of entry widget by deleting every character
    self.entry1.delete(0, tk.END)
    self.entry1.insert(0, entry_string) #starting at index 0, insert the new string

  def encoderPosUpdate(self):    
    encoderUpdate = self.MotorOBJ.EncoderOBJ.readEncoderPos()
    self.encoder_pos_text.set("Encoder Pos = " + str(encoderUpdate))
    
  def getAutoActivator(self):
    return self.autoplay_activate
 
  def getAutoOngoing(self):
    return self.autoplay_ongoing
  
  def getAutoShutoff(self):
    return self.autoplay_shutoff

  def setAutoActivator(self, new_state):
    self.autoplay_activate = new_state
  
  def setAutoOngoing(self, new_state):
    self.autoplay_ongoing = new_state
  
  def autoplay_toggle(self):
    if self.autoplay_ongoing == True:
      self.autoplay_button_text.set("Play")
      #self.autoplay_shutoff = True
    else:
      self.autoplay_activate = True
      self.autoplay_ongoing = True
      #self.autoplay_shutoff = False #reset this fella from previous shutoffs, potentially
      self.autoplay_button_text.set("Pause")

  def getMoveActivator(self):
    return self.motion_activate
  
  def setMoveActivator(self, new_state):
    self.motion_activate = new_state

  def move_command(self):
    if self.MotorOBJ.isMoveComplete() == True: #check if the motor is not in motion
      self.motion_activate = True 
    else:
      pass
  
  def getZeroActivator(self):
    return self.zero_activate
  
  def setZeroActivator(self, new_state):
    self.zero_activate = new_state
  
  def zero_command(self):
    if self.MotorOBJ.isMoveComplete() == True: #check if the motor is not in motion
      self.zero_activate = True
    else:
      pass
