import cv2  # opencv - display the video stream
import depthai  # depthai - access the camera and its data packets
import threading
import time
import contextlib
import config
import protocol
import os
from socket import *
import numpy as np  # numpy - manipulate the packet data returned by depthai
import blobconverter  # blobconverter - compile and download MyriadX neural network blobs
from PIL import Image
import pickle
import struct

class server:

    # Constructor: load the server information from config file
    def __init__(self):
        self.port, self.path=config.config().readServerConfig()
    
    # Main function of server, start the file sharing service
    def start(self):
        devices = activate_cameras()
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

# To create a list of camera information
def getPipeline():
    pipeline = depthai.Pipeline()

    # We only need one node, which is the camera, the pipeline 
    # should be defined as camera -> host 
    cam_rgb = pipeline.create(depthai.node.ColorCamera)

    cam_rgb.setPreviewKeepAspectRatio(True)
    xout_rgb = pipeline.create(depthai.node.XLinkOut)
    xout_rgb.setStreamName("rgb")
    cam_rgb.preview.link(xout_rgb.input)

    return pipeline

def worker(device_info, stack, devices):
    openvino_version = depthai.OpenVINO.Version.VERSION_2021_4
    usb2_mode = False
    device = stack.enter_context(depthai.Device(openvino_version, device_info, usb2_mode))

    # Note: currently on POE, DeviceInfo.getMxId() and Device.getMxId() are different!
    print("=== Connected to " + device_info.getMxId())
    device.startPipeline(getPipeline())

    # Output queue will be used to get the rgb frames from the output defined above
    devices[device.getMxId()] = {
        'rgb': device.getOutputQueue(name="rgb"),
    }

def showVideo(q,mxid):
    while True:
        frame = q['rgb'].get().getCvFrame()
        cv2.imshow(f"{mxid}", frame) #does not work with multithreading
        if cv2.waitKey(1) == ord('q'):
            break

def send_frames(serverSocket, camera):

        while True:
            frame = camera['rgb'].get().getCvFrame()
            if frame is not None:
                a = pickle.dumps(frame)
                message = struct.pack("Q", len(a)) + a
                serverSocket.sendall(message) #send frame data
                
            if cv2.waitKey(1) == ord('q'):
                break

# https://docs.python.org/3/library/contextlib.html#contextlib.ExitStack
def activate_cameras():
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
        
        '''
        # Create multiple threads to deal with frames from different camera
        cam_threads = []
        
        for mxid, q in devices.items():
            thread = threading.Thread(target=showVideo,args=[q,mxid])
            thread.start()
            cam_threads.append(thread)
        
        
        for t in cam_threads:
            t.join()
        '''
        

def handle_thread(connectionSocket, addr, devices):
    # Main logic of the program, send different content to client according to client's requests
    dataRec = connectionSocket.recv(1024)
    header,msg=protocol.decodeMsg(dataRec.decode()) # get client's info, parse it to header and content
    print("Message 1 -", msg)
    CONNECTED = True
    while CONNECTED:

        if(header==protocol.HEAD_REQUEST):
            camera = devices[msg]
            send_frames(connectionSocket, camera)
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
    
