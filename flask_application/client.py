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
import pickle, struct

class Client:

    #Constructor: load client configuration from config file
    def __init__(self):
        self.serverName, self.serverPort, self.clientPort = config.config().readClientConfig()
        self.conn = True
        self.count = 0


    # Build connection to server
    def connect(self):
        serverName = self.serverName
        serverPort = self.serverPort
        clientSocket = socket(AF_INET, SOCK_STREAM)
        clientSocket.connect((serverName,serverPort))
        return clientSocket
    
    def get_camera(self, camera):
        mySocket=self.connect()
        mySocket.send(protocol.prepareMsg(protocol.HEAD_REQUEST,camera))

        data = b""
        payload_size = struct.calcsize("Q")

        while True:
            
            while len(data) < payload_size:
                packet = mySocket.recv(4*1024) #4k
                if not packet: break
                data += packet
            packed_msg_size = data[:payload_size]
            data = data[payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]

            while len(data) < msg_size:
                data += mySocket.recv(4*1024) #4k
            frame_data = data[:msg_size]
            data = data[msg_size:]
            frame = pickle.loads(frame_data)
            ret, new_frame = cv2.imencode('.jpg',frame)
            final_frame = new_frame.tobytes()
            yield(b'--frame\r\n'b'Content-Type: image/jpeg\r\n\r\n' + final_frame + b'\r\n')

            #send new message saying to continue
            mySocket.send(protocol.prepareMsg(protocol.HEAD_CONN,''))

            if cv2.waitKey(1) == ord('q'):
                    break
        
        mySocket.send(protocol.prepareMsg(protocol.HEAD_DISCONNECT,''))