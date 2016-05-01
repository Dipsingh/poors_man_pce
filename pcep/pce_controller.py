__author__ = 'dipsingh'

import socket,zmq,sys,pika,pickle,functools
import gevent,pickle,json
#import pcep_handler
#import te_controller
from pcep.pcep_handler import *
from pcep.te_controller import *
from gevent import monkey
monkey.patch_socket()
#import zmq,os,string,time
import zmq.green as zmq

MAXCLIENTS = 10
PCEADDR='0.0.0.0'
PCEPORT=4189

def parse_config(pce_config_file):
    SR_TE = False
    TunnelName =''
    ERO_LIST = list() # ERO List
    TUNNEL_SRC_DST = list()  #Tunnel Source and Destination
    LSPA_PROPERTIES = list() #Setup Priority,Hold Priority,Local Protection Desired(0 means false)
    SR_ERO_LIST = list() # ERO List with SR Labels
    with open(pce_config_file) as data_file:
        data= json.load(data_file)
    for key in data:
        if key == 'TunnelName':
            TunnelName = data[key]
        if key == 'SR-TE':
            SR_TE = data[key]
        if key == 'EndPointObject':
            for endpoint in data[key]:
                if endpoint == 'Tunnel_Source':
                    TUNNEL_SRC_DST.insert(0,data[key][endpoint])
                if endpoint == 'Tunnel_Destination':
                    TUNNEL_SRC_DST.insert(1,data[key][endpoint])
        if key == 'LSPA_Object':
            for lspa_object in data[key]:
                if lspa_object == 'Hold_Priority':
                    LSPA_PROPERTIES.insert(0,data[key][lspa_object])
                if lspa_object == 'Setup_Priority':
                    LSPA_PROPERTIES.insert(1,data[key][lspa_object])
                if lspa_object == 'FRR_Desired':
                    LSPA_PROPERTIES.insert(2,data[key][lspa_object])
        if key == 'ERO_LIST':
            for ero in data[key]:
                for key_ip in ero:
                    ERO_LIST.append(key_ip)
        if key == 'SR_ERO_LIST':
            for ero in data[key]:
                for sr_ip in ero:
                    SR_ERO_LIST.append((sr_ip,ero[sr_ip]))
    return (SR_TE,str.encode(TunnelName),tuple(TUNNEL_SRC_DST),tuple(LSPA_PROPERTIES),tuple(ERO_LIST),tuple(SR_ERO_LIST))

def send_ka(client_sock,pcep_context):
    while True:
        client_sock.send(pcep_context.generate_ka_msg())
        gevent.sleep(pcep_context._ka_timer)

'''
def check_queue(client_sock):
    connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
    channel = connection.channel()
    result = channel.queue_declare(queue='pcep_queue')
    channel.queue_bind(exchange='pcep-exchange',queue="pcep_queue",routing_key='pcep-key')
    channel.basic_consume(callback,queue="pcep_queue",no_ack=True)
    print ("Checking Queue for MSGS for Client",client_sock)
    channel.start_consuming()
    print ("Checked Queue Going for sleep")
    gevent.sleep(5)

def callback(ch, method, properties,body):
    recvd_obj=pickle.loads(body)
    #print ("For Client",client_sock)
    print(" [x] Received ",recvd_obj)
'''


def pcc_handler(client_sock,sid,controller):
    PCE_INIT_FlAG= True
    PCE_UPD_FLAG = False
    pcep_context = PCEP(open_sid = sid)
    print ("Received Client Request from ",client_sock[1])
    msg_received = client_sock[0].recv(1000)
    pcep_context.parse_recvd_msg(msg_received)
    client_sock[0].send(pcep_context.generate_open_msg(30))
    ka_greenlet = gevent.spawn(send_ka,client_sock[0],pcep_context)

    print ("Trying Subscribe to PCE")
    #check_queue_greenlet=subscribe_to_pce()
    check_queue_greenlet = gevent.spawn(subscribe_to_pce,client_sock,pcep_context)
    print ("Received this from SUBSCRIBE TO PCE",check_queue_greenlet)
    while True:
        msg= client_sock[0].recv(1000)
        parsed_msg = pcep_context.parse_recvd_msg(msg)
        result = controller.handle_pce_message(client_sock[1],parsed_msg)
        if PCE_UPD_FLAG:
            if result:
                if result[0]!=None:
                    for key in result[1]:
                        pcep_msg_upd = pcep_context.generate_lsp_upd_msg(result[1][key],parsed_results[4])
                        print ("Sending PCC Update Request")
                        if pcep_msg_upd:
                            client_sock[0].send(pcep_msg_upd)
        '''
        if PCE_INIT_FlAG:
            if parsed_results[0]:
                pcep_msg_init = pcep_context.generate_sr_lsp_inititate_msg(parsed_results[5],parsed_results[2],parsed_results[3],parsed_results[1])
                print ("Creating SR TE Tunnel")
                if pcep_msg_init:
                    client_sock[0].send(pcep_msg_init)
            else:
                pcep_msg_init = pcep_context.generate_lsp_inititate_msg(parsed_results[4],parsed_results[2],parsed_results[3],parsed_results[1])
                print ("Creating TE Tunnel")
                if pcep_msg_init:
                    client_sock[0].send(pcep_msg_init)
            PCE_INIT_FlAG=False
        '''
    client_sock[0].close()

def push_sr_tunnel(client_sock,parsed_results,pcep_context):
    print ("All the Client Sockets are",client_sock)
    if parsed_results[0]=='True':
        pcep_msg_init = pcep_context.generate_sr_lsp_inititate_msg(parsed_results[5],parsed_results[2],parsed_results[3],str.encode(parsed_results[1]))
        print ("Creating SR TE Tunnel")
        if pcep_msg_init:
            client_sock[0].send(pcep_msg_init)
    else:
        pcep_msg_init = pcep_context.generate_lsp_inititate_msg(parsed_results[4],parsed_results[2],parsed_results[3],str.encode(parsed_results[1]))
        print ("Creating TE Tunnel")
        if pcep_msg_init:
            client_sock[0].send(pcep_msg_init)


def subscribe_to_pce(client_sock,pcep_context):
    xsub_url = "tcp://127.0.0.1:50001"
    context= zmq.Context()
    sub_socket=context.socket(zmq.SUB)
    sub_socket.connect(xsub_url)
    sub_socket.setsockopt(zmq.SUBSCRIBE,b'')
    while True:
        try:
            parsed_results=sub_socket.recv_json()
            print ("The Client is ",client_sock[1])
            print ("Recieved Following from Pub Data",parsed_results)
            if parsed_results:
                if client_sock[1][0] == parsed_results[0]:
                    print ("The Headend Router is",parsed_results[0])
                    print ("The Data sent is ",parsed_results[1])
                    push_sr_tunnel(client_sock,parsed_results[1],pcep_context)
                return parsed_results
        except zmq.error.Again as e:
            if str("Resource temporarily unavailable") in e:
                return None
            else:
                raise ("Exception occured")


def pcep_main ():
    print ("PCEP Thread Started")
    CURRENT_SID=0
    pce_server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    #controller = te_controller.TEController()
    controller = TEController()
    pce_server_sock.bind((PCEADDR,PCEPORT))
    pce_server_sock.listen(MAXCLIENTS)
    print ("Listening on socket",pce_server_sock)
    while True:
        client = pce_server_sock.accept()
        gevent.spawn(pcc_handler,client,CURRENT_SID,controller)
        CURRENT_SID += 1


'''
def main ():
    CURRENT_SID=0
    parsed_results =parse_config('PCE_Config.json')
    pce_server_sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    controller = te_controller.TEController()
    pce_server_sock.bind((PCEADDR,PCEPORT))
    pce_server_sock.listen(MAXCLIENTS)
    while True:
        client = pce_server_sock.accept()
        gevent.spawn(pcc_handler,client,CURRENT_SID,controller)
        CURRENT_SID += 1

if __name__ == '__main__':
    main()
'''
