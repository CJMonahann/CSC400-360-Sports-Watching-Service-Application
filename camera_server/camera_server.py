import cv2  # opencv - display the video stream
import depthai  # depthai - access the camera and its data packets
import threading
import time
import contextlib
import socket
import imutils
import base64
import pickle
import protocol

class Timer:
    def __init__(self, duration = 30):
        self.duration = duration
        self.stop = False
        self.count = 0
        self.started = False
    
    def get_count(self):
        return self.count
    
    def inc_count(self):
        self.count += 1

    def count_started(self):
        return self.get_count() >= 1

    def get_duration(self):
        return self.duration
    
    def end(self):
        return self.stop
    
    def exit(self):
        self.stop = True
    
    def start(self):
        self.started = True

    def has_started(self):
        return self.started

def handle_timer(timer):
    timer.start()
    time.sleep(timer.get_duration())
    print("TIMER DONE!")
    timer.exit()

def getPipeline():
    pipeline = depthai.Pipeline()

    # We only need one node, which is the camera, the pipeline 
    # should be defined as camera -> host 
    cam_rgb = pipeline.create(depthai.node.ColorCamera)

    cam_rgb.setPreviewKeepAspectRatio(True)
    xout_rgb = pipeline.create(depthai.node.XLinkOut)
    xout_rgb.setStreamName("video")
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
        'cam': device.getOutputQueue(name="video"),
    }

def stream_motion_video(q_rgb, mxid, server_IP, server_port, timer_obj):
        sending_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        IP = server_IP
        Port = server_port
        address = (IP, Port)
        THRESHOLD = 25.0

        #this will be the frame we use for the optical flow - grayscale to detect motion
        gray_frame = q_rgb['cam'].get().getCvFrame()
        gray_frame = cv2.cvtColor(gray_frame, cv2.COLOR_RGB2GRAY)

        #we will now detect motion and only send a frame if motion is detected
        x = 0
        while True:
            frame = q_rgb['cam'].get().getCvFrame() #collect a frame from feed
            packet = pack_frame(mxid, frame) #this will be the frame we send via UDP
           
            if frame is not None:
                curr_gray = cv2.cvtColor(frame, cv2.COLOR_RGB2GRAY) #current grayscale image for comparison
            
                #calculate optical flow to detect motion
                flow = cv2.calcOpticalFlowFarneback(gray_frame, curr_gray, None, 0.5, 3, 15, 3, 5, 1.2, 0)

                #calculate magnitude and compare it to threshold to determine if motion was detected
                magnitude, angle = cv2.cartToPolar(flow[..., 0], flow[..., 1])
                detected_motion_mask = magnitude > THRESHOLD

                
                if detected_motion_mask.any() and not(timer_obj.count_started()): #if motion is detected
                    #start timer. This will denote how long we send video
                    print(F"CAMERA - {mxid} - DETECTED MOTION")
                    print('TIMER STARTED!!')
                    timer_obj.inc_count()
                    timer_thread = threading.Thread(target=handle_timer, args=[timer_obj])
                    timer_thread.start()

                if timer_obj.has_started() and not(timer_obj.end()):
                    x += 1
                    print(f"{mxid} - Frame {x} - Sent")
                    sending_socket.sendto(packet, address)
                
                gray_frame = curr_gray

            if cv2.waitKey(1) == ord('q'):
                break

def pack_frame(mxid,frame):
    res_frame = imutils.resize(frame, width=400)
    _, new_frame = cv2.imencode('.jpg', res_frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
    byte_packet = base64.b64encode(new_frame)
    header = protocol.HEAD_CS
    data_struct = {"header":header, 
                   "data":
                   {
                   "mxid":mxid, 
                   "frame":byte_packet
                   }
                   }
    packet = pickle.dumps(data_struct)
    
    return packet

def start_cameras(server_IP, server_port, timer_obj):
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

        
        # Create multiple threads to deal with frames from different camera

        cam_threads = []

        for mxid, q in devices.items():
            thread = threading.Thread(target=stream_motion_video,args=[q,mxid,server_IP, server_port, timer_obj])
            thread.start()
            cam_threads.append(thread)
        
        for t in cam_threads:
            t.join()
        
def main():
    t = Timer() #default of 30 seconds for camera record time when no argument is passed
    start_cameras('192.168.1.132', 1200, t)

if __name__ == "__main__":
    main()