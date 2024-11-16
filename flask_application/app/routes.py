from flask import Flask, render_template, redirect, url_for, request, jsonify, Response, session
from app import app, db
from app.models import User, Event, Camera, Site, Organization #imports like this will import the databse relations we have made in the 'models.py' page
from app.forms import signUpForm, loginForm, eventOrganizerForm, eventsEOForm, SiteManagerSettingsForm, eventsSMForm, CameraForm, SiteForm, OrgForm, UpdateSiteForm, UpdateEventForm #makes forms functional in routes
import numpy as np  # numpy - manipulate the packet data returned by depthai
import cv2  # opencv - display the video stream
#import depthai  # depthai - access the camera and its data packets
#import blobconverter  # blobconverter - compile and download MyriadX neural network blobs
import time
import client
import pickle
import base64
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

@app.route('/events_eo/event-page-<int:id>')
@app.route('/events_sm/event-page-<int:id>')
@app.route('/events/event-page-<int:id>')
@app.route('/event-page-<int:id>')
def event_page(id):
    id = int(id)
    event = Event.query.get(id) #gets the event data needed
    site_id = event.s_id
    #get any related cameras of the particular site for which the event is configured
    cameras = Camera.query.filter_by(s_id=site_id).all()
    return render_template('event-page.html', event=event, cameras=cameras, id=id)

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
            session['is_eo'] = new_user.is_eo
            session['is_sm'] = new_user.is_sm
            print("Session username set to:", input_username)  # Debug statement

            # Redirect based on user role
            return redirect(url_for('organizations'))

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
    
@app.route('/recording/CAM-<string:MXID>')
def recording(MXID):
    str = MXID.split('&')
    MXID = str[0]
    event_id = int(str[1])
    event = Event.query.get(event_id) #gets the event data needed
    site_id = event.site
    try:
        load_dotenv('.env')
        S_IP = os.getenv('STREAM_SERVER_IP')
        S_Port = int(os.getenv('STREAM_SERVER_PORT'))
        F_IP = os.getenv('FLASK_IP')
        F_Port = port_obj.get_port()  # Dynamically assign new internal-port number
        port_obj.inc_port()  # Increment to avoid duplicate ports
        socket = client.Client(S_IP, S_Port, F_IP, F_Port, ERROR_IMG)
        return Response(socket.get_recording(MXID, site_id), mimetype='multipart/x-mixed-replace; boundary=frame')
    except:
        new_url = f'/video/CAM-<string:{MXID}>'
        return redirect(new_url)

@app.route('/past/games/<int:id>')
def past_game_page(id):
    id = int(id) #represents event ID
    event = Event.query.get(id) #gets the event data needed
    site_id = event.s_id
    #get any related cameras of the particular site for which the event is configured
    cameras = Camera.query.filter_by(s_id=site_id).all()
    return render_template('past_game_page.html', event=event, cameras=cameras)
    

@app.route('/event_organizer/<int:id>', methods=['GET', 'POST'])
def event_organizer(id):
    form = eventOrganizerForm()
    if form.validate_on_submit():
        print("EVENT CREATED!!!")
        new_event = Event(event_name=form.event_name.data, sport=form.sport.data, date=form.date.data,s_time=form.s_time.data, e_time=form.e_time.data, notes=form.notes.data, s_id=id, e_id=form.e_id.data)
        db.session.add(new_event)
        db.session.commit()
        return redirect(url_for('route_events', id=id))
    return render_template('event_organizer.html', form=form, id=id)

@app.route('/events/<int:id>')
def events(id):
    id = int(id)
    events = Event.query.filter_by(s_id=id).all()
    return render_template('events.html', events=events)

@app.route('/events_eo/<int:id>', methods=['GET', 'POST'])
def events_eo(id):
    id = int(id)
    events = Event.query.filter_by(s_id=id).all()

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
            return redirect(url_for('events_eo', id=id))
        
        elif action == 'modify_event':
            # Handle event modification
            event = Event.query.get(event_id)  # Get the event by ID
            if event:
                # Update the event details
                event.event_name = request.form.get('event_name')
                event.sport = request.form.get('sport')
                event.date = request.form.get('date')
                event.s_time = request.form.get('s_time')
                event.e_time = request.form.get('e_time')
                event.notes = request.form.get('notes')
                
                db.session.commit()  # Save changes to the database
                print("Event modified")
            else:
                print("Event not found")  # Optional: handle case where event is not found
            
            return redirect(url_for('events_eo', id=id))

    return render_template('events_eo.html', events=events, id=id)  # Pass events to the template

@app.route('/get/events/<int:id>')
def route_events(id):
    id = int(id) #represenrs a site ID
    if session['is_eo']:
        return redirect(url_for('events_eo', id=id))
    elif session['is_sm']:
        return redirect(url_for('events_sm', id=id))
    else:
        return redirect(url_for('events', id=id))

@app.route('/events_sm/<int:id>', methods=['GET', 'POST'])
def events_sm(id):
    id = int(id)
    events = Event.query.filter_by(s_id=id).all()

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
            return redirect(url_for('events_sm', id=id))
        
        elif action == 'modify_event':
            # Handle event modification
            event = Event.query.get(event_id)  # Get the event by ID
            if event:
                # Update the event details
                event.event_name = request.form.get('event_name')
                event.sport = request.form.get('sport')
                event.date = request.form.get('date')
                event.s_time = request.form.get('s_time')
                event.e_time = request.form.get('e_time')
                event.notes = request.form.get('notes')
                
                db.session.commit()  # Save changes to the database
                print("Event modified")
            else:
                print("Event not found")  # Optional: handle case where event is not found
            
            return redirect(url_for('events_sm', id=id))
    
    return render_template('site_manager.html', events=events, id=id)  # Pass events to the template

@app.route('/organizations')
def organizations():
    orgs = Organization.query.all()  # Fetch all organizations
    if session['is_sm']:
        return render_template('orgs_admin.html', orgs=orgs)  # Pass sites to the template
    else:
        return render_template('orgs_general.html', orgs=orgs)  # Pass sites to the template
    
@app.route('/create/org', methods=['GET', 'POST'])
def create_org():
    form = OrgForm()
    if form.validate_on_submit():
        new_site = Organization(name=form.name.data, street=form.street.data, city=form.city.data, state=form.state.data, about=form.about.data)
        db.session.add(new_site)
        db.session.commit()
        print("organization data was saved!")
        return redirect(url_for('organizations'))
    
    return render_template('create_org.html', form=form)

@app.route('/sites/<int:id>')
def sites(id):
    id = int(id) #organization id
    #get any related cameras via the forein key within the Camera table
    sites = Site.query.filter_by(org_id=id).all()
    org = Organization.query.get(id)
    org_name = org.name
    if session['is_sm']: 
        return render_template('sites_admin.html', sites=sites, id=id, name=org_name)  # Pass sites to the template
    else:
        return render_template('sites_general.html', sites=sites, name=org_name)  # Pass sites to the template

@app.route('/create/site/<int:id>', methods=['GET', 'POST'])
def create_site(id):
    id = int(id) #this represents the organization id, which will be a foreign key in the org
    form = SiteForm()
    org = Organization.query.get(id)
    org_name = org.name
    if form.validate_on_submit():
        new_site = Site(org_id = id, name=form.name.data, about=form.about.data, s_id=form.s_id.data)
        db.session.add(new_site)
        db.session.commit()
        print("site data was saved!")
        return redirect(url_for('sites', id=id))
    
    return render_template('create_site.html', form=form, name=org_name)

@app.route('/config-cams/<int:id>', methods=['GET', 'POST'])
def config_cams(id):
    id = int(id) #represents the Site ID
    form = CameraForm()
    if form.validate_on_submit():
        site = Site.query.get(id)
        org_id = site.org_id #get the Organization ID to redirect to appropriate sites page after update
        print("FORM VALIDATED!!")
        new_camera = Camera(s_id=id, mxid=form.mxid.data)
        db.session.add(new_camera)
        db.session.commit()
        print("data was saved!")
        return redirect(url_for('sites', id=org_id))
    
    return render_template('config_cams.html', form=form, id=id)

@app.route('/config-site-ID/<int:id>', methods=['GET', 'POST'])
def config_site_ID(id):
    id = int(id) #represents the site, id
    form = UpdateSiteForm()
    if form.validate_on_submit():
        site_id = form.s_id.data
        site = Site.query.get(id)
        site.s_id = site_id
        db.session.commit()
        org_id = site.org_id #get the Organization ID to redirect to appropriate sites page after update
        return redirect(url_for('sites', id=org_id))
    
    return render_template('config_site_ID.html', form=form, id=id)

@app.route('/set/event//<int:id>', methods=['GET', 'POST'])
def event_ID(id):
    id = int(id) #represents the event id
    form = UpdateEventForm()
    if form.validate_on_submit():
        event_id = form.e_id.data
        event = Event.query.get(id)
        event.e_id = event_id
        db.session.commit()
        #now, we get the site the event pertains to in order to route back to appropriate event page
        s_id = event.s_id #this is the side ID used within the event as a foreign key
        print(f"EVENT ID Updated! - {event_id}")
        return redirect(url_for('route_events', id=s_id))
    
    return render_template('config_event_ID.html', form=form, id=id)

@app.route('/return/home')
def return_home():
    return redirect(url_for('index'))

'''
def return_home():
    if session['is_eo']:
        return redirect(url_for('events_eo'))
    elif session['is_sm']:
        return redirect(url_for('events_sm'))
    else:
        return redirect(url_for('events'))
'''