'''
Script for client side
@author: hao
@author: Cornelius Monahan
'''
import protocol
import config
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
    def __init__(self):
        self.serverName, self.serverPort, self.clientPort = config.config().readClientConfig()
        self.clientAddr = ("192.168.1.132", 12001)
        self.BUFFER = 65536
    
    def get_server_addr(self):
         return (self.serverName, self.serverPort) #(IP, PORT)
    
    def get_camera(self, camera):
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFFER)
        server.bind(self.clientAddr)

        #create package to be sent to streaming server for a specific camera
        data_struct = {"header": protocol.HEAD_REQUEST, "data":{"port": 12001, "mxid": camera}}
        msg = pickle.dumps(data_struct)

        #send message to streaming server for specific camera
        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sending_socket.sendto(msg, self.get_server_addr())

        #start unpacking frames and streaming video
        while True:
            rec_data, addr = server.recvfrom(self.BUFFER)
            packet = pickle.loads(rec_data)
            dec_data = base64.b64decode(packet["data"], ' /') #this is the frame data
            yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + dec_data + b'\r\n')

            if cv2.waitKey(1) == ord('q'):
                    break