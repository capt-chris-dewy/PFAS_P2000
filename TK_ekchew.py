import tkinter as tk
from queue import Empty, Queue
from threading import Event, Thread
import sys

import TK_Objects

class _GUICallData:

    def __init__(self, fn, args, kwargs):
        self.fn = fn
        self.args = args
        self.kwargs = kwargs
        self.reply = None
        self.reply_event = Event()

class App(tk.Frame):

    def __init__(self, master, threadFn=None): #thread function can be none initially and assigned later
        super().__init__(master)
        #self.place(x=0,y=0, width=600, height=400) #places application frame (which everything else will be a child of)
                                                   #at the top left of the canvas / window -- it will hopefully
                                                   #also inherit those same dimensions to fill the whole thing

        self.pack(fill=tk.BOTH, expand=True) #apparently this will do the job of filling the canvas, and may even
                                             #work when full-screened

        self["bg"] = "green"
        self.call_queue = Queue()
        self.bind("<<gui_call>>", self.gui_call_handler) #this code creates a custom "gui call" event that runs the handler
        self.threadFn = threadFn
        self.thread = Thread(target=self.threadFn, daemon=True) #target= function that runs once thread is spawned
                                                                #self.thread.start() would actually kick it off
                                                                #daemon=True means that the program can end even if this
                                                                #thread never finishes execution 
    def make_gui_call(self, fn, *args, **kwargs):
        data = _GUICallData(fn, args, kwargs)
        self.call_queue.put(data) 
        self.event_generate("<<gui_call>>", when="tail") #tail option, gui call enters back of queue, has to wait in line
        data.reply_event.wait() #event object contains a flag that when true, will "unblock"/allow program to continue
                                #progressing. set() will make the flag true, clear() will make it false

        return data.reply #initially reply is "None", gets filled with return data of function passed to gui call

    def gui_call_handler(self, event):
        try:
            while True:
                data = self.call_queue.get_nowait()
                data.reply = data.fn(*data.args, *data.kwargs)
                data.reply_event.set()
        except Empty:
            pass

    def set_threadFn(self, new_threadFn):
      self.threadFn = new_threadFn
      self.thread = Thread(target=self.threadFn, daemon=True) #have to reset the thread object as well
       
