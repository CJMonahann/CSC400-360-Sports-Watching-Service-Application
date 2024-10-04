'''
Script for server
@author: hao
@author: Cornelius Monahan
'''

import config
import protocol
import os
from socket import *
import numpy as np  # numpy - manipulate the packet data returned by depthai
import cv2  # opencv - display the video stream
import depthai  # depthai - access the camera and its data packets
import blobconverter  # blobconverter - compile and download MyriadX neural network blobs
import time
from sklearn.decomposition import PCA
import matplotlib.pyplot as plt
from PIL import Image
import pickle
import struct

class server:

    # Constructor: load the server information from config file
    def __init__(self):
        self.port, self.path=config.config().readServerConfig()

    def send_frames(self, serverSocket, CAM):
        MXID = CAM

        #define camera height and width
        width = 600
        height = 500

        #Define a pipeline
        pipeline = depthai.Pipeline()

        # We only need one node, which is the camera, the pipeline 
        # should be defined as camera -> host 
        cam_rgb = pipeline.create(depthai.node.ColorCamera)

        # Set the preview size
        cam_rgb.setPreviewSize(width, height)
        #cam_rgb.setPreviewKeepAspectRatio(True)
        #Create output
        xout_rgb = pipeline.create(depthai.node.XLinkOut)
        xout_rgb.setStreamName("rgb")
        cam_rgb.preview.link(xout_rgb.input)

        # This code only gets the frame from a single camera. 
        # Need to do: how to define a particular camera and get its stream
        #             how to setup ip addresses for the camera
        # 

        # Connect to multiple devices to get device information

        for device in depthai.Device.getAllAvailableDevices():
            print(f"{device.getMxId()} {device.state}")

        # Specify MXID, IP Address or USB path
        device_info = depthai.DeviceInfo(MXID) # MXID

        #pick a particular device

        with depthai.Device(pipeline,device_info) as device:
            CONST = 255
            HEADERSIZE = 10
            q_rgb = device.getOutputQueue("rgb")
            frame = None

            while True:
                in_rgb = q_rgb.tryGet()
                if in_rgb is not None:
                    frame = in_rgb.getCvFrame()
                if frame is not None:
                    a = pickle.dumps(frame)
                    message = struct.pack("Q", len(a)) + a
                    serverSocket.sendall(message) #send frame data
                    
                if cv2.waitKey(1) == ord('q'):
                    break


    # Main function of server, start the file sharing service
    def start(self):
        serverPort=self.port
        serverSocket=socket(AF_INET,SOCK_STREAM)
        serverSocket.bind(('',serverPort))
        serverSocket.listen(20)
        print('The server is ready to receive')
        while True:
            connectionSocket, addr = serverSocket.accept()
            dataRec = connectionSocket.recv(1024)
            header,msg=protocol.decodeMsg(dataRec.decode()) # get client's info, parse it to header and content
            # Main logic of the program, send different content to client according to client's requests
            if(header==protocol.HEAD_REQUEST):
                self.send_frames(connectionSocket, msg)
            else:
                connectionSocket.send(protocol.prepareMsg(protocol.HEAD_ERROR, "Invalid Message"))
            connectionSocket.close()

def main():
    s=server()
    s.start()

if __name__ == "__main__":
    main()