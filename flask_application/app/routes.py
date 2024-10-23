from flask import Flask, render_template, redirect, url_for, request, jsonify, Response, session
from app import app, db
from app.models import Accounts #imports like this will import the databse relations we have made in the 'models.py' page
from app.forms import signUpForm #makes forms functional in routes
import numpy as np  # numpy - manipulate the packet data returned by depthai
import cv2  # opencv - display the video stream
#import depthai  # depthai - access the camera and its data packets
#import blobconverter  # blobconverter - compile and download MyriadX neural network blobs
import time
import client
import pickle
import os
from dotenv import load_dotenv

@app.route('/')
@app.route('/home')
@app.route('/HOME')
def index():
    return render_template('index.html')

@app.route('/event-page')
def event_page():
    return render_template('event-page.html')

@app.route('/video/CAM-<string:MXID>')
def video(MXID):
    try:
        load_dotenv('.env')
        S_IP = os.getenv('STREAM_SERVER_IP')
        S_Port = int(os.getenv('STREAM_SERVER_PORT'))
        F_IP = os.getenv('FLASK_IP')
        F_Port = int(os.getenv('FLASK_PORT'))
        socket = client.Client(S_IP, S_Port, F_IP, F_Port)
        return Response(socket.get_camera(MXID), mimetype='multipart/x-mixed-replace; boundary=frame')
    except:
        new_url = f'/video/CAM-<string:{MXID}>'
        return redirect(new_url)