# -*- coding: utf-8 -*-

from flask import Flask, request
from flask_socketio import SocketIO, send, emit
import json
import requests
import random

import im_postgres_lib
from im_corpus import corpus_options


with open("config.json") as f:
    conn_params = json.load(f)

db = im_postgres_lib.im_postgres(conn_params['conn'])
if not db.isConnected():
    print "Unable to connect to Postgres database. Exiting"
    exit(1)

app = Flask(__name__)
socketio = SocketIO(app)


class UserSession:
    def __init__(self, sid, username):
        self._sid          = sid
        self._username     = username
        self._chat_history = []
        self._active       = True

    def update_chat(self, msg):
        self._chat_history.append(msg)

    def get_username(self):
        return self._username

    def get_chat_history(self):
        return str(' ## '.join(self._chat_history))

    def isActive(self):
        return self._active

    def invalidate(self):
        self._active = False


Table_UserSessions = {}


#-----------------------------------------------------------------------------------------------------------------------
@app.route('/login', methods=['POST'])
def login():
    # print request.data

    if request.method == 'POST':
        # Get the form
        data = eval(request.get_data())

        # Extract the form data
        user_name = data.get('username')
        password  = data.get('password')

        data = db.Get_RowsMatching('ims_users', 'user_name', user_name)
        _password = data[1]

        if password == _password:
            otp = random.randint(1000, 9999)
            db.Update_Table('ims_users', 'otp', otp, "user_name='%s'"%user_name)
            print "SERVER:: User authentication SUCCESSFUL\n\n"

            return str(otp)

        else:
            print "SERVER:: User authentication FAILED\n\n"
            return ''


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('connect')
def connect():
    print "SERVER:: Connection request received"
    # emit('my response', {'data': 'Client Connected'})

    obj = {
            'from'      : "bot",
            'type'      : "mandatory-action",
            'text'      : "Please click this link to signin first",
            'ftr_id'    : 0,
            'options'   : [
                            {
                                'id'    : 0,
                                'name'  : 'signin'
                            }
                          ]
          }

    emit('message', obj)
    print "SERVER:: Sent message:\n", obj, "\n"

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

    if request.sid in Table_UserSessions and not Table_UserSessions[request.sid].isActive():
        obj = {
                'from'      : "bot",
                'type'      : "mandatory-action",
                'text'      : "Please click this link to signin first",
                'options'   : [
                                {
                                    'id'    : 0,
                                    'name'  : 'signin'
                                }
                              ]
              }

        emit('message', obj)
        print "SERVER:: Sent message:\n", obj, "\n"

    else:
        process_message(msg)


#-----------------------------------------------------------------------------------------------------------------------
def process_message(msg):
    if msg['id']:
        process_message_with_id(msg)
    else:
        process_message_freetext(msg)


#-----------------------------------------------------------------------------------------------------------------------
def process_message_with_id(msg):
    msg_id = msg['id']
    obj = None

    tbl_name = 'ims_master'
    for i in str(msg_id):
        tbl_name = db.Get_Child(tbl_name, i)
        if not tbl_name:
            break

    if tbl_name:
        metadata = db.Get_RowFirst('%s_meta'%tbl_name)
        data = db.Get_RowsAll(tbl_name)
        obj = make_obj(metadata, data, msg_id)
        emit('message', obj)
    else:
        if msg_id == '4':
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

        elif msg_id == '5':
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

        elif msg_id == '0':
            otp = msg['text']

            data = db.Get_RowsMatching('ims_users', 'otp', otp)
            if data:
                _username = data[0]

                print "SERVER:: User logged in\n\n"

                obj = {
                        'from'  : 'bot',
                        'type'  : 'text',
                        'text'  : "Welcome, {username}! You are now logged in".format(username=_username)
                        }
                emit('message', obj)

                metadata = db.Get_RowFirst('ims_master_meta')
                data = db.Get_RowsAll('ims_master')
                obj2 = make_obj(metadata, data, 0)

                emit('message', obj2)

                Table_UserSessions[request.sid] = UserSession(request.sid, _username)

            else:
                print "SERVER:: ERROR : User login FAILED\n\n"
                obj = {
                        'from'  : 'bot',
                        'type'  : 'text',
                        'text'  : "Oops! I'm sorry. The code you entered is incorrect."
                        }
                emit('message', obj)

        elif msg_id == '-1':
            if request.sid in Table_UserSessions:
                Table_UserSessions[request.sid].invalidate()

        elif msg_id == '9999':
            msg_text = msg['text']
            obj = {
                    'from'  : 'bot',
                    'type'  : 'text',
                    'text'  : ''
                    }

            if msg_text in ['Terrible', 'Bad']:
                obj['text'] = "Thanks for you feedback. We are really sorry that you had a bad experience with us. We will strive to improve your experience with us"
            if msg_text in ['Okay', 'Good']:
                obj['text'] = "Thanks for you feedback. We will improve ourself to serve you better"
            elif msg_text == 'Great':
                obj['text'] = "Thanks for you feedback. We are happy that we could give you a good experience"

            emit('message', obj)

            if request.sid in Table_UserSessions:
                chat_history = Table_UserSessions[request.sid].get_chat_history()
                user_name = Table_UserSessions[request.sid].get_username()
                db.InsertInto_Table('ims_user_chat', ('user_name', 'chat_text', 'chat_end_time', 'feedback'), (user_name, chat_history, 'now', str(msg_text)))

        else:
            obj = {
                    'from'  : 'bot',
                    'type'  : 'text',
                    'text'  : 'Please use this link to get information on this: https://innominds.com/%s'%('_'.join(msg['text'].split()))
                    }

            emit('message', obj)


    print "SERVER:: Sent message:\n", obj, "\n"


#-----------------------------------------------------------------------------------------------------------------------
def process_message_freetext(msg):
    msg_text = msg['text'].strip().lower()
    obj = None

    if request.sid in Table_UserSessions:
        Table_UserSessions[request.sid].update_chat(msg['text'])


    if msg_text in corpus_options['option_incident_create']:
        msg['id'] = 1
        process_message_with_id(msg)

    elif msg_text in corpus_options['option_incident_enquiry']:
        msg['id'] = 2
        process_message_with_id(msg)

    elif 'access' in msg_text:
        msg['id'] = 31
        process_message_with_id(msg)

    elif 'software' in msg_text:
        msg['id'] = 32
        process_message_with_id(msg)

    elif 'hardware' in msg_text:
        msg['id'] = 33
        process_message_with_id(msg)

    elif 'network' in msg_text:
        msg['id'] = 34
        process_message_with_id(msg)

    elif 'server' in msg_text:
        msg['id'] = 35
        process_message_with_id(msg)

    elif msg_text == 'hi':
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
                'text'  : "I'm sorry. I don't think I've understood your query. Please write an email to chatbot@innominds.com for more help. Thank you",
                }
        emit('message', obj)

    print "SERVER:: Sent message:\n", obj, "\n"


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

