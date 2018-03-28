# -*- coding: utf-8 -*-

from flask import Flask
from flask_socketio import SocketIO, send, emit

import json
import requests


app = Flask(__name__)
socketio = SocketIO(app)


#-----------------------------------------------------------------------------------------------------------------------
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


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('disconnect')
def disconnect():
    print 'SERVER: Client Disconnected'


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('message')
def handle_sending_data_event(msg):
    print 'SERVER: Received message: {0}'.format(str(msg))
    # emit('my response', {'data': "%d words"%(len(msg.split()))}, broadcast=True)

    # if 'id' in msg and 'text' in msg:
    if msg['id']:
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
                    'text'      : "On which of the following topics do you need information?",
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


        ##
        elif msg['id'] == 31:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'option',
                    'text'      : 'Pick a category',
                    'options'   : [
                                    {'id': 311, 'name': 'New Registration'},
                                    {'id': 312, 'name': 'Existing User'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 32:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'option',
                    'text'      : 'Pick a category',
                    'options'   : [
                                    {'id': 321, 'name': 'License related'},
                                    {'id': 322, 'name': 'Malfunction related'},
                                    {'id': 323, 'name': 'Virus Threats & Phishing'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 33:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'option',
                    'text'      : 'Pick a category',
                    'options'   : [
                                    {'id': 331, 'name': 'Printer related'},
                                    {'id': 332, 'name': 'Display related'},
                                    {'id': 333, 'name': 'Keyboard related'},
                                    {'id': 334, 'name': 'Mouse related'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 34:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'option',
                    'text'      : 'Pick a category',
                    'options'   : [
                                    {'id': 341, 'name': 'Wireless network'},
                                    {'id': 342, 'name': 'Wired network'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 35:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'option',
                    'text'      : 'Pick a category',
                    'options'   : [
                                    {'id': 351, 'name': 'New Server'},
                                    {'id': 352, 'name': 'Existing Server'}
                                    ]
                    }
            emit('message', obj)


        ###
        elif msg['id'] == 311:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3111, 'name': 'What are the steps to be followed during a new user registration?'},
                                    {'id': 3112, 'name': 'I already followed the steps in the new registration, still I am unable to access'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 312:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3121, 'name': 'I forgot my username'},
                                    {'id': 3122, 'name': 'I forgot my password'},
                                    {'id': 3123, 'name': 'I remember username and password but I am unable to login'}
                                    ]
                    }
            emit('message', obj)

        elif msg['id'] == 321:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3211, 'name': 'My software license got expired. Can you renew it?'},
                                    {'id': 3212, 'name': 'I need a license for a software'},
                                    {'id': 3213, 'name': 'Can you revoke the license?'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 322:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3221, 'name': 'I lost my data. Can you recover it?'},
                                    {'id': 3222, 'name': 'My system is hanging'},
                                    {'id': 3223, 'name': 'Can you re-install a software?'},
                                    {'id': 3224, 'name': 'Can you provide/remove admin privileges?'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 323:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3231, 'name': 'I am suspecting a phishing incident'},
                                    {'id': 3232, 'name': 'My system seems to be attacked by a virus'}
                                    ]
                    }
            emit('message', obj)

        elif msg['id'] == 331:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3311, 'name': 'Find my nearest printer'},
                                    {'id': 3312, 'name': 'Unable to connect to a printer'},
                                    {'id': 3313, 'name': 'Printer is not working'},
                                    {'id': 3314, 'name': 'Refill the catridge'},
                                    {'id': 3315, 'name': 'Fill up the papers'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 332:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3321, 'name': 'Unable to see any display'},
                                    {'id': 3322, 'name': 'My screen is flickering'},
                                    {'id': 3323, 'name': 'Replace my monitor'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 333:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3331, 'name': 'Some keys are not detecting'},
                                    {'id': 3332, 'name': 'Keyboard is not working'},
                                    {'id': 3333, 'name': 'Replace my keyboard'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 334:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3341, 'name': 'Mouse sensitivity has to be changed'},
                                    {'id': 3342, 'name': 'Replace my mouse'}
                                    ]
                    }
            emit('message', obj)

        elif msg['id'] == 341:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3411, 'name': 'Unable to connect to Wireless network'},
                                    {'id': 3412, 'name': 'Wireless network is slow'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 342:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3421, 'name': 'Unable to connect to Wired network'},
                                    {'id': 3422, 'name': 'Provide with a new LAN wire'}
                                    ]
                    }
            emit('message', obj)

        elif msg['id'] == 351:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'option',
                    'text'      : 'Pick a category',
                    'options'   : [
                                    {'id': 3511, 'name': 'In-house'},
                                    {'id': 3512, 'name': 'Over cloud'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 352:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 3521, 'name': 'Unable to access the server'},
                                    {'id': 3522, 'name': 'Add a new login to the existing server'},
                                    {'id': 3523, 'name': 'Upgrade/Downgrade the configuration'}
                                    ]
                    }
            emit('message', obj)



        ###
        elif msg['id'] == 3511:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 35111, 'name': 'Configuration requirements'},
                                    {'id': 35112, 'name': 'Possible locations'}
                                    ]
                    }
            emit('message', obj)
        elif msg['id'] == 3512:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'questions',
                    'text'      : 'Click on appropriate link for further information - ',
                    'options'   : [
                                    {'id': 35111, 'name': 'AWS'},
                                    {'id': 35112, 'name': 'Digital Ocean'},
                                    {'id': 35113, 'name': 'Vultr'}
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
    except:
        incident_num = 0
        print "SERVER: ", response.json()
    
    return incident_num


#-----------------------------------------------------------------------------------------------------------------------
def incident_status(id_incident):
    url = 'https://dev18273.service-now.com/api/now/v2/table/incident?sysparm_display_value=true&sysparm_fields=incident_state&sysparm_query=number={id_incident}'\
            .format(id_incident=id_incident)

    response = requests.get(url, auth=("admin","qegZBqHH8gO3"))
    try:
        result = response.json()['result']
        incident_state = result[0]['incident_state'] if result else 'Ticket number seems to be invalid. Could you please check and try again?'
    except:
        incident_state = ''
        print "SERVER: ", response.json()

    return incident_state


