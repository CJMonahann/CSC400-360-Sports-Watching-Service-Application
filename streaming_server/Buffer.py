'''
@author: Cornelius Monahan
This class implements the Queue data structure as 'Buffer'.
The buffer will be used in the larger project to store
camera frame data in a FIFO order. These buffers will
be accessed by client sockets to collect available image
frames, which will be sent to the Flask application.

This allows to send frames from the cameras only once the 
cameras have detected motion, which is handled within the
'Server.py' file.
'''

class Buffer:
    def __init__(self):
        self.buffer = [] #uses a list
        self.idle = 0
        self.end = False

    #allows data to be entered into buffer at the beginning
    def collect(self, data):
        self.buffer.insert(0, data)

    #allows the latest image frame to be released from the Buffer
    def release(self):
        if not(self.is_empty()):
            return self.buffer.pop()
        else:
            self.inc_idle()
            return b''
    
    #collects len of buffer - how many data frames as stored
    def len(self):
        return len(self.buffer)
    
    #checks if the Buffer is empty
    def is_empty(self):
        return self.buffer == [] #return True if buffer is empty, else False
    
    #clears buffer of any image frames
    def reset(self):
        self.buffer.clear()

    def inc_idle(self):
        self.idle += 1

    def set_end(self):
        self.end = True

    def reset_idle(self):
        self.idle = 0
        self.end = False
    
    def eval_idle(self, time):
        if not(self.is_empty()):
            self.reset_idle()
        elif self.idle >= time:
            self.set_end()
    
    def get_idle(self):
        return self.end