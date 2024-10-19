'''
Script for client side
@author: hao
@author: Cornelius Monahan
'''
import protocol
import config
from socket import *
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
        self.BUFFER = 65536
    
    def get_server_addr(self):
         return (self.serverName, self.serverPort) #(IP, PORT)
    
    def get_camera(self, camera):
        #create socket connection. Client will act as server to recieve data
        server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, self.BUFFER)
        server.bind(self.address)

        #create package to be sent to streaming server for a specific camera
        data_struct = {"header": protocol.HEAD_REQUEST, "data":{"mxid": camera}}
        msg = pickle.dumps(data_struct)

        #send message to streaming server for specific camera
        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sending_socket.sendto(msg, self.get_server_addr())

        #start unpacking frames and streaming video
        while True:
            rec_data, addr = server.recvfrom(self.BUFFER)
            packet = pickle.loads(rec_data)
            dec_data = base64.b64decode(packet, ' /')
            np_data = np.fromstring(dec_data, dtype=np.uint8)
            frame = cv2.imdecode(np_data, 1)

            yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

            if cv2.waitKey(1) == ord('q'):
                    break