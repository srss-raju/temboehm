import psycopg2


class im_postgres:
    #-------------------------------------------------------------------------------------------------------------------
    def __init__(self, conn_params):
        self.conn = None
        self.cur  = None
        
        # connect to the server
        try:
            self.conn = psycopg2.connect(**conn_params)
            self._Get_Cursor()

        except (Exception, psycopg2.DatabaseError) as error:
            print error

    #-------------------------------------------------------------------------------------------------------------------
    def __del__(self):
        self._Close_Cursor()
        self._Close_Connection()

    #-------------------------------------------------------------------------------------------------------------------
    def isConnected(self):
        return self.conn and self.cur

    #-------------------------------------------------------------------------------------------------------------------
    def _Get_Cursor(self):
        # create a cursor
        self.cur = self.conn.cursor()
        return self.cur

    #-------------------------------------------------------------------------------------------------------------------
    def _Close_Cursor(self):
        # close the cursor
        if self.cur:
            self.cur.close()

    #-------------------------------------------------------------------------------------------------------------------
    def _Close_Connection(self):
        # close the connection
        if self.conn:
            self.conn.close()

    #-------------------------------------------------------------------------------------------------------------------
    def Get_RowsAll(self, table):
        # self.cur.execute("SELECT * FROM {table_name} ORDER BY id")
        self.cur.execute("SELECT * FROM {table_name}".format(table_name=table))
        return self.cur.fetchall()

    #-------------------------------------------------------------------------------------------------------------------
    def Get_RowFirst(self, table):
        # self.cur.execute("SELECT * FROM {table_name} ORDER BY id")
        self.cur.execute("SELECT * FROM {table_name}".format(table_name=table))
        return self.cur.fetchone()

    #-------------------------------------------------------------------------------------------------------------------
    def Get_RowById(self, table, id):
        self.cur.execute("SELECT * FROM {table_name} WHERE id={id}".format(table_name=table, id=id))
        return self.cur.fetchone()

    #-------------------------------------------------------------------------------------------------------------------
    def Get_RowsMatching(self, table, field, value):
        value = "'%s'"%value if type(value) in (str, unicode) else value
        self.cur.execute("SELECT * FROM {table_name} WHERE {fld}={val}".format(table_name=table, fld=field, val=value))
        return self.cur.fetchone()

    #-------------------------------------------------------------------------------------------------------------------
    def Get_Child(self, table, id):
        self.cur.execute("SELECT child FROM {table_name} WHERE id={id}".format(table_name=table, id=id))
        child = self.cur.fetchone()
        return child[0] if child else ''

    #-------------------------------------------------------------------------------------------------------------------
    def Update_Table(self, table, field, value, where_cond):
        self.cur.execute("UPDATE {table_name} SET {fld}={val} WHERE {where_cond}".format(table_name=table, fld=field, val=value, where_cond=where_cond))
        self.conn.commit()
    
    #-------------------------------------------------------------------------------------------------------------------
    def InsertInto_Table(self, table, fields, values):
        fields = '(' + ', '.join(fields) + ')'
        cmd = "INSERT INTO {table_name} {flds} VALUES {vals}".format(table_name=table, flds=fields, vals=values)
        self.cur.execute(cmd)
        self.conn.commit()
    
    
