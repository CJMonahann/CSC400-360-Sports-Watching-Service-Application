import socket
import cv2, imutils
import numpy as np
import time
import base64
import pickle
import threading
import config
import protocol
import Buffer

s_buffers = {}

class StreamingServer:
     def __init__(self):
          self.address= ("192.168.1.132", 12000) 
          self.BUFFER = 65536
          self.packet_delay = 0.045 #of a second
        
     def start(self):
          server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFFER)
          server.bind(self.address)

          print("The server is ready to recieve")
          while True:
               rec_data, addr = server.recvfrom(self.BUFFER)
               data_struct = pickle.loads(rec_data)
               header = data_struct["header"]
               data = data_struct["data"]
               
               if (header == protocol.HEAD_CS): #collects camera frames from camera server
                    mxid = data["mxid"]


                    if mxid not in s_buffers: #check to see if space is made in global-buffer space fro camera
                         s_buffers[mxid] = Buffer.Buffer() #create camera-specific buffer if not
                         print(s_buffers.keys())

                    s_buffers[mxid].collect(data["frame"]) #send frame data of that camera to its unique buffer
               
               if (header == protocol.HEAD_REQUEST): #if user from Flask application is requesting cam frames
                    print(f"Handling request from - {addr}")
                    port = data["port"] #the specific port of the client's host server. Can be different from tuples address recieved by the server.
                    mxid = data["mxid"]
                    address = (addr[0], port) #addr[0] gets the IP address in the tuple address sent by a client socket
                    thread = threading.Thread(target=handle_Flask_req, args=[address, mxid, self.packet_delay])
                    thread.start()

def handle_Flask_req(addr, mxid, packet_delay):
     sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
     buffer_space = s_buffers[mxid]

     while not(buffer_space.is_empty()):
          curr_packet = buffer_space.release()
          data_struct = {"data": curr_packet}
          sent_data = pickle.dumps(data_struct)
          sending_socket.sendto(sent_data, addr)
          time.sleep(packet_delay) #add delay, as buffer releases frames too fast. Allows client time to process a packet

def main():
    s = StreamingServer()
    s.start()

if __name__ == "__main__":
    main()