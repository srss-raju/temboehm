# -*- coding: utf-8 -*-

from flask import Flask
from flask_socketio import SocketIO, send, emit
import json
import requests

import im_postgres_lib


with open("config.json") as f:
    conn_params = json.load(f)

db = im_postgres_lib.im_postgres(conn_params['conn'])
if not db.isConnected():
    print "Unable to connect to Postgres database. Exiting"
    exit(1)

app = Flask(__name__)
socketio = SocketIO(app)

    
#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('connect')
def connect():
    print "SERVER:: Connection request received"
    # emit('my response', {'data': 'Client Connected'})

    metadata = db.Get_RowFirst('ims_master_meta')
    data = db.Get_RowsAll('ims_master')
    obj = make_obj(metadata, data, 0)

    emit('message', obj)
    print "SERVER:: Sent message:\n", obj

    # return True


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('disconnect')
def disconnect():
    print 'SERVER:: Client Disconnected'


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('message')
def handle_sending_data_event(msg):
    print 'SERVER:: Received message: \n', str(msg)
    # emit('my response', {'data': "%d words"%(len(msg.split()))}, broadcast=True)

    obj = None

    if msg['id']:
        msg_id = msg['id']

        tbl_name = 'ims_master'
        for i in str(msg_id):
            tbl_name = db.Get_Child(tbl_name, i)

        if tbl_name:
            metadata = db.Get_RowFirst('%s_meta'%tbl_name)
            data = db.Get_RowsAll(tbl_name)
            obj = make_obj(metadata, data, msg_id)
            emit('message', obj)
        else:
            if msg['id'] == '4':
                obj_incident = {
                                'description' : msg['text'],
                                'priority'    : 1
                                }
                incident_num = incident_create(obj_incident)

                obj = {
                        'from'  : 'bot',
                        'type'  : 'text',
                        'text'  : "A ticket has been created for your issue. Ticket reference number is : {0}".format(incident_num)\
                                  if incident_num\
                                  else "Sorry. Couldn't create incident for your problem due to some issue with server"
                        }
                emit('message', obj)

            elif msg['id'] == '5':
                id_incident = msg['text']
                res = incident_status(id_incident)

                obj = {
                        'from'  : 'bot',
                        'type'  : 'text',
                        'text'  : "The state of your ticket ({id}) is: {state}".format(id=id_incident, state=res)\
                                    if res\
                                    else "Sorry. Couldn't get the state of your incident due to some issue with server"
                        }
                emit('message', obj)

    elif msg['text'] =='hi':
        obj = {
                'from'  : 'bot',
                'type'  : 'text',
                'text'  : "Hello",
                }
        emit('message', obj)
    else:
        obj = {
                'from'  : 'bot',
                'type'  : 'text',
                'text'  : "I'm sorry. I don't think I've understood your querry. Please write an email to chatbot@innominds.com for more help. Thank you",
                }
        emit('message', obj)

    print "SERVER:: Sent message:\n", obj


#-----------------------------------------------------------------------------------------------------------------------
def incident_create(obj_incident):
    url = 'https://dev18273.service-now.com/api/now/v1/table/incident'
    payload = {
                    'short_description' : obj_incident['description'],
                    'priority'          : obj_incident['priority'],
                    'urgency'           : '1',
                    'assignment_group'  : 'Hardware'
                }
    
    response = requests.post(
                             url,
                             data    = json.dumps(payload),
                             auth    = ("admin", "qegZBqHH8gO3"),
                             headers = {'Content-type': 'application/json'}
                             )

    try:
        incident_num = response.json()['result']['number'] or 0
    except Exception as e:
        print "ERROR: ", type(e), e
        incident_num = 0
        print response
    
    return incident_num


#-----------------------------------------------------------------------------------------------------------------------
def incident_status(id_incident):
    url = 'https://dev18273.service-now.com/api/now/v2/table/incident?sysparm_display_value=true&sysparm_fields=incident_state&sysparm_query=number={id_incident}'\
            .format(id_incident=id_incident)

    response = requests.get(url, auth=("admin","qegZBqHH8gO3"))
    try:
        result = response.json()['result']
        incident_state = result[0]['incident_state'] if result else 'Ticket number seems to be invalid. Could you please check and try again?'
    except Exception as e:
        print "ERROR: ", type(e), e
        incident_state = ''
        print response

    return incident_state


#-----------------------------------------------------------------------------------------------------------------------
def make_header(metadata):
    return {i:j for i,j in zip(('from', 'type', 'text'), metadata)}


#-----------------------------------------------------------------------------------------------------------------------
def make_options(data, msg_id):
    return {'options' : [{i:j for i,j in zip(('id', 'name'), (msg_id*10+row[0], row[1]))} for row in data]}


#-----------------------------------------------------------------------------------------------------------------------
def make_obj(metadata, data, msg_id):
    d = {}

    d.update(make_header(metadata))
    d.update(make_options(data, msg_id))

    return d

