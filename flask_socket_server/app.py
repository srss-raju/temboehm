# -*- coding: utf-8 -*-

from flask import Flask, request, jsonify, session, app
from flask_socketio import SocketIO, send, emit
from flask_cors import CORS
from datetime import timedelta


import sys
import time
import json
import random
import importlib

import im_postgres_lib
import im_incident_manager

import im_corpus
import sentiment
import requests



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


# Start flask server with CrossOriginResourceSharing and Socket capability
app = Flask(__name__)
CORS(app)
params = {
    'ping_timeout': 100000,
    'ping_interval': 5
}
socketio = SocketIO(app, logger=True, engineio_logger=True, **params)


class UserSession:
    def __init__(self, sid, username, otp):
        self._sid                   = sid
        self._username              = username
        self._chat_history          = []
        self._active                = False
        self.otp                    = otp
        self.msg_waiting_for_login  = None
        self.context_id             = None
        self.incident_id_enquired   = ''
        self.intensity              = 0

    def update_chat(self, msg):
        self._chat_history.append(msg)

    def get_username(self):
        return self._username

    def get_chat_history(self):
        return self._chat_history

    def isActive(self):
        return self._active

    def invalidate(self):
        self._active = False
        self.otp = None

    def update_login_info(self, username, otp):
        self._username  = username
        self.otp        = otp
        self._active    = True


# SessionId -> UserSession object
Table_UserSessions = {}


#-----------------------------------------------------------------------------------------------------------------------
@app.route('/login', methods=['POST', 'OPTIONS'])
def login():
    if request.method == 'POST':
        # Get the application data
        data = eval(request.get_data())

        # Extract the data
        user_name = data.get('username')
        password  = data.get('password')

        # Get the stored password from database
        data = db.Get_RowsMatching('ims_users', 'user_name', user_name)
        _password = data[1]

        # verify the user provided password; and generate an OTP
        if password == _password:
            otp = random.randint(1000, 9999)
            db.Update_Table('ims_users', 'otp', otp, "user_name='%s'"%user_name)
            print "SERVER:: User authentication SUCCESSFUL\n\n"

            return str(otp)

        else:
            print "SERVER:: User authentication FAILED\n\n"
            return ''

    elif request.method == 'OPTIONS':
        return ''


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('connect')
def connect():
    print "SERVER:: Connection request received"

    Table_UserSessions[request.sid] = UserSession(request.sid, None, None)
    intensity = Table_UserSessions[request.sid].intensity

    metadata = db.Get_RowFirst('ims_master_meta') + (time.strftime("%I:%M %p"), None, intensity)
    data = db.Get_RowsAll('ims_master')
    obj = make_obj(metadata, data, 0)

    emit_n_print('message', obj)

    # return True


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('disconnect')
def disconnect():
    print 'SERVER:: Client Disconnected'


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('feedback')
def handle_feedback_event(msg):
    print 'SERVER:: Received message: \n', str(msg)

    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None
    intensity = Table_UserSessions[request.sid].intensity
    msg_text = msg['text']

    obj = {
            'from'      : 'bot',
            'type'      : 'text',
            'text'      : '',
            'timestamp' : time.strftime("%I:%M %p"),
            'idToken'   : OTP,
            'intensity' : intensity
            }

    if msg_text in ['Terrible', 'Bad']:
        obj['text'] = "Thanks for you feedback. We are really sorry that you had a bad experience with us. We will strive to improve your experience with us in the future"
    if msg_text in ['Okay', 'Good']:
        obj['text'] = "Thanks for you feedback. We will improve ourself to serve you better"
    elif msg_text == 'Great':
        obj['text'] = "Thanks for you feedback. We are happy that we could give you a great experience"

    emit_n_print('message', obj)

    # Upon feedback, store the chat history into database
    if request.sid in Table_UserSessions:
        chat_history = Table_UserSessions[request.sid].get_chat_history()
        chat_history = str(' ## '.join(chat_history))
        user_name = Table_UserSessions[request.sid].get_username()
        db.InsertInto_Table('ims_user_chat', ('user_name', 'chat_text', 'chat_end_time', 'feedback'), (user_name, chat_history, 'now', str(msg_text)))


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('otp')
def handle_otp_event(msg):
    print 'SERVER:: Received message: \n', str(msg)

    otp = msg['text']

    try:
        otp = int(otp)
    except:
        pass

    if type(otp) in [str, unicode]:
        process_message_freetext(msg)
        return

    intensity = Table_UserSessions[request.sid].intensity
    data = db.Get_RowsMatching('ims_users', 'otp', otp)
    if data:
        _username = data[0]

        print "SERVER:: User logged in\n\n"

        obj_login = {
                        'from'      : 'bot',
                        'type'      : 'text',
                        'text'      : "Welcome, {username}! You are now logged in".format(username=_username),
                        'timestamp' : time.strftime("%I:%M %p"),
                        'idToken'   : otp,
                        'intensity' : intensity
                        }
        emit_n_print('message', obj_login)

        Table_UserSessions[request.sid].update_login_info(_username, otp)

        # check for any pending message waiting for the user to login; if there is any, process it
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
                'timestamp' : time.strftime("%I:%M %p"),
                'idToken'   : None,
                'intensity' : intensity
                }
        emit_n_print('message', obj)


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('idle')
def handle_idle_event(msg):
    print 'SERVER:: Received message: \n', str(msg)

    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None
    intensity = Table_UserSessions[request.sid].intensity

    obj = {
            'from'      : 'bot',
            'type'      : 'prompt-action',
            'text'      : "Can I help you with anything else?",
            'timestamp' : time.strftime("%I:%M %p"),
            'idToken'   : OTP,
            'intensity' : intensity,
            'options': [
                          {
                              'id': 91,
                              'name': 'No'
                          },
                          {
                              'id': 92,
                              'name': 'Yes'
                          }
                        ]
            }

    emit_n_print('message', obj)


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('timeout')
def handle_timeout_event(msg):
    print 'SERVER:: Received message: \n', str(msg)

    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None
    intensity = Table_UserSessions[request.sid].intensity

    # Invalidate the session
    if request.sid in Table_UserSessions:
        Table_UserSessions[request.sid].invalidate()

    obj = {
            'from'      : 'bot',
            'type'      : 'text',
            'text'      : "Looks like you are away. Let's connect again once you are back. Thank you",
            'timestamp' : time.strftime("%I:%M %p"),
            'idToken'   : OTP,
            'intensity' : intensity
            }

    emit_n_print('message', obj)


#-----------------------------------------------------------------------------------------------------------------------
@socketio.on('message')
def handle_message_event(msg):
    print 'SERVER:: Received message: \n', str(msg)
    process_message(msg)


#-----------------------------------------------------------------------------------------------------------------------
def process_message(msg):
    if msg['id']:
        process_message_with_id(msg)
    else:
        process_message_freetext(msg)


#-----------------------------------------------------------------------------------------------------------------------
def process_message_with_id(msg):
    print('with Id.......')
    msg_id = msg['id']
    Table_UserSessions[request.sid].context_id = msg_id
    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None
    intensity = Table_UserSessions[request.sid].intensity

    try:
        _msg_id = int(msg_id)
    except:
        _msg_id = ''

    tbl_name = None
    if type(_msg_id) is int:
        tbl_name = 'ims_master'
        _msg_id = '' if msg_id == 0 else str(msg_id)
        for i in _msg_id:
            tbl_name = db.Get_Child(tbl_name, i)
            if not tbl_name:
                break

    if tbl_name:
        metadata = db.Get_RowFirst('%s_meta'%tbl_name) + (time.strftime("%I:%M %p"), OTP, intensity)
        data = db.Get_RowsAll(tbl_name)
        obj = make_obj(metadata, data, msg_id)
        emit_n_print('message', obj)
    else:
        if msg_id == 'on_create_incident':
            on_create_incident(msg)

        elif msg_id == 'on_enquire_incident':
            on_enquire_incident(msg)

        elif msg_id == 'on_update_incident':
            on_update_incident(msg)

        elif msg_id == 91:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'request-feedback',
                    'text'      : 'Thank you. Please provide feedback on your experience with us. Your feedback helps us serve you better',
                    'timestamp' : time.strftime("%I:%M %p"),
                    'idToken'   : OTP,
                    'intensity' : intensity
                    }
            emit_n_print('message', obj)

        elif msg_id == 92:
            msg['id'] = 0
            process_message_with_id(msg)


        elif msg_id == 93:
            msg['id'] = 0
            process_message_with_id(msg)

        elif msg_id == 94:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'text',
                    'text'      : "Please tell me what is the update",
                    'timestamp' : time.strftime("%I:%M %p"),
                    'idToken'   : OTP,
                    'intensity' : intensity
                    }
            emit_n_print('message', obj)

        else:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'text',
                    'text'      : 'Please use this link to get information on this: https://innominds.com/%s'%('_'.join(msg['text'].split())),
                    'timestamp' : time.strftime("%I:%M %p"),
                    'idToken'   : OTP,
                    'intensity' : intensity
                    }

            emit_n_print('message', obj)


#-----------------------------------------------------------------------------------------------------------------------
def process_message_freetext(msg):
    print('noooooooooo ddddddddddddddddddddddddddd')
    msg_text = msg['text'].strip().lower()
    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None

    if request.sid in Table_UserSessions:
        Table_UserSessions[request.sid].update_chat(msg['text'])

    intensity = sentiment.getIntensity('. '.join(Table_UserSessions[request.sid].get_chat_history()))
    Table_UserSessions[request.sid].intensity = intensity

    # Get the Context-Id
    context_id = Table_UserSessions[request.sid].context_id
    Table_UserSessions[request.sid].context_id = None
    
    if context_id in [1, 4]:
        msg['id'] = 'on_create_incident'
        on_create_incident(msg)

    elif context_id == 2:
        msg['id'] = 'on_enquire_incident'
        on_enquire_incident(msg)

    elif context_id in ['on_create_incident', 'on_enquire_incident']:
        if msg_text in im_corpus.corpus_yes_no['yes']:
            msg['id'] = 0
            process_message_with_id(msg)
        elif msg_text in im_corpus.corpus_yes_no['no']:
            obj = {
                    'from'      : 'bot',
                    'type'      : 'request-feedback',
                    'text'      : 'Thank you. Please provide feedback on your experience with us. Your feedback helps us serve you better',
                    'timestamp' : time.strftime("%I:%M %p"),
                    'idToken'   : OTP,
                    'intensity' : intensity
                    }
            emit_n_print('message', obj)
        else:
            process_message_freetext(msg)

    elif context_id == 94:
        msg['id'] = 'on_update_incident'
        on_update_incident(msg)

    elif msg['text'] == "Search":
        search(msg)


    elif msg_text in im_corpus.corpus_options['option_incident_create']:
        msg['id'] = 1
        process_message_with_id(msg)

    elif msg_text in im_corpus.corpus_options['option_incident_enquiry']:
        msg['id'] = 2
        process_message_with_id(msg)

    elif msg_text in im_corpus.corpus_quit['quit']:
        obj = {
                'from'      : 'bot',
                'type'      : 'request-feedback',
                'text'      : 'Thank you. Please provide feedback on your experience with us. Your feedback helps us serve you better',
                'timestamp' : time.strftime("%I:%M %p"),
                'idToken'   : OTP,
                'intensity' : intensity
                }
        emit_n_print('message', obj)

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
                'timestamp' : time.strftime("%I:%M %p"),
                'idToken'   : OTP,
                'intensity' : intensity
                }
        emit_n_print('message', obj)

    else:
        obj = {
                'from'      : 'bot',
                'type'      : 'text',
                'text'      : "I'm sorry. I don't think I've understood your query. Please write an email to chatbot@innominds.com for more help. Thank you",
                'timestamp' : time.strftime("%I:%M %p"),
                'idToken'   : OTP,
                'intensity' : intensity
                }
        emit_n_print('message', obj)


#-----------------------------------------------------------------------------------------------------------------------
def on_create_incident(msg):
    Table_UserSessions[request.sid].context_id = msg['id']
    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None
    intensity = Table_UserSessions[request.sid].intensity

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
                    'timestamp' : time.strftime("%I:%M %p"),
                    'idToken'   : OTP,
                    'intensity' : intensity
                    }
            obj2 = {
                    'from'      : 'bot',
                    'type'      : 'prompt-action',
                    'text'      : "Can I help you with anything else?",
                    'timestamp' : time.strftime("%I:%M %p"),
                    'idToken'   : OTP,
                    'intensity' : intensity,
                    'options': [
                                  {
                                      'id': 91,
                                      'name': 'No'
                                  },
                                  {
                                      'id': 92,
                                      'name': 'Yes'
                                  }
                                ]
                    }

            emit_n_print('message', obj)
            emit_n_print('message', obj2)

    else:
        Table_UserSessions[request.sid].msg_waiting_for_login = msg

        obj = {
                'from'      : "bot",
                'type'      : "mandatory-action",
                'text'      : "Please click this link to signin first",
                'timestamp' : time.strftime("%I:%M %p"),
                'idToken'   : None,
                'intensity' : intensity,
                'options'   : [
                                {
                                    'id'    : 0,
                                    'name'  : 'signin'
                                }
                              ]
              }

        emit_n_print('message', obj)


#-----------------------------------------------------------------------------------------------------------------------
def on_enquire_incident(msg):
    
    Table_UserSessions[request.sid].context_id = msg['id']
    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None
    intensity = Table_UserSessions[request.sid].intensity

    if request.sid in Table_UserSessions\
        and Table_UserSessions[request.sid].isActive()\
        and msg.get('idToken'):
            Table_UserSessions[request.sid].incident_id_enquired = id_incident = msg['text']
            incident_status = ''
            res = inc_mgr.incident_status(id_incident)

            if res == 'INVALID_ID':
                text = "Ticket number seems to be invalid. Could you please check and try again?"
            elif res == 'SERVER_ISSUE':
                text = "Sorry. Couldn't get the state of your incident due to some issue with server"
            else:
                incident_status = res
                text = "The state of your ticket ({id}) is: {state}".format(id=id_incident, state=incident_status)

            obj = {
                    'from'      : 'bot',
                    'type'      : 'text',
                    'text'      : text,
                    'timestamp' : time.strftime("%I:%M %p"),
                    'idToken'   : OTP,
                    'intensity' : intensity
                    }
            emit_n_print('message', obj)

            if incident_status and not inc_mgr.is_incident_resolved(incident_status):
                obj2 = {
                        'from'      : 'bot',
                        'type'      : 'prompt-action',
                        'text'      : "Do you want to update anything on this ticket (%s)?"%id_incident,
                        'timestamp' : time.strftime("%I:%M %p"),
                        'idToken'   : OTP,
                        'intensity' : intensity,
                        'options': [
                                      {
                                          'id': 93,
                                          'name': 'No'
                                      },
                                      {
                                          'id': 94,
                                          'name': 'Yes'
                                      }
                                    ]
                        }
                emit_n_print('message', obj2)

            else:
                obj2 = {
                        'from'      : 'bot',
                        'type'      : 'prompt-action',
                        'text'      : "Can I help you with anything else?",
                        'timestamp' : time.strftime("%I:%M %p"),
                        'idToken'   : OTP,
                        'intensity' : intensity,
                        'options': [
                                      {
                                          'id': 91,
                                          'name': 'No'
                                      },
                                      {
                                          'id': 92,
                                          'name': 'Yes'
                                      }
                                    ]
                        }

                emit_n_print('message', obj2)

    else:
        Table_UserSessions[request.sid].msg_waiting_for_login = msg

        obj = {
                'from'      : "bot",
                'type'      : "mandatory-action",
                'text'      : "Please click this link to signin first",
                'timestamp' : time.strftime("%I:%M %p"),
                'idToken'   : None,
                'intensity' : intensity,
                'options'   : [
                                {
                                    'id'    : 0,
                                    'name'  : 'signin'
                                }
                              ]
              }

        emit_n_print('message', obj)


#-----------------------------------------------------------------------------------------------------------------------
def on_update_incident(msg):

    Table_UserSessions[request.sid].context_id = msg['id']
    OTP = Table_UserSessions[request.sid].otp if Table_UserSessions.get(request.sid) and msg.get('idToken') else None
    intensity = Table_UserSessions[request.sid].intensity

    if request.sid in Table_UserSessions\
        and Table_UserSessions[request.sid].isActive()\
        and msg.get('idToken'):
            id_incident = Table_UserSessions[request.sid].incident_id_enquired
            update_text = msg['text']
            res = inc_mgr.incident_update(id_incident, update_text)

            if res == 'SUCCESS':
                obj = {
                        'from'      : 'bot',
                        'type'      : 'text',
                        'text'      : "Your incident (%s) is updated"%id_incident,
                        'timestamp' : time.strftime("%I:%M %p"),
                        'idToken'   : OTP,
                        'intensity' : intensity
                        }
            else:
                obj = {
                        'from'      : 'bot',
                        'type'      : 'text',
                        'text'      : "Your incident {incident} could not be updated due to following error: {err}".format(incident=id_incident, err=res),
                        'timestamp' : time.strftime("%I:%M %p"),
                        'idToken'   : OTP,
                        'intensity' : intensity
                        }

            emit_n_print('message', obj)

            obj2 = {
                    'from'      : 'bot',
                    'type'      : 'prompt-action',
                    'text'      : "Can I help you with anything else?",
                    'timestamp' : time.strftime("%I:%M %p"),
                    'idToken'   : OTP,
                    'intensity' : intensity,
                    'options': [
                                  {
                                      'id': 91,
                                      'name': 'No'
                                  },
                                  {
                                      'id': 92,
                                      'name': 'Yes'
                                  }
                                ]
                    }
            emit_n_print('message', obj2)


#-----------------------------------------------------------------------------------------------------------------------
def emit_n_print(evt_name, msg):
    # msg['idToken'] = idToken
    emit(evt_name, msg)
    print "SERVER:: Sent message:\n", msg, "\n"


#-----------------------------------------------------------------------------------------------------------------------
def make_header(metadata):
    return {i:j for i,j in zip(('from', 'type', 'text', 'timestamp', 'idToken', 'intensity'), metadata)}


#-----------------------------------------------------------------------------------------------------------------------
def make_options(data, msg_id):
    return {'options' : [{i:j for i,j in zip(('id', 'name'), (msg_id*10+row[0], row[1]))} for row in data]}


#-----------------------------------------------------------------------------------------------------------------------
def make_obj(metadata, data, msg_id):
    d = {}

    d.update(make_header(metadata))
    d.update(make_options(data, msg_id))

    return d


#-----------------------------------------------------------------------------------------------------------------------
@app.before_request
def make_session_permanent():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=5)

#-----------------------------------------------------------------------------------------------------------------------

def search(msg):
    idandtitle = ""
    needtool = ""
    eof = "Y"
    
    searchtext = msg.get('searchtext').encode('ascii', 'ignore')
    isfirsttime = msg.get('is_first_time').encode('ascii', 'ignore')
    url = 'http://192.168.204.13:5000/search_kr'
    print('searchtext -->>> ', searchtext)
    head = {"text":searchtext, "is_first_time":isfirsttime, "Content-type": "application/x-www-form-urlencoded"}
    response = requests.post(url,headers=head)
    print('Response========== >>>',response.json())
    for topic in response.json()['response']['topics']:
        for incident in topic['incidents']:
            idandtitle = idandtitle + incident['id'] + "-" +incident['title'] + "-" +incident['solution'] + "###"

    needtool = response.json()['response']['need_tool']
    print('needtool =========>>>',needtool)
    if needtool == "Y":
        idandtitle = "Do you have any tool information, if yes can you please provide (yes/no) ?"
        eof = "N"
    else:
        if len(response.json()['response']['topics']) == 0:
            idandtitle = "No results found for entered text"
       
    obj = {
            'from'      : 'bot',
            'type'      : 'text',
            'text'      : idandtitle,
            'timestamp' : time.strftime("%I:%M %p"),
            'idToken'   : '',
            'intensity' : '',
            'searchtext': searchtext,
            'need_tool' : needtool,
            'id'        : 5,
            'eof'       : eof
            }

    emit_n_print('message', obj)
    


