import sqlite3 as lite
import sys
from collections import namedtuple

nodes_db='pce.db'

def Create_initial_db(graph_nodes):
    db_filename = 'pce.db'
    insert_query = """INSERT INTO NODES(NODE_NAME,ISO_ID,ROUTER_ID,SR_ID)
                      VALUES (:NODE_NAME,:ISO_ID,:ROUTER_ID,:SR_ID)
                   """
    print ("Creating Initial DB and Schema for Node Attributes")
    try:
        conn = lite.connect(nodes_db)
        cur = conn.cursor()
        cur.execute("DROP TABLE if EXISTS NODES")
        cur.execute("CREATE TABLE NODES(NODE_NAME TEXT PRIMARY KEY,ISO_ID TEXT,ROUTER_ID TEXT,SR_ID INT)")
        cur.execute("CREATE INDEX index_name on NODES(NODE_NAME)")
        cur.execute("CREATE INDEX index_id on NODES(ISO_ID)")
        for node in graph_nodes.nodes(data=True):
            node_attr= [[node[1]["name"],node[1]["iso_id"],node[1]["router_id"],node[1]["nodesid"]]]
            cur.executemany(insert_query,node_attr)
        conn.commit()
    except lite.Error as e:
        if conn:
            conn.rollback()
        print ("Error %s",e)
        sys.exit(1)
    finally:
        if conn:
            conn.close()

def Query_node_name(node_id):
    db_filename = 'pce.db'
    try:
        conn=lite.connect(nodes_db)
        cur = conn.cursor()
        cur.execute("SELECT NODE_NAME FROM NODES WHERE ISO_ID=:ISO_ID",{"ISO_ID":node_id})
        conn.commit()
        node_name = cur.fetchone()
    except:
        if conn:
            conn.rollback()
        print ("Error Occured while Querying Node Name ")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    return (node_name[0])

def Query_node_id(node_name):
    db_filename = 'pce.db'
    try:
        conn=lite.connect(nodes_db)
        cur = conn.cursor()
        cur.execute("SELECT ISO_ID FROM NODES WHERE NODE_NAME=:NODE_NAME",{"NODE_NAME":node_name})
        conn.commit()
        node_id = cur.fetchone()
    except:
        if conn:
            conn.rollback()
        print ("Error Occured while Querying Node Name ")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    return (node_id[0])

def Query_node_ip(node_name):
    db_filename = 'pce.db'
    try:
        conn=lite.connect(nodes_db)
        cur = conn.cursor()
        cur.execute("SELECT ROUTER_ID FROM NODES WHERE NODE_NAME=:NODE_NAME",{"NODE_NAME":node_name})
        conn.commit()
        node_ip = cur.fetchone()
    except:
        if conn:
            conn.rollback()
        print ("Error Occured while Querying Node IP")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    return (node_ip[0])

def Query_all_nodes():
    try:
        conn = lite.connect(nodes_db)
        conn.row_factory = lambda cursor,row: row[0]
        cur = conn.cursor()
        cur.execute("SELECT NODE_NAME FROM NODES")
        conn.commit()
        node_names = cur.fetchall()
    except:
        if conn:
            conn.rollback()
        print ("Error Occured while Querying Node IP")
        sys.exit(1)

    finally:
        if conn:
            conn.close()

    return (node_names)

def Query_check_node(node_name):
    try:
        conn = lite.connect(nodes_db)
        conn.row_factory = lambda cursor,row: row[0]
        cur = conn.cursor()
        cur.execute("SELECT NODE_NAME from NODES WHERE NODE_NAME=:NODE_NAME",{"NODE_NAME":node_name})
        conn.commit()
        node_names = cur.fetchone()
        check_node_result = False
        if node_name == node_names:
            check_node_result = True
    except:
        if conn:
            conn.rollback()
        print ("Error Occured while Querying Node Node")
        sys.exit(1)
    finally:
        if conn:
            conn.close()

    return(check_node_result)

def Query_node_ip_sid(node_name):
    db_filename = 'pce.db'
    try:
        conn=lite.connect(nodes_db)
        cur = conn.cursor()
        cur.execute("SELECT ROUTER_ID,SR_ID FROM NODES WHERE NODE_NAME=:NODE_NAME",{"NODE_NAME":node_name})
        conn.commit()
        node_ip_sid = cur.fetchone()
    except:
        if conn:
            conn.rollback()
        print ("Error Occured while Querying Node IP")
        sys.exit(1)
    finally:
        if conn:
            conn.close()
    return (node_ip_sid[0],node_ip_sid[1])
