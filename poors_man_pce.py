import json,math
import networkx as nx
import re,threading,requests
import dboperations,httplib2
import zmq,pickle,functions_dict
from networkx.readwrite import json_graph
#from networkx_viewer import Viewer
from pcep.pce_controller import *
import message_broker


def extract_routerid(str):
    rg = re.compile("router=(.*)",re.IGNORECASE|re.DOTALL)
    m=rg.search(str)
    if m:
        router_id = m.group(1)
        return (router_id)
    return ("Nil")

def extract_isis_level(str):
    unicode_strlist = str.split("/")
    strlist = [x.encode('UTF8') for x in unicode_strlist ]
    rg = re.compile(".*(IsisLevel).*",re.IGNORECASE|re.DOTALL)
    isis_level_list = filter(rg.match , strlist)
    isis_level_string = isis_level_list[0]
    isis_level_list = isis_level_string.split(":")
    isis_level= isis_level_list[0]
    return isis_level

class Node(object):
    _instance_track = []
    def __init__(self,node_name,iso_system_id,router_id):
        self.node_name = node_name
        self.iso_system_id = iso_system_id
        self.router_id = router_id
        self.prefix_metric = {}
        self._instance_track.append(self)
        self.label_base = None
        self.label_range = None
        self.node_sid = None

    def add_prefix_metric(self,prefix,metric):
        self.prefix_metric[prefix] = metric
    @classmethod
    def get_instance(cls):
        return cls._instance_track

class ThreadingPCEPFunction(object):
    """ This class Daemonize the thread
    """
    def __init__(self,interval=1):
        self.interval =  interval
        thread=threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            pcep_main()

class ThreadingBrokerFunction(object):
    """ This class Daemonize the thread
    """
    def __init__(self,interval=1):
        self.interval =  interval
        thread=threading.Thread(target=self.run)
        thread.daemon = True
        thread.start()

    def run(self):
        while True:
            message_broker.broker_main()

'''
def parse_links(bgpls_config_file):
    with open(bgpls_config_file) as data_file:
        data= json.load(data_file)
    edge_dict = {}
    attr_dict = {}
    for key in data['network-topology']['topology']:
        if key['topology-id'] == 'example-linkstate-topology':
            for link in key['link']:
                if link['source']['source-node']:
                    src_node=extract_routerid(link['source']['source-node'])
                if link['destination']['dest-node']:
                    dest_node=extract_routerid(link['destination']['dest-node'])
                if link['l3-unicast-igp-topology:igp-link-attributes']['isis-topology:isis-link-attributes']['ted']:
                    max_link_bandwidth = link['l3-unicast-igp-topology:igp-link-attributes']['isis-topology:isis-link-attributes']['ted']['max-link-bandwidth']
                    for priority in link['l3-unicast-igp-topology:igp-link-attributes']['isis-topology:isis-link-attributes']['ted']['unreserved-bandwidth'] :
                        if priority['priority'] == 0:
                            unreserved_bw=priority['bandwidth']
                if link['l3-unicast-igp-topology:igp-link-attributes']['isis-topology:isis-link-attributes']['ted']['te-default-metric']:
                    te_metric = link['l3-unicast-igp-topology:igp-link-attributes']['isis-topology:isis-link-attributes']['ted']['te-default-metric']
                if link['l3-unicast-igp-topology:igp-link-attributes']['isis-topology:isis-link-attributes']['ted']['color']:
                    color = str(link['l3-unicast-igp-topology:igp-link-attributes']['isis-topology:isis-link-attributes']['ted']['color'])
                    color = 1
                if link['l3-unicast-igp-topology:igp-link-attributes']['metric']:
                    igp_metric = link['l3-unicast-igp-topology:igp-link-attributes']['metric']
                attr_dict['max_link_bandwidth'] = max_link_bandwidth
                attr_dict['unreserved_bw'] = unreserved_bw
                attr_dict['te_metric'] = te_metric
                attr_dict['color'] = link['l3-unicast-igp-topology:igp-link-attributes']['isis-topology:isis-link-attributes']['ted']['color']
                attr_dict['igp_metric'] = igp_metric
                edge_dict[src_node,dest_node] = dict(attr_dict)

    return (edge_dict)

def parse_nodes(bgpls_config_file):
    with open(bgpls_config_file) as data_file:
        data= json.load(data_file)
    G=nx.MultiDiGraph()
    for key in data['network-topology']['topology']:
        if key['topology-id'] == 'example-linkstate-topology':
            for node in key['node']:
                try:
                    if node['l3-unicast-igp-topology:igp-node-attributes']['isis-topology:isis-node-attributes']['ted']['te-router-id-ipv4']:
                        router_id = node['l3-unicast-igp-topology:igp-node-attributes']['isis-topology:isis-node-attributes']['ted']['te-router-id-ipv4']
                    if node['l3-unicast-igp-topology:igp-node-attributes']['isis-topology:isis-node-attributes']['iso']["iso-system-id"]:
                        iso_id = node['l3-unicast-igp-topology:igp-node-attributes']['isis-topology:isis-node-attributes']['iso']["iso-system-id"]
                    if node['l3-unicast-igp-topology:igp-node-attributes']['name']:
                        name= node['l3-unicast-igp-topology:igp-node-attributes']['name']
                    node_instance = Node(name,iso_id,router_id)
                    for p in node['l3-unicast-igp-topology:igp-node-attributes']['prefix']:
                        node_instance.add_prefix_metric(str(p['prefix']),str(p['metric']))
                    G.add_node(node_instance.iso_system_id)
                    G.node[node_instance.iso_system_id]['router_id'] = node_instance.router_id
                    G.node[node_instance.iso_system_id]['iso_id'] = node_instance.iso_system_id
                    G.node[node_instance.iso_system_id]['prefix_metric'] = node_instance.prefix_metric
                    G.node[node_instance.iso_system_id]['name'] = node_instance.node_name
                except:
                    print("Error Occured")
    return (G)
'''

def parse_nodes(json_message):
    G=nx.MultiDiGraph()
    for key in json_message:
        if key['paths']:
            for attr in key['paths']:
                if attr['nlri']['nlritype'] == "node":
                    iso_id = attr['nlri']['nodeid']
                    for pathattr in attr['attrs']:
                        if pathattr['type'] == 29:
                            for node_attr in pathattr['LSAttributeValue']:
                                if node_attr['type'] == 1026:
                                    name=node_attr['NodeName']
                                if node_attr['type'] == 1028:
                                    router_id = node_attr['value']
                                if node_attr['type'] == 1034:
                                    #BASE+RANGE
                                    label_range = node_attr['labelRange']
                                    for labelbase in node_attr['labelstart']:
                                        label_base = labelbase['label']
                    node_instance = Node(name,iso_id,router_id)
                    if label_base != None and label_range != None:
                        node_instance.label_range = label_range
                        node_instance.label_base = label_base

    for key in json_message:
        if key['paths']:
            for attr in key['paths']:
                if attr['nlri']['nlritype'] == "prefix":
                    for pathattr in attr['attrs']:
                        if pathattr['type'] == 14:
                            for item in pathattr['value']:
                                prefix_len = item['prefix']+"/"+str(item['prefixlen'])
                                for node in Node.get_instance():
                                    if node.iso_system_id == item['nodeid']:
                                        node.add_prefix_metric(prefix_len,str(0))
    for key in json_message:
        if key['paths']:
            for attr in key['paths']:
                if attr['nlri']['nlritype'] == 'prefix':
                    for node in Node.get_instance():
                        if node.iso_system_id == attr['nlri']['nodeid']:
                            for patthattr in attr['attrs']:
                                if patthattr['type'] == 29:
                                    for lsattr in patthattr['LSAttributeValue']:
                                        if lsattr['type'] == 1158:
                                            node.node_sid =lsattr['prefixsid']

    for node in Node.get_instance():
        G.add_node(node.iso_system_id)
        G.node[node.iso_system_id]['router_id'] = node.router_id
        G.node[node.iso_system_id]['iso_id'] = node.iso_system_id
        G.node[node.iso_system_id]['prefix_metric'] = node.prefix_metric
        G.node[node.iso_system_id]['name'] = node.node_name
        G.node[node.iso_system_id] ['labelrange'] = node.label_range
        G.node[node.iso_system_id] ['labelbase'] = node.label_base
        G.node[node.iso_system_id] ['nodesid'] = node.node_sid

    return (G)

def parse_links(json_message):
    edge_dict = {}
    attr_dict = {}
    for key in json_message:
        if key['paths']:
            for attr in key['paths']:
                if attr['nlri']['nlritype'] == "link":
                    source_node = attr['nlri']['localnode']
                    dest_node = attr['nlri']['remotenode']
                    local_ip = attr['nlri']['localip']
                    remote_ip = attr['nlri']['remoteip']
                    attr_dict ['local_ip'] = local_ip
                    attr_dict ['remote_ip'] = remote_ip
                    for item in attr['attrs']:
                        if item['type'] == 29:
                            for pathattr in item['LSAttributeValue']:
                                if pathattr['type']== 1028:
                                    source_router_id = pathattr['value']
                                    attr_dict['source_router_id'] = source_router_id
                                if pathattr['type']== 1030:
                                    dest_router_id = pathattr['value']
                                    attr_dict['dest_router_id'] = dest_router_id
                                if pathattr['type']== 1089:
                                    max_link_bandwidth = pathattr['MaxLinkBW']
                                    attr_dict['max_link_bandwidth'] = max_link_bandwidth
                                if pathattr['type']== 1092:
                                    te_metric = pathattr['value']
                                    attr_dict['te_metric'] = te_metric
                                if pathattr['type']== 1095:
                                    igp_metric = pathattr['value']
                                    attr_dict['igp_metric'] = igp_metric
                                if pathattr['type']== 1091:
                                    unreserved_bw = pathattr['UnresvBW']['0']
                                    attr_dict['unreserved_bw'] = unreserved_bw
                                if pathattr['type']== 1099:
                                    if pathattr['AdjSidFlags'] == 48:
                                        adj_sid_label = pathattr['AdjLabel']
                                        attr_dict['adj_sid_label']=adj_sid_label
                                if pathattr['type']== 1088:
                                    color = "white"
                                    attr_dict['color'] = color
                                edge_dict[source_node,dest_node] = dict(attr_dict)
    return (edge_dict)

def save_to_jsonfile(filename,graph):
    g= graph
    g_json=json_graph.node_link_data(g)
    json.dump(g_json,open(filename,'w'),indent=4)

def apply_styles(graph, styles):
    graph.graph_attr.update(
        ('graph' in styles and styles['graph']) or {}
    )
    graph.node_attr.update(
        ('nodes' in styles and styles['nodes']) or {}
    )
    graph.edge_attr.update(
        ('edges' in styles and styles['edges']) or {}
    )
    return graph

def add_nodes(graph,graph_nodes):
    for s,d in graph_nodes.nodes_iter(data=True):
        graph.node(s)
    return (graph)

def add_edges(graph,graph_nodes):
    for s,t,k,d in graph_nodes.edges_iter(keys=True,data=True):
        graph.edge(s,t)
    return (graph)

def draw_graph(graph_nodes):
    app=Viewer(graph_nodes)
    app.mainloop()

def main():
    func_dict = dict()
    context = zmq.Context()
    socket = context.socket(zmq.REQ)
    socket.connect("tcp://localhost:9999")
    neighbor="SendTopology:172.16.2.10"
    socket.send_string(neighbor)
    json_message = socket.recv_json()

    print("JSON Message",type(json_message))

    graph_nodes=parse_nodes(json_message)
    edge_dict = parse_links(json_message)

    #graph_nodes=parse_nodes('bgp_ls_topo_data.json')
    #edge_dict = parse_links('bgp_ls_topo_data.json')

    for source,dest in edge_dict:
        graph_nodes.add_edge(source,dest,key=tuple((source,dest)),attr_dict=edge_dict[source,dest])

    dboperations.Create_initial_db(graph_nodes)

    pcep_start = ThreadingPCEPFunction()
    broker_start = ThreadingBrokerFunction()

    #draw_graph(graph_nodes)
    #nx.write_gpickle(graph_nodes,"draw_graph.gpickle")
    '''
    node_name_a= 'por'
    node_name_b= 'san'
    avoid_node_name = 'sjc'
    color = 'blue'
    color_exc_inc = 'exclude'
    bw_constraint=12500
    avoid_node_id = dboperations.Query_node_id(avoid_node_name)
    #path_list = spf(graph_nodes,dboperations.Query_node_id(node_name_a),dboperations.Query_node_id(node_name_b),'igp_metric',color=color,color_exc_inc=color_exc_inc,avoid_node=avoid_node_id)

    for p in path_list:
        print (p)
    #draw_graph(graph_nodes)
    #nx.write_gpickle(graph_nodes,"draw_graph.gpickle")
    '''

    server_port = "5559"
    server_context = zmq.Context()
    server_socket= server_context.socket(zmq.REP)
    server_socket.bind("tcp://*:%s" % server_port)
    func_dict['show_nodes'] = functions_dict.show_nodes
    func_dict['check_node'] = functions_dict.check_nodes
    func_dict['run_spf'] = functions_dict.run_spf
    func_dict['run_spf_avoid_node'] = functions_dict.run_spf_avoid_node
    func_dict['run_spf_avoid_node_color'] = functions_dict.run_spf_avoid_node_color
    func_dict['run_spf_avoid_color'] = functions_dict.run_spf_avoid_color
    func_dict['push_path'] = functions_dict.pcep_interface
    print ("Starting PCEP")


    while True:
        pickle_recv = server_socket.recv()
        server_message=pickle.loads(pickle_recv)
        print ("Server Recieved",server_message)
        extract_code=server_message.split(" ")

        if extract_code[0] == 'show_nodes':
            node_names = func_dict['show_nodes']()
            pobj=pickle.dumps(node_names,3)
            server_socket.send(pobj)

        if extract_code[0] == 'check_node':
            result = func_dict['check_node'](extract_code[1])
            pobj_send=pickle.dumps(result,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'run_spf':
            path_list = func_dict['run_spf'](graph_nodes,extract_code[1],extract_code[2],metric='igp_metric')
            pobj_send=pickle.dumps(path_list,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'run_spf_avoid_node':
            path_list = func_dict['run_spf_avoid_node'](graph_nodes,extract_code[1],extract_code[2],extract_code[3],metric='igp_metric')
            pobj_send=pickle.dumps(path_list,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'run_spf_avoid_node_color':
            path_list = func_dict['run_spf_avoid_node_color'](graph_nodes,extract_code[1],extract_code[2],extract_code[3],extract_code[4],extract_code[5],metric='igp_metric')
            pobj_send=pickle.dumps(path_list,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'run_spf_avoid_color':
            path_list = func_dict['run_spf_avoid_color'](graph_nodes,extract_code[1],extract_code[2],extract_code[3],extract_code[4],metric='igp_metric')
            pobj_send=pickle.dumps(path_list,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'push_path':
            sr_te=extract_code[1]
            path_list = extract_code[2:]
            func_dict['push_path'](path_list,graph_nodes,sr_te)
            status_code="Message Recieved"
            pobj_send=pickle.dumps(status_code,3)
            server_socket.send(pobj_send)


if __name__ == "__main__":
    main()