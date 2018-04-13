# -*- coding: utf-8 -*-

import json
import requests



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

