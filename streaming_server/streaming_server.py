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
          self.address= ("192.168.1.132", 1200) 
          self.BUFFER = 65536
        
     def start(self):
          server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFFER)
          server.bind(self.address)

          print("The server is ready to recieve")
          v = 0
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
               
               if (header == protocol.HEAD_REQUEST and v <= 0): #if user from Flask application is requesting cam frames
                    v += 1
                    mxid = data["mxid"]
                    thread = threading.Thread(target=handle_Flask_req, args=[addr, mxid])
                    thread.start()

def handle_Flask_req(addr, mxid):
     sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
     buffer_space = s_buffers[mxid]

     while not(buffer_space.is_empty()):
          curr_packet = buffer_space.release()
          dec_data = base64.b64decode(curr_packet, ' /')
          np_data = np.fromstring(dec_data, dtype=np.uint8)
          frame = cv2.imdecode(np_data, 1)
          cv2.imshow(mxid, frame)
          if cv2.waitKey(1) == ord('q'):
               break
          #sending_socket.sendto(packet, addr)
          time.sleep(0.05)

def collect_cam_frame(packet):
     dec_data = base64.b64decode(packet, ' /')
     np_data = np.fromstring(dec_data, dtype=np.uint8)
     frame = cv2.imdecode(np_data, 1)
     yield(frame)
     
     '''
     #trying this to see if I'm still getting the data
     if len(buffer) > 0:
          curr_packet = buffer.pop()
          mxid = curr_packet["mxid"]
          frame_data = curr_packet["frame"]
          dec_data = base64.b64decode(frame_data, ' /')
          np_data = np.fromstring(dec_data, dtype=np.uint8)
          frame = cv2.imdecode(np_data, 1)
          cv2.imshow(mxid, frame)
          if cv2.waitKey(1) == ord('q'):
               break
     '''

def main():
    s = StreamingServer()
    s.start()

if __name__ == "__main__":
    main()