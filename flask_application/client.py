'''
Script for client side
@author: hao
@author: Cornelius Monahan
'''
import protocol
import socket
import os
import numpy as np  # numpy - manipulate the packet data returned by depthai
import cv2  # opencv - display the video stream
#import depthai  # depthai - access the camera and its data packets
#import blobconverter  # blobconverter - compile and download MyriadX neural network blobs
import time
import numpy as np
import threading
import pickle, struct, base64

class Client:

    #Constructor: load client configuration from config file
    def __init__(self, server_IP, server_port, flask_IP, flask_port, ERROR_IMG):
        self.server_addr = (server_IP, server_port)
        self.flask_addr = (flask_IP, flask_port)
        self.BUFFER = 85536
        self.ERROR_IMG = ERROR_IMG["IMG"] #points to location of the image data created in memory
    
    def get_server_addr(self):
         return self.server_addr
    
    def get_flask_addr(self):
         return self.flask_addr
    
    def flask_port(self):
         return self.flask_addr[1] #takes port number from Flask address tuple
    
    def buffer_size(self):
         return self.BUFFER
    
    def get_error_img(self):
         return self.ERROR_IMG
    
    def get_recording(self, camera, s_id, e_id, date, s_time, e_time):
          server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.buffer_size())
          server.bind(self.get_flask_addr())

          #create package to be sent to streaming server for a specific camera
          data_struct = {"header": protocol.HEAD_REC, "data":{"port": self.flask_port(), 
                                                                  "mxid": camera,
                                                                  "id": s_id}}
          msg = pickle.dumps(data_struct)

          #send message to streaming server for specific camera
          sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
          sending_socket.sendto(msg, self.get_server_addr())

          #start unpacking frames and streaming video
          while True:
               rec_data, addr = server.recvfrom(self.buffer_size())
               packet = pickle.loads(rec_data)
               data = packet["data"]

               if data:
                    dec_data = base64.b64decode(packet["data"], ' /') #this is the frame data
               else:
                    dec_data = self.get_error_img()

               yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + dec_data + b'\r\n')

               if cv2.waitKey(1) == ord('q'):
                         break
    
    def get_camera(self, camera):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.buffer_size())
        server.bind(self.get_flask_addr())

        #create package to be sent to streaming server for a specific camera
        data_struct = {"header": protocol.HEAD_REQUEST, "data":{"port": self.flask_port(), "mxid": camera}}
        msg = pickle.dumps(data_struct)

        #send message to streaming server for specific camera
        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sending_socket.sendto(msg, self.get_server_addr())

        #start unpacking frames and streaming video
        while True:
            rec_data, addr = server.recvfrom(self.buffer_size())
            packet = pickle.loads(rec_data)
            data = packet["data"]
            Flag = packet["flag"]

            if data:
                 dec_data = base64.b64decode(packet["data"], ' /') #this is the frame data
                 yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + dec_data + b'\r\n')
            elif Flag:
                 dec_data = self.get_error_img()
                 yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + dec_data + b'\r\n')

            if cv2.waitKey(1) == ord('q'):
                    break