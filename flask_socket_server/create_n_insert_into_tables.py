import psycopg2


conn = None

conn_params = {
                "host"     : "localhost",
                "port"     : "5432", 
                "database" : "deloitte_ims",
                "user"     : "postgres",
                "password" : "postgres"
                }


commands_create_n_insert= (
    # Users table
    """
    CREATE TABLE ims_users(user_name TEXT PRIMARY KEY NOT NULL, password TEXT NOT NULL, otp INT);
    """,

    """
    INSERT INTO ims_users values ('murali', 'pass1');
    """,
    """
    INSERT INTO ims_users values ('rajesh', 'pass2');
    """,
    """
    INSERT INTO ims_users values ('sarath', 'pass3');
    """,


    # Chat histiry table
    """
    CREATE TABLE ims_user_chat (user_name TEXT NOT NULL,
                                chat_text TEXT NOT NULL,
                                chat_end_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
                                feedback TEXT NOT NULL);
    """,


    # First level (master table)
    """
    CREATE TABLE ims_master_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_master_meta VALUES ('bot',
                                        'option', 
                                        'Hi, I''m Elisa. I can help you on the below topics. Please click on one of them basded on what you need');
    """,

    """
    CREATE TABLE ims_master (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_master (name, child) VALUES ('Incident Creation', 'ims_IncidentCreation'),
                                                 ('Incident Enquiry', 'ims_IncidentEnquiry'),
                                                 ('Information', 'ims_Information');
    """,


    # Second level (for option 1)
    """
    CREATE TABLE ims_IncidentCreation_Meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_IncidentCreation_Meta VALUES ('bot',
                                                  'text',
                                                  'Can you please briefly describe the problem you are facing?');
    """,

    """
    CREATE TABLE ims_IncidentCreation (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,


    # Second level (for option 2)
    """
    CREATE TABLE ims_IncidentEnquiry_Meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_IncidentEnquiry_Meta VALUES ('bot',
                                                 'text',
                                                 'Can you please share the ticket reference number?');
    """,

    """
    CREATE TABLE ims_IncidentEnquiry (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,


    # Second level (for option 3)
    """
    CREATE TABLE ims_Information_Meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_Information_Meta VALUES ('bot',
                                             'option',
                                             'On which of the following topics do you need information?');
    """,

    """
    CREATE TABLE ims_Information (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_Information (name, child) VALUES ('Access Issues', 'ims_AccesIssues'),
                                                     ('Software Concerns', 'ims_SoftwareConcerns'),
                                                     ('Hardware Problems', 'ims_HardwareProblems'),
                                                     ('Network Challenges', 'ims_NetworkChallenges'),
                                                     ('Server Connections', 'ims_ServerConnections');
    """,



    # Third level
    """
    CREATE TABLE ims_AccesIssues_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_AccesIssues_meta VALUES ('bot',
                                             'option',
                                             'Pick a category');
    """,

    """
    CREATE TABLE ims_AccesIssues (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_AccesIssues (name, child) VALUES ('New Registration', 'ims_NewRegistration'),
                                                     ('Existing User', 'ims_ExistingUser');
    """,


    """
    CREATE TABLE ims_SoftwareConcerns_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_SoftwareConcerns_meta VALUES ('bot',
                                                  'option',
                                                  'Pick a category');
    """,

    """
    CREATE TABLE ims_SoftwareConcerns (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_SoftwareConcerns (name, child) VALUES ('License related', 'ims_LicenseRelated'),
                                                          ('Malfunction related', 'ims_MalfunctionRelated'),
                                                          ('Virus Threats & Phishing', 'ims_VirusThreatsPhishing');
    """,



    """
    CREATE TABLE ims_HardwareProblems_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_HardwareProblems_meta VALUES ('bot',
                                                  'option',
                                                  'Pick a category');
    """,

    """
    CREATE TABLE ims_HardwareProblems (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_HardwareProblems (name, child) VALUES ('Printer related', 'ims_PrinterRelated'),
                                                          ('Display related', 'ims_DisplayRelated'),
                                                          ('Keyboard related','ims_KeyboardRelated'),
                                                          ('Mouse related', 'ims_MouseRelated');
    """,


    """
    CREATE TABLE ims_NetworkChallenges_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_NetworkChallenges_meta VALUES ('bot',
                                                   'option',
                                                   'Pick a category');
    """,

    """
    CREATE TABLE ims_NetworkChallenges (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_NetworkChallenges (name, child) VALUES ('Wireless network', 'ims_WirelessNetwork'),
                                                           ('Wired network', 'ims_WiredNetwork');
    """,


    """
    CREATE TABLE ims_ServerConnections_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_ServerConnections_meta VALUES ('bot',
                                                   'option',
                                                   'Pick a category');
    """,

    """
    CREATE TABLE ims_ServerConnections (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_ServerConnections (name, child) VALUES ('New Server', 'ims_NewServer'),
                                                           ('Existing Server', 'ims_ExistingServer');
    """,



    # Fourth level
    """
    CREATE TABLE ims_NewRegistration_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_NewRegistration_meta VALUES ('bot',
                                                 'questions',
                                                 'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_NewRegistration (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_NewRegistration (name) VALUES ('What are the steps to be followed during a new user registration?'),
                                                  ('I already followed the steps in the new registration, still I am unable to access');
    """,


    """
    CREATE TABLE ims_ExistingUser_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_ExistingUser_meta VALUES ('bot',
                                              'questions',
                                              'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_ExistingUser (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_ExistingUser (name) VALUES ('I forgot my username'),
                                               ('I forgot my password'),
                                               ('I remember username and password but I am unable to login');
    """,


    """
    CREATE TABLE ims_LicenseRelated_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_LicenseRelated_meta VALUES ('bot',
                                                'questions',
                                                'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_LicenseRelated (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_LicenseRelated (name) VALUES ('My software license got expired. Can you renew it?'),
                                                 ('I need a license for a software'),
                                                 ('Can you revoke the license?');
    """,


    """
    CREATE TABLE ims_MalfunctionRelated_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_MalfunctionRelated_meta VALUES ('bot',
                                                    'questions',
                                                    'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_MalfunctionRelated (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_MalfunctionRelated (name) VALUES ('I lost my data. Can you recover it?'),
                                                     ('My system is hanging'),
                                                     ('Can you re-install a software?'),
                                                     ('Can you provide/remove admin privileges?');
    """,


    """
    CREATE TABLE ims_VirusThreatsPhishing_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_VirusThreatsPhishing_meta VALUES ('bot',
                                                       'questions',
                                                       'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_VirusThreatsPhishing (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_VirusThreatsPhishing (name) VALUES ('I am suspecting a phishing incident'),
                                                       ('My system seems to be attacked by a virus');
    """,


    """
    CREATE TABLE ims_PrinterRelated_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_PrinterRelated_meta VALUES ('bot',
                                                'questions',
                                                'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_PrinterRelated (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_PrinterRelated (name) VALUES ('Find my nearest printer'),
                                                 ('Unable to connect to a printer'),
                                                 ('Printer is not working'),
                                                 ('Refill the catridge'),
                                                 ('Fill up the papers');
    """,


    """
    CREATE TABLE ims_DisplayRelated_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_DisplayRelated_meta VALUES ('bot',
                                                'questions',
                                                'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_DisplayRelated (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_DisplayRelated (name) VALUES ('Unable to see any display'),
                                                 ('My screen is flickering'),
                                                 ('Replace my monitor');
    """,


    """
    CREATE TABLE ims_KeyboardRelated_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_KeyboardRelated_meta VALUES ('bot',
                                                 'questions',
                                                 'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_KeyboardRelated (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_KeyboardRelated (name) VALUES ('Some keys are not detecting'),
                                                  ('Keyboard is not working'),
                                                  ('Replace my keyboard');
    """,


    """
    CREATE TABLE ims_MouseRelated_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_MouseRelated_meta VALUES ('bot',
                                              'questions',
                                              'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_MouseRelated (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_MouseRelated (name) VALUES ('Mouse sensitivity has to be changed'),
                                               ('Replace my mouse');
    """,


    """
    CREATE TABLE ims_WirelessNetwork_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_WirelessNetwork_meta VALUES ('bot',
                                                 'questions',
                                                 'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_WirelessNetwork (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_WirelessNetwork (name) VALUES ('Unable to connect to Wireless network'),
                                                  ('Wireless network is slow');
    """,


    """
    CREATE TABLE ims_WiredNetwork_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_WiredNetwork_meta VALUES ('bot',
                                              'questions',
                                              'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_WiredNetwork (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_WiredNetwork (name) VALUES ('Unable to connect to Wired network'),
                                               ('Provide with a new LAN wire');
    """,


    """
    CREATE TABLE ims_NewServer_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_NewServer_meta VALUES ('bot',
                                           'option',
                                           'Pick a category');
    """,

    """
    CREATE TABLE ims_NewServer (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_NewServer (name, child) VALUES ('In-house', 'ims_InHouse'),
                                                   ('Over cloud', 'ims_OverCloud');
    """,


    """
    CREATE TABLE ims_ExistingServer_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_ExistingServer_meta VALUES ('bot',
                                                'questions',
                                                'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_ExistingServer (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_ExistingServer (name) VALUES ('Unable to access the server'),
                                                 ('Add a new login to the existing server'),
                                                 ('Upgrade/Downgrade the configuration');
    """,



    # Fifth level
    """
    CREATE TABLE ims_InHouse_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_InHouse_meta VALUES ('bot',
                                         'questions',
                                         'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_InHouse (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_InHouse (name) VALUES ('Configuration requirements'),
                                          ('Possible locations');
    """,


    """
    CREATE TABLE ims_OverCloud_meta (_from TEXT DEFAULT 'bot', _type TEXT, _text TEXT);
    """,
    """
    INSERT INTO ims_OverCloud_meta VALUES ('bot',
                                           'questions',
                                           'Click on appropriate link for further information - ');
    """,

    """
    CREATE TABLE ims_OverCloud (id SERIAL PRIMARY KEY NOT NULL, name TEXT NOT NULL, child TEXT);
    """,
    """
    INSERT INTO ims_OverCloud (name) VALUES ('AWS'),
                                            ('Digital Ocean'),
                                            ('Vultr');
    """
    )


# connect to the server
# create tables
# insert data

try:
    conn = psycopg2.connect(**conn_params)
    cur = conn.cursor()
    
    for cmd in commands_create_n_insert:
        cur.execute(cmd)
    cur.close()
    conn.commit()

except (Exception, psycopg2.DatabaseError) as error:
    print error

finally:
    conn and conn.close()

