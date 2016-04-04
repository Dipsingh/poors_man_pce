import zmq
import networkx as nx
import json
from networkx_viewer import Viewer


port = "5556"

def draw_graph(graph_nodes):
    app=Viewer(graph_nodes)
    app.mainloop()

def main():
    context = zmq.Context()
    socket = context.socket(zmq.SUB)
    socket.connect("tcp://localhost:%s" % port)
    socket.setsockopt_string(zmq.SUBSCRIBE,"")
    '''
    graph_nodes = nx.read_gpickle("draw_graph.gpickle")
    draw_graph(graph_nodes)
    '''
    while True:
        string = socket.recv()
        graph_nodes=nx.read_gpickle(string)
        draw_graph(graph_nodes)


if __name__=="__main__":
    main()