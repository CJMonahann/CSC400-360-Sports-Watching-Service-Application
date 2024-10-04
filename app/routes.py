from flask import Flask, render_template, redirect, url_for, request, jsonify, Response
from app import app
import numpy as np  # numpy - manipulate the packet data returned by depthai
import cv2  # opencv - display the video stream
#import depthai  # depthai - access the camera and its data packets
#import blobconverter  # blobconverter - compile and download MyriadX neural network blobs
import time
import client
import pickle

@app.route('/')
def index():
    return render_template('index.html')

times_selected = 0
@app.route('/video/CAM-<string:MXID>')
def video(MXID):
    socket = client.Client()
    return Response(socket.get_camera(MXID), mimetype='multipart/x-mixed-replace; boundary=frame')