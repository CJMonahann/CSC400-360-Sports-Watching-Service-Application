import socket
import cv2, imutils
import numpy as np
import time
import base64
import pickle
import threading
import protocol
import Buffer
import os
from dotenv import load_dotenv
from PIL import Image
from datetime import datetime

s_buffers = {}
s_request = {}
EVENTS = {}

class CameraServer:
     def __init__(self, IP, port, path=""):
          self.__address= (IP, port) 
          self.__BUFFER = 68536
          self.__rec_path = path

     def get_address(self):
          return self.__address
     
     def get_path(self):
          return self.__rec_path

     def receive_size(self):
          return self.__BUFFER
     
     def start(self):
          #define constants
          RECV_SIZE = self.receive_size() #defines buffer size from which the server can recieve data
          PATH = self.get_path() #defines the path to the recordings server where event footage is stored

          #configure and start streaming server
          server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_SIZE)
          server.bind(self.get_address())

          print("Camera Only - Server is ready to recieve")
          while True:
               rec_data, addr = server.recvfrom(RECV_SIZE)
               data_struct = pickle.loads(rec_data)
               header = data_struct["header"]
               data = data_struct["data"]

               #start thread to handle recieved data
               h_thread = threading.Thread(target=handle_thread, args=[header, addr, data, PATH])
               h_thread.start()  

class StreamingServer:
     def __init__(self, IP, port, delay=0.08, max=100, path="", idle=30):
          self.__address= (IP, port) 
          self.__BUFFER = 68536
          self.__delay = delay
          self.__max = max
          self.__rec_path = path
          self.__idle = idle

     def get_address(self):
          return self.__address
     
     def get_delay(self):
          return self.__delay
     
     def get_path(self):
          return self.__rec_path
     
     def get_idle(self):
          return self.__idle

     def receive_size(self):
          return self.__BUFFER

     def max_buffer_size(self):
          return self.__max
     
     def start(self):
          #define constants
          RECV_SIZE = self.receive_size() #defines buffer size from which the server can recieve data
          PATH = self.get_path() #defines the path to the recordings server where event footage is stored

          #configure and start streaming server
          server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, RECV_SIZE)
          server.bind(self.get_address())

          thread = threading.Thread(target=send_buffer_frames, args=[s_buffers, s_request, self.get_delay(), self.get_idle()])
          thread.start()

          monitor_thread = threading.Thread(target=monitor_buffers, args=[s_buffers, self.max_buffer_size()])
          monitor_thread.start()

          print("The server is ready to recieve")
          while True:
               rec_data, addr = server.recvfrom(RECV_SIZE)
               data_struct = pickle.loads(rec_data)
               header = data_struct["header"]
               data = data_struct["data"]

               #start thread to handle recieved data
               h_thread = threading.Thread(target=handle_thread, args=[header, addr, data, PATH])
               h_thread.start()  

def handle_thread(header, addr, data, PATH):
     if (header == protocol.HEAD_CS): #collects camera frames from camera server

          #Starts the process of recording frame data. 
          #This thread ends after the frame has been recorded
          rec_thread = threading.Thread(target=rec_event, args=[PATH, data["S_ID"], data["mxid"], data["num_frame"], data["frame"], data["DATE"], data["TIME"]])
          rec_thread.start()
          
          mxid = data["mxid"]

          #one way in which buffer space can be created for camera information 
          create_cam_buffer(s_buffers, mxid)
          s_buffers[mxid].collect(data["frame"]) #send frame data of that camera to its unique buffer
     
     if (header == protocol.HEAD_REQUEST): #if user from Flask application is requesting cam frames
          port = data["port"] #the specific port of the client's host server. Can be different from tuples address recieved by the server.
          mxid = data["mxid"]
          address = (addr[0], port) #addr[0] gets the IP address in the tuple address sent by a client socket

          #create buffer space for camera if not already had
          create_cam_buffer(s_buffers, mxid)

          #create request reqistry for a user trying to access a camera
          if mxid not in s_request:
               s_request[mxid] = []
          
          s_request[mxid].append(address)

     if (header == protocol.HEAD_REC):
          port = data["port"] #the specific port of the client's host server. Can be different from tuples address recieved by the server.
          address = (addr[0], port) #addr[0] gets the IP address in the tuple address sent by a client socket
          rec_req = threading.Thread(target=send_rec, args=[PATH, data["mxid"], address, data["s_id"], data["e_id"], data["date"], data["s_time"], data["e_time"]])
          rec_req.start()

     if(header == protocol.HEAD_UPE):
          s_id = data["s_id"]
          e_id = data["e_id"]
          date = data["date"]
          s_time = data["s_time"]
          e_time = data["e_time"]
          print(f"recieved data - {s_id}, {e_id} - {date} - {s_time} - {e_time}")
          update_events(s_id, e_id, date, s_time, e_time)


def create_cam_buffer(s_buffers, mxid):
           if mxid not in s_buffers: #check to see if space is made in global-buffer space fro camera
                s_buffers[mxid] = Buffer.Buffer() #create camera-specific buffer if not

def send_buffer_frames(s_buffers, s_requests, packet_delay, buff_idle):
     print('Buffer space online')
     sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

     while True:
          try:
               for mxid, buffer in s_buffers.items():
                         buffer.eval_idle(buff_idle)
                         curr_packet = buffer.release()
                         Flag = buffer.get_idle()

                         if mxid in s_requests: #if we have a request for a particular camera
                              data_struct = {"data": curr_packet, "flag": Flag}
                              sent_data = pickle.dumps(data_struct)
                              req_list = s_requests[mxid] #gather all addresses that requested a frame
                              for addr in req_list:
                                   sending_socket.sendto(sent_data, addr)
               time.sleep(packet_delay)
          except:
               continue

def update_events(s_id, e_id, date, s_time, e_time):
     date = date.strftime('%Y-%m-%d')

     if s_id not in EVENTS: #check to see if space is made in global-buffer space fro camera
          EVENTS[s_id] = {}
          #then, update the events, s_id, with sub-directory info pertaining to an event
          date_dict = EVENTS[s_id]
          date_dict[date] = {}

          #to the dictionary of dates, add the time range of the new event
          time_dict = date_dict[date]
          time_dict[f"{s_time}-{e_time}"] = {}

          #put the event name in the final sub directory
          time_dict[f"{s_time}-{e_time}"] = e_id
     else: #site id already had, so just add new entry to the dictionary under the site ID
          #then, update the events, s_id, with sub-directory info pertaining to an event
          date_dict = EVENTS[s_id]
          if date in date_dict: #if we are adding a new event on the same date
               #to the dictionary of dates, add the time range of the new event
               time_dict = date_dict[date]
               time_dict[f"{s_time}-{e_time}"] = {}

               #put the event name in the final sub directory
               time_dict[f"{s_time}-{e_time}"] = e_id
          else: #we have a new date, start a new entry at the site-ID level
               date_dict[date] = {}

               #to the dictionary of dates, add the time range of the new event
               time_dict = date_dict[date]
               time_dict[f"{s_time}-{e_time}"] = {}

               #put the event name in the final sub directory
               time_dict[f"{s_time}-{e_time}"] = e_id

     print(EVENTS)

def monitor_buffers(s_buffers, max_size):
     print('monitoring buffers')

     while True:
          try:
               for mxid, buffer in s_buffers.items():
                    if buffer.len() >= max_size: #if a buffer has reached the max length we have defined
                         buffer.reset() #clear the current buffer to make space in memory
          except:
               continue

def has_event(S_ID, DATE, TIME):
     #check to see whether the site ID is in the dicitonary holding all server EVENTS
     if S_ID in EVENTS: #if the SITE is provided by the streaming server, look for event
          dates_dict = EVENTS[S_ID]
          if DATE in dates_dict:
               times_dict = dates_dict[DATE]
               #iterate through times dict to find the correct time range, and therefore needed event
               for time_range in times_dict.keys():
                    if within_range(time_range, TIME): #checks whether current time is within the time range
                         return time_range, times_dict[time_range] #returns time range and the event ID had on the flask server
     else: #site not had, or not yet had, by streaming server
          return None, None

def within_range(time_range, curr_time):
    new_time = datetime.strptime(curr_time,"%H:%M:%S").time()

    #split the time range string from the dictionary into start time and end time
    s_str, e_str = time_range.split('-')

    #create datetime objects to compare
    s_time = datetime.strptime(s_str,"%H:%M:%S").time()
    e_time = datetime.strptime(e_str,"%H:%M:%S").time()

    #return boolean value as to whether current time is within the range
    return s_time <= new_time <= e_time

def rec_event(PATH, S_ID, mxid, num_frame, data, DATE, TIME):
     #check to see whether we can record event
     time_range, event = has_event(S_ID, DATE, TIME)

     if  time_range and event: #if the event is had by the streaming server from the flask app, create a directory to store video
          time_range = time_range.replace(":", "-") #needed, as we can't create a directory with ':'
          S_dir = os.path.join(PATH, S_ID)
          D_dir = os.path.join(S_dir, DATE)
          T_dir = os.path.join(D_dir, time_range)
          E_dir = os.path.join(T_dir, event)
          cam_dir = os.path.join(E_dir, mxid)
          FRAME = "Frame-"

          #check to see if site directory has been created
          if not(os.path.exists(S_dir) and os.path.isdir(S_dir)): #if the event dir doesnt exist, create it
               os.makedirs(S_dir, exist_ok= True)
          
          #check to see if a date sub-directory within an event exist
          if not(os.path.exists(D_dir) and os.path.isdir(D_dir)): #if the date  dir doesnt exist, create it
               os.makedirs(D_dir, exist_ok= True)

          #check to see if a date sub-directory within an event exist
          if not(os.path.exists(T_dir) and os.path.isdir(T_dir)): #if the time range dir doesnt exist, create it
               os.makedirs(T_dir, exist_ok= True)

          if not(os.path.exists(E_dir) and os.path.isdir(E_dir)): #if the time range dir doesnt exist, create it
               os.makedirs(E_dir, exist_ok= True)

          #check to see if a camera sub-directory within an event exist
          if not(os.path.exists(cam_dir) and os.path.isdir(cam_dir)): #if the time range dir doesnt exist, create it
               os.makedirs(cam_dir, exist_ok= True)

          #add the frame to the appropreate cam sub-directory using the name convention
          curr_frame = FRAME + num_frame + ".jpg"
          curr_path = os.path.join(cam_dir, curr_frame)

          dec_data = base64.b64decode(data, ' /') #this is the frame data

          with open(curr_path, "wb") as frame:
               frame.write(dec_data)
     
def send_rec(PATH, mxid, addr, S_ID, e_id, DATE, s_time, e_time):
     sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
     time_range = f"{s_time}-{e_time}"
     time_range = time_range.replace(":", "-") #needed, as we can't create a directory with ':'
     date = DATE.strftime('%Y-%m-%d')
     S_dir = os.path.join(PATH, S_ID)
     D_dir = os.path.join(S_dir, date)
     T_dir = os.path.join(D_dir, time_range)
     E_dir = os.path.join(T_dir, e_id)
     cam_dir = os.path.join(E_dir, mxid)

     if (os.path.exists(S_dir) and os.path.isdir(S_dir)) and \
     (os.path.exists(D_dir) and os.path.isdir(D_dir)) and \
     (os.path.exists(T_dir) and os.path.isdir(T_dir)) and \
     (os.path.exists(E_dir) and os.path.isdir(E_dir)) and \
     (os.path.exists(cam_dir) and os.path.isdir(cam_dir)): #if the recording is had on the server
          
          frames = return_frames(cam_dir) #a list of all frame names had in the directory
          for img in frames:
               img_path = os.path.join(cam_dir, img)
               with open(img_path, "rb") as data: #convery byte data into np array, encode, and send
                    frame = data.read()
                    np_arr = np.frombuffer(frame, np.uint8) #converts bytes to a NumPy array
                    new_frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR) #the np array
                    res_frame = imutils.resize(new_frame, width=400)
                    _, final_frame = cv2.imencode('.jpg', res_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
                    byte_packet = base64.b64encode(final_frame) #encode so that it fits in UDP buffer space
                    data_struct = {"data": byte_packet, "flag": False}
                    sent_data = pickle.dumps(data_struct)
                    sending_socket.sendto(sent_data, addr)
          sending_socket.close()
                    
     else:
          #send an empty byte package to denote that the directory/reocrdings isn't/arent had
          print("NO RECORDING!!")
          data_struct = {"data": None, "flag": True} #triggers event on web server to tell user no frames are had
          sent_data = pickle.dumps(data_struct)
          sending_socket.sendto(sent_data, addr)
          sending_socket.close()        


def return_frames(directory):
     with os.scandir(directory) as frames:
          return [img.name for img in frames if img.is_file()]

def camera_server():
    load_dotenv()
    IP = os.getenv("SERVER_IP")
    C_Port = int(os.getenv("CAM_PORT"))
    rec_path = str(os.getenv("REC_PATH"))
    s = CameraServer(IP, C_Port, rec_path)
    s.start()

def main():
    #create independent camera server/channel to only recieve camera 
    # frames on a different port than those that accept user request
    CS = threading.Thread(target=camera_server)
    CS.start() #this is used so that the cameras send incoming frames to a seperate port/channel than user requests
    load_dotenv()
    IP = os.getenv("SERVER_IP")
    Port = int(os.getenv("SERVER_PORT"))
    delay = float(os.getenv("DELAY"))
    buffer_size = int(os.getenv("BUFFER_SIZE"))
    rec_path = str(os.getenv("REC_PATH"))
    buffer_idle = float(os.getenv("IDLE"))
    s = StreamingServer(IP, Port, delay, buffer_size, rec_path, buffer_idle)
    s.start() #will handle user request

if __name__ == "__main__":
    main()