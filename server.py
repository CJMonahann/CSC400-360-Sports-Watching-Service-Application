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
import threading
import contextlib

class server:

    # Constructor: load the server information from config file
    def __init__(self):
        self.port, self.path=config.config().readServerConfig()
    
    # Main function of server, start the file sharing service
    def start(self):
        devices = connect_all_devices()
        print(devices)
        serverPort=self.port
        serverSocket=socket(AF_INET,SOCK_STREAM)
        serverSocket.bind(('',serverPort))
        serverSocket.listen(20)
        print('The server is ready to receive')
        while True:
            connectionSocket, addr = serverSocket.accept()
            thread = threading.Thread(target=handle_thread, args=[connectionSocket, addr, devices])
            thread.start()

def worker(device_info, stack, devices):
    openvino_version = depthai.OpenVINO.Version.VERSION_2021_4
    usb2_mode = False
    device = stack.enter_context(depthai.Device(openvino_version, device_info, usb2_mode))

    # Note: currently on POE, DeviceInfo.getMxId() and Device.getMxId() are different!
    print("=== Connected to " + device_info.getMxId())
    device.startPipeline(create_pipeline())

    # Output queue will be used to get the rgb frames from the output defined above
    devices[device.getMxId()] = device
    
    '''
    {
        'rgb': device #device.getOutputQueue(name="rgb"),
    }
    '''

def connect_all_devices():
    with contextlib.ExitStack() as stack:
        device_infos = depthai.Device.getAllAvailableDevices()
        if len(device_infos) == 0:
            raise RuntimeError("No devices found!")
        else:
            print("Found", len(device_infos), "devices")
        devices = {}
        threads = []

        for device_info in device_infos:
            time.sleep(1) # Currently required due to XLink race issues
            thread = threading.Thread(target=worker, args=(device_info, stack, devices))
            thread.start()
            threads.append(thread)

        for t in threads:
            t.join() # Wait for all threads to finish (to connect to devices)
        
        return devices

def create_pipeline():
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

    return pipeline

def create_all_pipelines(pipeline):
    #dictionary to store the pipeline alongside a camera connection
    all_cameras = {}

    for device in depthai.Device.getAllAvailableDevices():
        MXID = device.getMxId()
        all_cameras[MXID] = depthai.DeviceInfo(MXID) # MXID
    
    return all_cameras


def send_frames(serverSocket, MXID, devices):
    print("made it to send frames FUNCTION!")
    device = devices[MXID]
    device.getOutputQueue(name="rgb")

    '''
    while True:
            if frame is not None:
                a = pickle.dumps(frame)
                message = struct.pack("Q", len(a)) + a
                serverSocket.sendall(message) #send frame data
                
            if cv2.waitKey(1) == ord('q'):
                break
    '''

    '''
    #pick a particular device
    device_info = all_cameras[MXID]

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
    '''

def handle_thread(connectionSocket, addr, devices):
    # Main logic of the program, send different content to client according to client's requests
    dataRec = connectionSocket.recv(1024)
    header,msg=protocol.decodeMsg(dataRec.decode()) # get client's info, parse it to header and content
    print("Message 1 -", msg)
    CONNECTED = True
    while CONNECTED:

        if(header==protocol.HEAD_REQUEST):
            send_frames(connectionSocket, msg, devices)
        elif(header==protocol.HEAD_DISCONNECT):
            CONNECTED = False
        elif(header==protocol.HEAD_CONN):
            continue
        else:
            connectionSocket.send(protocol.prepareMsg(protocol.HEAD_ERROR, "Invalid Message"))

    connectionSocket.close()      

def main():
    s=server()
    s.start()

if __name__ == "__main__":
    main()