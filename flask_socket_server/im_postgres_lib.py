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
    def Get_Child(self, table, id):
        self.cur.execute("SELECT child FROM {table_name} WHERE id={id}".format(table_name=table, id=id))
        child = self.cur.fetchone()
        return child[0] if child else ''



# conn.commit()

# ==========================

# cur.execute("SELECT vendor_id, vendor_name FROM vendors ORDER BY vendor_name")
# print("The number of parts: ", cur.rowcount)

# row = cur.fetchone()
# while row is not None:
#     print(row)
#     row = cur.fetchone()
 
# ==========================
# rows = cur.fetchall()

# fetchmany()

# ==========================
# psycopg2.connect(database="testdb", user="postgres", password="postgres", host="127.0.0.1", port="5432")

# cur.execute('''CREATE TABLE tyty (ID INT PRIMARY KEY  NOT NULL,  NAME TEXT  NOT NULL,  AGE  INT  NOT NULL,  ADDRESS  CHAR(50),  SALARY  REAL);''')



#   ++++++++++++++
# CREATE DATABASE dbname;
# \l
# \c testdb;

# CREATE TABLE COMPANY (ID INT PRIMARY KEY     NOT NULL,   NAME TEXT    NOT NULL,   AGE            INT     NOT NULL,   ADDRESS        CHAR(50),   SALARY         REAL);
