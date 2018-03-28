# -*- coding: utf-8 -*-
from flask import Flask
from flask_socketio import SocketIO, send, emit

import json
import requests


app = Flask(__name__)
socketio = SocketIO(app)


@socketio.on('connect')
def connect():
    print "SERVER: Connection req received"
    # emit('my response', {'data': 'Client Connected'})

    initialObj = {
                'type'      : 'option',
                'text'      : "Hi, I'm Elisa. I can help you on the below topics. Please click on one of them basded on what you need",
                'from'      : 'bot',
                'options'   : [
                                {
                                    'id'  : 1,
                                    'name': 'Incident Creation'
                                },
                                {
                                    'id'  : 2,
                                    'name': 'Incident Enquiry'
                                },
                                {
                                    'id'  : 3,
                                    'name': 'Information'
                                }
                              ]
                }
    emit('message', initialObj)
    # return True

@socketio.on('disconnect')
def disconnect():
    print 'SERVER: Client Disconnected'

@socketio.on('message')
def handle_sending_data_event(msg):
    print 'SERVER: Received message: {0}'.format(str(msg))
    # emit('my response', {'data': "%d words"%(len(msg.split()))}, broadcast=True)

    if 'id' in msg and 'text' in msg:
        if msg['id'] == 1:
            obj = {
                    'from'  : 'bot',
                    'type'  : 'text',
                    'text'  : "Can you please briefly describe the problem you are facing?",
                    }
            emit('message', obj)

        elif msg['id'] == 2:
            obj = {
                    'from'  : 'bot',
                    'type'  : 'text',
                    'text'  : "Can you please share the ticket reference number?",
                    }
            emit('message', obj)

        elif msg['id'] == 3:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'options',
                    'text'      : "On which of the following topics would you like to know more information about?",
                    'options'   :[
                                    {
                                    'id'    : 31,
                                    'name'  : 'Access Issues'
                                    },
                                    {
                                    'id'    : 32,
                                    'name'  : 'Software Concerns'
                                    },
                                    {
                                    'id'    : 33,
                                    'name'  : 'Hardware Problems'
                                    },
                                    {
                                    'id'    : 34,
                                    'name'  : 'Network Challenges'
                                    },
                                    {
                                    'id'    : 35,
                                    'name'  : 'Server Connections'
                                    }
                                ]
                    }
            emit('message', obj)

        elif msg['id'] == '4':
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

    elif msg =='hi':
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
                'text'  : "Invalid message",
                }
        emit('message', obj)

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
    except:
        incident_num = 0
        print "SERVER: ", response.json()
    
    return incident_num

def incident_status(id_incident):
    url = 'https://dev18273.service-now.com/api/now/v2/table/incident?sysparm_display_value=true&sysparm_fields=incident_state&sysparm_query=number={id_incident}'\
            .format(id_incident=id_incident)

    response = requests.get(url, auth=("admin","qegZBqHH8gO3"))
    try:
        result = response.json()['result'][0]
        incident_state = result['incident_state'] if result else 'Ticket number seems to be invalid. Could you please check and try again?'
    except:
        incident_state = ''
        print "SERVER: ", response.json()


    return incident_state


