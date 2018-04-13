
table_incident_managers = \
{
    'SERVIE_NOW' : 'im_service_now'
}

def get_manager(inc_mgr_id):
	return table_incident_managers.get(inc_mgr_id)
	