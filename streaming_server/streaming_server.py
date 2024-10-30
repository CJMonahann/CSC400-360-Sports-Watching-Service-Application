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

class StreamingServer:
     def __init__(self, address, port, delay):
          self.address= (address, port) 
          self.BUFFER = 65536
          self.delay = delay

     def buffer_size(self):
          return self.BUFFER
     
     def get_delay(self):
          return self.delay
     
     def create_cam_buffer(self, s_buffers, mxid):
           if mxid not in s_buffers: #check to see if space is made in global-buffer space fro camera
                s_buffers[mxid] = Buffer.Buffer() #create camera-specific buffer if not
        
     def start(self):
          server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.buffer_size())
          server.bind(self.address)

          thread = threading.Thread(target=send_buffer_frames, args=[s_buffers, s_request, self.get_delay()])
          thread.start()
          
          #create error frame message
          #ERROR_FRAME = pack_error_frame()

          print("The server is ready to recieve")
          while True:
               rec_data, addr = server.recvfrom(self.buffer_size())
               data_struct = pickle.loads(rec_data)
               header = data_struct["header"]
               data = data_struct["data"]
               
               if (header == protocol.HEAD_CS): #collects camera frames from camera server
                    mxid = data["mxid"]

                    #one way in which buffer space can be created for camera information 
                    self.create_cam_buffer(s_buffers, mxid)

                    s_buffers[mxid].collect(data["frame"]) #send frame data of that camera to its unique buffer
               
               if (header == protocol.HEAD_REQUEST): #if user from Flask application is requesting cam frames
                    print(f"Handling request from - {addr}")
                    port = data["port"] #the specific port of the client's host server. Can be different from tuples address recieved by the server.
                    mxid = data["mxid"]
                    address = (addr[0], port) #addr[0] gets the IP address in the tuple address sent by a client socket

                    #create buffer space for camera if not already had
                    self.create_cam_buffer(s_buffers, mxid)

                    #create request reqistry for a user trying to access a camera
                    if mxid not in s_request:
                         s_request[mxid] = []
                    
                    s_request[mxid].append(address)


def send_buffer_frames(s_buffers, s_requests, packet_delay):
     print('Buffer space online')
     sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

     while True:
          try:
               for mxid, buffer in s_buffers.items():
                         curr_packet = buffer.release()

                         if mxid in s_requests: #if we have a request for a particular camera
                              data_struct = {"data": curr_packet}
                              sent_data = pickle.dumps(data_struct)
                              req_list = s_requests[mxid] #gather all addresses that requested a frame
                              for addr in req_list:
                                   sending_socket.sendto(sent_data, addr)
               time.sleep(packet_delay)
          except:
               continue

def main():
    load_dotenv()
    IP = os.getenv("SERVER_IP")
    Port = int(os.getenv("SERVER_PORT"))
    delay = float(os.getenv("DELAY"))
    s = StreamingServer(IP, Port, delay)
    s.start()

if __name__ == "__main__":
    main()