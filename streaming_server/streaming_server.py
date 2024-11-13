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

s_buffers = {}
s_request = {}

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

def handle_thread(header, addr, data, PATH):
     if (header == protocol.HEAD_CS): #collects camera frames from camera server

          #Starts the process of recording frame data. 
          #This thread ends after the frame has been recorded
          rec_thread = threading.Thread(target=rec_event, args=[PATH, data["event_id"], data["mxid"], data["num_frame"], data["frame"]])
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
          print("starting sendback")
          port = data["port"] #the specific port of the client's host server. Can be different from tuples address recieved by the server.
          mxid = data["mxid"]
          event_id = data["id"]
          address = (addr[0], port) #addr[0] gets the IP address in the tuple address sent by a client socket
          rec_req = threading.Thread(target=send_rec, args=[PATH, event_id, mxid, address])
          rec_req.start()

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
          rec_thread = threading.Thread(target=rec_event, args=[PATH, data["event_id"], data["mxid"], data["num_frame"], data["frame"]])
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
          print("starting sendback")
          port = data["port"] #the specific port of the client's host server. Can be different from tuples address recieved by the server.
          mxid = data["mxid"]
          event_id = data["id"]
          address = (addr[0], port) #addr[0] gets the IP address in the tuple address sent by a client socket
          rec_req = threading.Thread(target=send_rec, args=[PATH, event_id, mxid, address])
          rec_req.start()


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

def monitor_buffers(s_buffers, max_size):
     print('monitoring buffers')

     while True:
          try:
               for mxid, buffer in s_buffers.items():
                    if buffer.len() >= max_size: #if a buffer has reached the max length we have defined
                         buffer.reset() #clear the current buffer to make space in memory
          except:
               continue

def rec_event(PATH, event_id, mxid, num_frame, data):
     #define various paths
     event_dir = os.path.join(PATH, event_id)
     cam_dir = os.path.join(event_dir, mxid)
     FRAME = "Frame-"

     #check to see if event directory has been created
     if not(os.path.exists(event_dir) and os.path.isdir(event_dir)): #if the event dir doesnt exist, create it
          os.makedirs(event_dir, exist_ok= True)
     
     #check to see if a camera sub-directory within an event exist
     if not(os.path.exists(cam_dir) and os.path.isdir(cam_dir)): #if the event dir doesnt exist, create it
          os.makedirs(cam_dir, exist_ok= True)

     #add the frame to the appropreate cam sub-directory using the name convention
     curr_frame = FRAME + num_frame + ".jpg"
     curr_path = os.path.join(cam_dir, curr_frame)

     dec_data = base64.b64decode(data, ' /') #this is the frame data

     with open(curr_path, "wb") as frame:
          frame.write(dec_data)
     
def send_rec(PATH, event_id, mxid, addr):
     sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

     #check to see if the event directory, and needed camera sub-directory exist
     event_dir = os.path.join(PATH, event_id)
     cam_dir = os.path.join(event_dir, mxid)

     if (os.path.exists(event_dir) and os.path.isdir(event_dir)) and \
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
                    data_struct = {"data": byte_packet}
                    sent_data = pickle.dumps(data_struct)
                    sending_socket.sendto(sent_data, addr)
                    
     else:
          #send an empty byte package to denote that the directory/reocrdings isn't/arent had
          data_struct = {"data": b""} #triggers event on web server to tell user no frames are had
          sent_data = pickle.dumps(data_struct)
          sending_socket.sendto(sent_data, addr)          


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