import json
import networkx as nx
import re
import dboperations
import zmq,pickle
from plain_dijkstra import Copy_all_shortest_paths_plain as Copy_all_shortest_paths_plain
from exclude_link_dijkstra import Copy_all_shortest_paths_exclude_link as Copy_all_shortest_paths_exclude_link
from bandwidth_constraint_dijkstra import Copy_all_shortest_paths_bwconstraint as Copy_all_shortest_paths_bwconstraint
from bwconstraint_excludelink_dijkstra import Copy_all_shortest_paths_bwconstraint_excludelink as Copy_all_shortest_paths_bwconstraint_excludelink
from avoid_node import Copy_all_shortest_paths_avoidnode as Copy_all_shortest_paths_avoidnode
from avoid_node_link_color import Copy_all_shortest_paths_avoidnode_linkcolor
from networkx.readwrite import json_graph
from networkx_viewer import Viewer

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

    def add_prefix_metric(self,prefix,metric):
        self.prefix_metric[prefix] = metric

    @classmethod
    def get_instance(cls):
        return cls._instance_track

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

'''
# Dont Need these Functions as we are going to store Attributes in SQLITE DB Which will avoid Iterating over the Graphs Everytime

def find_node_id(graph_nodes,node_name):
    for node_id,node_attr in graph_nodes.nodes_iter(data=True):
        if node_attr['name'] == node_name:
            node_id_a = node_id
    return (node_id_a)

def find_node_name(graph_nodes,node_id_tofind):
    for node_id,node_attr in graph_nodes.nodes_iter(data=True):
        if node_id == node_id_tofind:
            node_name = node_attr['name']
    return (node_name)
'''

def main():
    graph_nodes=parse_nodes('bgp_ls_all_topo.json')
    edge_dict = parse_links('bgp_ls_all_topo.json')
    for source,dest in edge_dict:
        graph_nodes.add_edge(source,dest,key=tuple((source,dest)),attr_dict=edge_dict[source,dest])

    dboperations.Create_initial_db(graph_nodes)
    node_name_a= 'por'
    node_name_b= 'san'
    avoid_node_name = 'sjc'
    color = 'blue'
    color_exc_inc = 'exclude'
    bw_constraint=12500
    avoid_node_id = dboperations.Query_node_id(avoid_node_name)
    path_list = spf(graph_nodes,dboperations.Query_node_id(node_name_a),dboperations.Query_node_id(node_name_b),'igp_metric',color=color,color_exc_inc=color_exc_inc,avoid_node=avoid_node_id)

    '''
    for p in path_list:
        print (p)
    #draw_graph(graph_nodes)
    #nx.write_gpickle(graph_nodes,"draw_graph.gpickle")

    '''
    server_port = "5559"
    server_context = zmq.Context()
    server_socket= server_context.socket(zmq.REP)
    server_socket.bind("tcp://*:%s" % server_port)

    while True:
        pickle_recv = server_socket.recv()
        server_message=pickle.loads(pickle_recv)
        print ("Server Recieved",server_message)
        extract_code=server_message.split(" ")

        if extract_code[0] == 'show_nodes':
            node_names = dboperations.Query_all_nodes()
            pobj=pickle.dumps(node_names,3)
            server_socket.send(pobj)

        if extract_code[0] == 'check_node':
            result = dboperations.Query_check_node(extract_code[1])
            pobj_send=pickle.dumps(result,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'run_spf':
            src_node = extract_code[1]
            dst_node = extract_code[2]
            path_list = spf(graph_nodes,dboperations.Query_node_id(src_node),dboperations.Query_node_id(dst_node),'igp_metric')
            pobj_send=pickle.dumps(path_list,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'run_spf_avoid_node':
            src_node = extract_code[1]
            dst_node = extract_code[2]
            avoid_node_name=extract_code[3]
            avoid_node_id = dboperations.Query_node_id(avoid_node_name)
            path_list = spf(graph_nodes,dboperations.Query_node_id(src_node),dboperations.Query_node_id(dst_node),'igp_metric',avoid_node=avoid_node_id)
            pobj_send=pickle.dumps(path_list,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'run_spf_avoid_node_color':
            src_node = extract_code[1]
            dst_node = extract_code[2]
            avoid_node_name=extract_code[3]
            color_exc_inc = extract_code[4]
            color = extract_code[5]
            avoid_node_id = dboperations.Query_node_id(avoid_node_name)
            path_list = spf(graph_nodes,dboperations.Query_node_id(src_node),dboperations.Query_node_id(dst_node),'igp_metric',color=color,color_exc_inc=color_exc_inc,avoid_node=avoid_node_id)
            pobj_send=pickle.dumps(path_list,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'run_spf_avoid_color':
            src_node = extract_code[1]
            dst_node = extract_code[2]
            color_exc_inc = extract_code[3]
            color = extract_code[4]
            path_list = spf(graph_nodes,dboperations.Query_node_id(src_node),dboperations.Query_node_id(dst_node),'igp_metric',color=color,color_exc_inc=color_exc_inc)
            pobj_send=pickle.dumps(path_list,3)
            server_socket.send(pobj_send)

        if extract_code[0] == 'push_path':
            print ("extract_code",extract_code[1:])
            status_code="Message Recieved"
            pobj_send=pickle.dumps(status_code,3)
            server_socket.send(pobj_send)



if __name__ == "__main__":
    main()