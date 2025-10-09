#code mostly stolen from Gemini-generated "LabelFrameEx.py" in another folder near this one
import tkinter as tk
import TK_Objects

root = tk.Tk()
root.title("Testing TK_Objects.py module I've created")
root.geometry("600x400")

test_sensor_frame = TK_Objects.SensorFrame(root, 3)
print(test_sensor_frame.numSensors)
print(test_sensor_frame.masterFrame)
print(test_sensor_frame.label_frame)

root.mainloop()



"""For reference:

import tkinter as tk

root = tk.Tk()
root.title("LabelFrame Example")

# Create a LabelFrame widget
my_labelframe = tk.LabelFrame(root, text="My Grouped Widgets", padx=10, pady=10)
my_labelframe.pack(pady=20, padx=20)

# Add widgets inside the LabelFrame
label1 = tk.Label(my_labelframe, text="Item 1")
label1.pack()

entry1 = tk.Entry(my_labelframe)
entry1.pack()
"""
