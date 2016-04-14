import dboperations,zmq,json,pickle
from pcep.pce_controller import *
from plain_dijkstra import Copy_all_shortest_paths_plain as Copy_all_shortest_paths_plain
from exclude_link_dijkstra import Copy_all_shortest_paths_exclude_link as Copy_all_shortest_paths_exclude_link
from bandwidth_constraint_dijkstra import Copy_all_shortest_paths_bwconstraint as Copy_all_shortest_paths_bwconstraint
from bwconstraint_excludelink_dijkstra import Copy_all_shortest_paths_bwconstraint_excludelink as Copy_all_shortest_paths_bwconstraint_excludelink
from avoid_node import Copy_all_shortest_paths_avoidnode as Copy_all_shortest_paths_avoidnode
from avoid_node_link_color import Copy_all_shortest_paths_avoidnode_linkcolor


class Node_Tunnel_Tracker(object):
    head_ends = {}
    @classmethod
    def create(cls,node_name):
        head_end = Node_Tunnel_Tracker(node_name)
        cls.head_ends[node_name]=head_end
        return head_end
    def __init__(self,node_name):
        self.node_name = node_name
        self.tunnel_nu_start = 6500
        self.tunnel_nu_end = 6599
        self.current=self.tunnel_nu_start
        self.gen_stat = None

    def tunnel_nu(self):
        while self.current < self.tunnel_nu_end:
            yield self.current
            self.current += 1

def show_nodes():
    return dboperations.Query_all_nodes()

def check_nodes(extract_code):
    return dboperations.Query_check_node(extract_code)

def run_spf(graph_nodes,src_node,dst_node,metric):
    src_node_id =dboperations.Query_node_id(src_node)
    dst_node_id =dboperations.Query_node_id(dst_node)
    return spf(graph_nodes,src_node_id,dst_node_id,metric)

def run_spf_avoid_node(graph_nodes,src_node,dst_node,avoid_node,metric):
    src_node_id =dboperations.Query_node_id(src_node)
    dst_node_id =dboperations.Query_node_id(dst_node)
    avoid_node_id = dboperations.Query_node_id(avoid_node)
    return spf(graph_nodes,src_node_id,dst_node_id,metric,avoid_node=avoid_node_id)

def run_spf_avoid_node_color(graph_nodes,src_node,dst_node,avoid_node,color_exc_inc,color,metric):
    src_node_id =dboperations.Query_node_id(src_node)
    dst_node_id =dboperations.Query_node_id(dst_node)
    avoid_node_id = dboperations.Query_node_id(avoid_node)
    return spf(graph_nodes,src_node_id,dst_node_id,metric,color=color,color_exc_inc=color_exc_inc,avoid_node=avoid_node_id)

def run_spf_avoid_color(graph_nodes,src_node,dst_node,color_exc_inc,color,metric):
    src_node_id =dboperations.Query_node_id(src_node)
    dst_node_id =dboperations.Query_node_id(dst_node)
    return spf(graph_nodes,src_node_id,dst_node_id,metric,color=color,color_exc_inc=color_exc_inc)

def spf(graph_nodes,node_a,node_b,weight,color=None,color_exc_inc=None,bw_constraint=None,avoid_node=None):
    if (color_exc_inc and bw_constraint):
        path_list = Copy_all_shortest_paths_bwconstraint_excludelink(graph_nodes,source=node_a,target=node_b,weight=weight,color=color,color_exc_inc=color_exc_inc,bw_constraint=bw_constraint)
    elif(color_exc_inc and avoid_node):
        path_list = Copy_all_shortest_paths_avoidnode_linkcolor(graph_nodes,source=node_a,target=node_b,weight=weight,avoid_node=avoid_node,color=color,color_exc_inc=color_exc_inc)
    elif color_exc_inc:
        path_list = Copy_all_shortest_paths_exclude_link(graph_nodes,source=node_a,target=node_b,weight=weight,color=color,color_exc_inc=color_exc_inc)
    elif bw_constraint:
        path_list = Copy_all_shortest_paths_bwconstraint(graph_nodes,source=node_a,target=node_b,weight=weight,bw_constraint=bw_constraint)
    elif avoid_node:
        path_list = Copy_all_shortest_paths_avoidnode(graph_nodes,source=node_a,target=node_b,weight=weight,avoid_node=avoid_node)
    else:
        path_list = Copy_all_shortest_paths_plain(graph_nodes,source=node_a,target=node_b,weight=weight)

    node_name_list = list()
    if path_list:
        for p in path_list:
            temp_list = list()
            for x in p:
                temp_list.append(dboperations.Query_node_name(x))
            node_name_list.append(temp_list)
    return (node_name_list)

def pcep_interface(path_list,graph_nodes):
    client_port = "50000"

    #server_port = "50001"
    #server_context=zmq.Context()
    #server_socket = self.server_context.socket(zmq.REP)
    #server_socket.bind("tcp://*:%s" % self.server_port)

    client_context=zmq.Context()
    client_socket=client_context.socket(zmq.REQ)
    client_socket.connect("tcp://localhost:%s" %client_port)

    #print ("Path List",path_list)
    PCEP_MSG = {}
    SR_ERO_LIST = []
    LSPA_Object = {"Hold_Priority":6,"Setup_Priority": 6,"FRR_Desired": 0}
    EndPointObject = {"Tunnel_Source":dboperations.Query_node_ip(path_list[0]),"Tunnel_Destination":dboperations.Query_node_ip(path_list[-1])}
    SR_TE=True

    for node in path_list:
        node_ip,node_sid = dboperations.Query_node_ip_sid(node)
        print (node,node_ip,node_sid)
        SR_ERO_LIST.append({node_ip:node_sid})
    try:
        Node_Tunnel_Tracker.head_ends[path_list[0]]
        tunnel_id= (next(Node_Tunnel_Tracker.head_ends[path_list[0]].gen_stat))
    except KeyError:
        Node_Tunnel_Tracker.create(path_list[0])
        Node_Tunnel_Tracker.head_ends[path_list[0]].gen_stat = Node_Tunnel_Tracker.head_ends[path_list[0]].tunnel_nu()
        tunnel_id= (next(Node_Tunnel_Tracker.head_ends[path_list[0]].gen_stat))
    except e:
        print ("Exception Occured %s" %str(e))

    TunnelName = 'auto'+'_'+path_list[0]+"_"+str(tunnel_id)

    print ("TunnelName",TunnelName)
    print ("ST_TE",SR_TE)
    print ("EndPointObject and SR TE",EndPointObject)
    print ("SR ERO",SR_ERO_LIST)
    print ("LSPA_OBJECT",LSPA_Object)

    PCEP_MSG['TunnelName'] = TunnelName
    PCEP_MSG['SR-TE'] = SR_TE
    PCEP_MSG['EndPointObject']=EndPointObject
    PCEP_MSG['LSPA_Object'] = LSPA_Object
    PCEP_MSG['SR_ERO_LIST']=SR_ERO_LIST

    print ("PCEP_MSG",PCEP_MSG)

    json_obj = json.dumps(PCEP_MSG)
    pobj_send = pickle.dumps(json_obj)
    pcep_main(pobj_send)


    '''
    self.client_socket.send(pobj_send)
    pobj_recv=self.client_socket.recv()
    print ("The Nodes are",pickle.loads(pobj_recv))
    '''



