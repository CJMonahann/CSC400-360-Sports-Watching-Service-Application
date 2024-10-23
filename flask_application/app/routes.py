from flask import Flask, render_template, redirect, url_for, request, jsonify, Response, session
from app import app, db
from app.models import User #imports like this will import the databse relations we have made in the 'models.py' page
from app.forms import signUpForm, loginForm #makes forms functional in routes
import numpy as np  # numpy - manipulate the packet data returned by depthai
import cv2  # opencv - display the video stream
#import depthai  # depthai - access the camera and its data packets
#import blobconverter  # blobconverter - compile and download MyriadX neural network blobs
import time
import client
import pickle
import os
from dotenv import load_dotenv

#global variables

@app.route('/')
@app.route('/home')
@app.route('/HOME')
def index():
    return render_template('index.html')

@app.route('/event-page')
def event_page():
    return render_template('event-page.html')

@app.route('/signup', methods=['GET', 'POST'])
def sign_up():
    form = signUpForm()
    if form.validate_on_submit():
        password = form.password.data
        new_user = User(username=form.username.data,  email=form.email.data, password=password)
        db.session.add(new_user)
        db.session.commit()
        print("redirected to login")
        return redirect (url_for('login'))
    print("render sign-up.html")
    return render_template('signup.html', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit():
        input_username = form.username.data
        input_password = form.password.data
        print("Submitted username:", input_username)  # Debug statement
        print("Submitted password:", input_password)  # Debug statement
        new_user = User.query.filter_by(username=input_username).first()
        if new_user is None:
            print("User not found, please try again.")  # Debug statement
        elif new_user.password != input_password:  # Assuming password is stored as plaintext
            print("Password incorrect, please try again.")  # Debug statement
        else:
            print("You have been logged in.")  # Debug statement
            session['username'] = input_username
            print("Session user_name set to:", input_username)  # Debug statement
            print("Redirecting to landing page...")  # Debug statement
            return redirect (url_for('event_page'))
    else:
        print("Form validation failed.")  # Debug statement
        print("Form errors:", form.errors)  # Debug statement
    return render_template('login.html', form=form)


@app.route('/video/CAM-<string:MXID>')
def video(MXID):
    try:
        load_dotenv('.env')
        S_IP = os.getenv('STREAM_SERVER_IP')
        S_Port = int(os.getenv('STREAM_SERVER_PORT'))
        F_IP = os.getenv('FLASK_IP')
        F_Port = int(os.getenv('FLASK_PORT'))
        socket = client.Client(S_IP, S_Port, F_IP, F_Port)
        print(F_Port, type(F_Port))
        return Response(socket.get_camera(MXID), mimetype='multipart/x-mixed-replace; boundary=frame')

    except:
        new_url = f'/video/CAM-<string:{MXID}>'
        return redirect(new_url)