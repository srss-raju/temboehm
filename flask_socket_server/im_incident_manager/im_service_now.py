# -*- coding: utf-8 -*-

import json
import requests


# map incident_id -> sys_id
table_incId_sysId = {}


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
    url = 'https://dev18273.service-now.com/api/now/v2/table/incident?sysparm_display_value=true&sysparm_query=number={id_incident}'\
            .format(id_incident=id_incident)

    response = requests.get(url, auth=("admin", "qegZBqHH8gO3"))

    try:
        result = response.json()['result']
        incident_state = result[0]['incident_state'] if result else 'INVALID_ID'
    except Exception as e:
        print "ERROR: ", type(e), e
        incident_state = 'SERVER_ISSUE'
        print response

    if response.status_code == 200:
        result = response.json()['result']
        if result:
            sys_id = result[0]['sys_id']
            table_incId_sysId[id_incident] = sys_id

    return incident_state


#-----------------------------------------------------------------------------------------------------------------------
def incident_update(id_incident, update_text):
    sys_id = table_incId_sysId.get(id_incident)
    if not sys_id:
        return 'INVALID_ID'

    url = "https://dev18273.service-now.com/api/now/table/incident/%s"%sys_id

    payload = {
                'comments' : update_text,
              }

    response = requests.put(
                            url,
                            data = json.dumps(payload),
                            auth = ("admin", "qegZBqHH8gO3"),
                            headers = {'Content-type': 'application/json'}
                            )

    if response.status_code != 200:
        error = {
                    'status_code' : response.status_code,
                    'headers'     : response.headers,
                    'error_resp:' : response.json(),
                }
    else:
        return 'SUCCESS'


#-----------------------------------------------------------------------------------------------------------------------
def is_incident_resolved(incident_status):
    return True if incident_status.lower() == 'resolved' else False

