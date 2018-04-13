# -*- coding: utf-8 -*-

from flask import Flask, request
from flask_socketio import SocketIO, send, emit
import sys
import json
import random
import importlib

import im_postgres_lib
import im_incident_manager
from im_corpus import corpus_options


# Read the config file
with open("config.json") as f:
    try:
        params = json.load(f)

        conn_params = params['conn']
        inc_mgr_id = params['incident_manager']
    except ValueError as e:
        print "The config file seems to be malformed. Please check"
        print "ValueError:", sys.exc_info()[1]
        exit(1)
    except KeyError as e:
        print "The config file doesn't contain one or more required field"
        print "KeyError:", sys.exc_info()[1]
        exit(1)


# Get Database adapter
db = im_postgres_lib.im_postgres(conn_params)
if not db.isConnected():
    print "Unable to connect to Postgres database. Exiting"
    exit(1)


# Get appropriate incident manager based on configuraion
inc_mgr_name = im_incident_manager.get_manager(inc_mgr_id)
if inc_mgr_name:
    inc_mgr = importlib.import_module('im_incident_manager.%s'%inc_mgr_name)
else:
    print "INVALID value '%s' for the field 'incident_manager'. Please check the config file"%inc_mgr_id
    exit(1)


# Start flask server
app = Flask(__name__)
socketio = SocketIO(app)


class UserSession:
    def __init__(self, sid, username, otp):
        self._sid                   = sid
        self._username              = username
        self._chat_history          = []
        self._active                = False
        self.otp                    = otp
        self.msg_waiting_for_login  = None
        self.context_id             = None

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

    def update_login_info(self, username, otp):
        self._username  = username
        self.otp        = otp
        self._active    = True


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

    Table_UserSessions[request.sid] = UserSession(request.sid, None, None)

    metadata = db.Get_RowFirst('ims_master_meta')
    data = db.Get_RowsAll('ims_master')
    obj2 = make_obj(metadata+(None,), data, 0)

    emit('message', obj2)
    print "SERVER:: Sent message:\n", obj2, "\n"

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
    Table_UserSessions[request.sid].context_id = msg_id
    obj = None
    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None

    tbl_name = 'ims_master'
    for i in str(msg_id):
        tbl_name = db.Get_Child(tbl_name, i)
        if not tbl_name:
            break

    if tbl_name:
        metadata = db.Get_RowFirst('%s_meta'%tbl_name)
        data = db.Get_RowsAll(tbl_name)
        obj = make_obj(metadata+(OTP,), data, msg_id)
        emit('message', obj)
    else:
        if msg_id == '4':
            if request.sid in Table_UserSessions\
                and Table_UserSessions[request.sid].isActive()\
                and msg.get('idToken'):
                    obj_incident = {
                                    'description' : msg['text'],
                                    'priority'    : 1
                                    }
                    incident_num = inc_mgr.incident_create(obj_incident)

                    obj = {
                            'from'      : 'bot',
                            'type'      : 'text',
                            'text'      : "A ticket has been created for your issue. Ticket reference number is : {0}".format(incident_num)\
                                          if incident_num\
                                          else "Sorry. Couldn't create incident for your problem due to some issue with server",
                            'idToken'   : OTP,
                            }
                    emit('message', obj)

            else:
                Table_UserSessions[request.sid].msg_waiting_for_login = msg

                obj = {
                        'from'      : "bot",
                        'type'      : "mandatory-action",
                        'text'      : "Please click this link to signin first",
                        'idToken'   : None,
                        'options'   : [
                                        {
                                            'id'    : 0,
                                            'name'  : 'signin'
                                        }
                                      ]
                      }

                emit('message', obj)


        elif msg_id == '5':
            if request.sid in Table_UserSessions\
                and Table_UserSessions[request.sid].isActive()\
                and msg.get('idToken'):
                    id_incident = msg['text']
                    res = inc_mgr.incident_status(id_incident)

                    obj = {
                            'from'      : 'bot',
                            'type'      : 'text',
                            'text'      : "The state of your ticket ({id}) is: {state}".format(id=id_incident, state=res)\
                                            if res\
                                            else "Sorry. Couldn't get the state of your incident due to some issue with server",
                            'idToken'   : OTP,
                            }
                    emit('message', obj)

            else:
                Table_UserSessions[request.sid].msg_waiting_for_login = msg

                obj = {
                        'from'      : "bot",
                        'type'      : "mandatory-action",
                        'text'      : "Please click this link to signin first",
                        'idToken'   : None,
                        'options'   : [
                                        {
                                            'id'    : 0,
                                            'name'  : 'signin'
                                        }
                                      ]
                      }

                emit('message', obj)


        elif msg_id == '0':
            otp = msg['text']

            data = db.Get_RowsMatching('ims_users', 'otp', otp)
            if data:
                _username = data[0]

                print "SERVER:: User logged in\n\n"

                obj = {
                        'from'      : 'bot',
                        'type'      : 'text',
                        'text'      : "Welcome, {username}! You are now logged in".format(username=_username),
                        'idToken'   : otp
                        }
                emit('message', obj)

                Table_UserSessions[request.sid].update_login_info(_username, otp)

                msg_waiting_for_login = Table_UserSessions[request.sid].msg_waiting_for_login
                if msg_waiting_for_login:
                    Table_UserSessions[request.sid].msg_waiting_for_login = None
                    msg_waiting_for_login['idToken'] = otp
                    process_message(msg_waiting_for_login)

            else:
                print "SERVER:: ERROR : User login FAILED\n\n"
                obj = {
                        'from'      : 'bot',
                        'type'      : 'text',
                        'text'      : "Oops! I'm sorry. The code you entered is incorrect.",
                        'idToken'   : None
                        }
                emit('message', obj)

        elif msg_id == '-1':
            if request.sid in Table_UserSessions:
                Table_UserSessions[request.sid].invalidate()

        elif msg_id == '9999':
            msg_text = msg['text']
            obj = {
                    'from'      : 'bot',
                    'type'      : 'text',
                    'text'      : '',
                    'idToken'   : OTP,
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
                    'from'      : 'bot',
                    'type'      : 'text',
                    'text'      : 'Please use this link to get information on this: https://innominds.com/%s'%('_'.join(msg['text'].split())),
                    'idToken'   : OTP,
                    }

            emit('message', obj)


    print "SERVER:: Sent message:\n", obj, "\n"


#-----------------------------------------------------------------------------------------------------------------------
def process_message_freetext(msg):
    msg_text = msg['text'].strip().lower()
    obj = None
    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None

    if request.sid in Table_UserSessions:
        Table_UserSessions[request.sid].update_chat(msg['text'])

    context_id = Table_UserSessions[request.sid].context_id
    Table_UserSessions[request.sid].context_id = None

    if context_id == 1:
        msg['id'] = '4'
        process_message_with_id(msg)

    elif context_id == 2:
        msg['id'] = '5'
        process_message_with_id(msg)

    elif msg_text in corpus_options['option_incident_create']:
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
                'from'      : 'bot',
                'type'      : 'text',
                'text'      : "Hello",
                'idToken'   : OTP
                }
        emit('message', obj)

    else:
        obj = {
                'from'      : 'bot',
                'type'      : 'text',
                'text'      : "I'm sorry. I don't think I've understood your query. Please write an email to chatbot@innominds.com for more help. Thank you",
                'idToken'   : OTP
                }
        emit('message', obj)

    print "SERVER:: Sent message:\n", obj, "\n"


#-----------------------------------------------------------------------------------------------------------------------
def make_header(metadata):
    return {i:j for i,j in zip(('from', 'type', 'text', 'idToken'), metadata)}


#-----------------------------------------------------------------------------------------------------------------------
def make_options(data, msg_id):
    return {'options' : [{i:j for i,j in zip(('id', 'name'), (msg_id*10+row[0], row[1]))} for row in data]}


#-----------------------------------------------------------------------------------------------------------------------
def make_obj(metadata, data, msg_id):
    d = {}

    d.update(make_header(metadata))
    d.update(make_options(data, msg_id))

    return d

