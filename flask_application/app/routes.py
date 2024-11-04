from flask import Flask, render_template, redirect, url_for, request, jsonify, Response, session
from app import app, db
from app.models import User, Event #imports like this will import the databse relations we have made in the 'models.py' page
from app.forms import signUpForm, loginForm, eventOrganizerForm, eventsEOForm #makes forms functional in routes
import numpy as np  # numpy - manipulate the packet data returned by depthai
import cv2  # opencv - display the video stream
#import depthai  # depthai - access the camera and its data packets
#import blobconverter  # blobconverter - compile and download MyriadX neural network blobs
import time
import client
import pickle
import os
from dotenv import load_dotenv
import PortCounter

#global variables
port_obj = PortCounter.PortCounter(int(os.getenv('FLASK_PORT')))
img_path = os.path.join(app.root_path, 'static', 'images', 'server_messages', 'Camera_Error_Display.JPG')
ERROR_IMG = {"IMG": b''}

#create instance of the error image in memory to be displayed to users when a camera isn't available
#this can be referenced by various users in real time
if os.path.exists(img_path): #if the path is correct, create the image, and store in the dictionary
    with open(img_path, 'rb') as image:
        image_data = image.read()
    ERROR_IMG['IMG'] = image_data
else:
    print("ERROR Image path not found")
    

@app.route('/')
@app.route('/home')
@app.route('/HOME')
def index():
    return render_template('index.html')

@app.route('/event-page')
def event_page():
    return render_template('event-page.html')

@app.route('/sign_up', methods=['GET', 'POST'])
def sign_up():
    form = signUpForm()
    if form.validate_on_submit():
        password = form.password.data
        new_user = User(username=form.username.data,  email=form.email.data, password=password, is_eo = False, is_sm = False)
        db.session.add(new_user)
        db.session.commit()
        print("redirected to login")
        return redirect (url_for('login'))
    print("render sign-up.html")
    return render_template('signup.html', form=form)

@app.route('/events')
def events():
    events = Event.query.all()  # Fetch all events
    return render_template('events.html', events=events)

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = loginForm()
    if form.validate_on_submit():
        input_username = form.username.data
        input_password = form.password.data
        print("Submitted username:", input_username)  # Debug statement
        print("Submitted password:", input_password)  # Debug statement

        # Query the user from the database
        new_user = User.query.filter_by(username=input_username).first()
        if new_user is None:
            print("User not found, please try again.")  # Debug statement
        elif new_user.password != input_password:  # Assuming password is stored as plaintext
            print("Password incorrect, please try again.")  # Debug statement
        else:
            print("You have been logged in.")  # Debug statement
            session['username'] = input_username
            print("Session username set to:", input_username)  # Debug statement

            # Redirect based on user role
            if new_user.is_eo:
                print("Redirecting admin to index page...")  # Debug statement
                return redirect(url_for('events_eo'))
            elif new_user.is_sm:
                print("Redirecting admin to index page...")  # Debug statement
                return redirect(url_for('events_sm'))
            else:
                print("Redirecting to event page...")  # Debug statement
                return redirect(url_for('events'))
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
        F_Port = port_obj.get_port()  # Dynamically assign new internal-port number
        port_obj.inc_port()  # Increment to avoid duplicate ports
        socket = client.Client(S_IP, S_Port, F_IP, F_Port, ERROR_IMG)
        return Response(socket.get_camera(MXID), mimetype='multipart/x-mixed-replace; boundary=frame')
    except:
        new_url = f'/video/CAM-<string:{MXID}>'
        return redirect(new_url)
    

@app.route('/event_organizer', methods=['GET', 'POST'])
def event_organizer():
    form = eventOrganizerForm()
    if form.validate_on_submit():
        new_event = Event(event_name=form.event_name.data, sport=form.sport.data, date=form.date.data,time=form.time.data, notes=form.notes.data)
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('events_eo'))
    return render_template('event_organizer.html', form=form)

@app.route('/events_eo', methods=['GET', 'POST'])
def events_eo():
    events = Event.query.all()  # Fetch all events

    if request.method == 'POST':
        action = request.form.get('action')  # Get the action (modify, delete, stream)
        event_id = request.form.get('id')  # Get the event ID from the form

        if action == 'delete_event':
            # Handle event deletion
            event = Event.query.get(event_id)  # Use the retrieved event ID
            if event:
                db.session.delete(event)
                db.session.commit()
                print("Event deleted")
            else:
                print("Event not found")  # Optional: handle case where event is not found
            return redirect(url_for('events_eo'))
        
        elif action == 'modify_event':
            # Handle event modification
            event = Event.query.get(event_id)  # Get the event by ID
            if event:
                # Update the event details
                event.event_name = request.form.get('event_name')
                event.sport = request.form.get('sport')
                event.date = request.form.get('date')
                event.time = request.form.get('time')
                event.notes = request.form.get('notes')
                
                db.session.commit()  # Save changes to the database
                print("Event modified")
            else:
                print("Event not found")  # Optional: handle case where event is not found
            
            return redirect(url_for('events_eo'))

    return render_template('events_eo.html', events=events)  # Pass events to the template

@app.route('/events_sm')
def events_sm():
    events = Event.query.all()  # Fetch all events
    return render_template('events_sm.html', events=events)

@app.route('/site_manager')
def site_manager():
    return render_template('site_manager.html')
