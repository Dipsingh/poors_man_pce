import networkx as nx
import csv

def main():
    G=nx.MultiDiGraph()
    '''
    for i in range(1,200):
        G.add_edge(i,i+1,weight=10)
        G.add_edge(i,i+2,weight=10)
    #G1=nx.fast_gnp_random_graph(200,10)
    #G2= nx.barabasi_albert_graph(200,2)

    '''
    with open('synth200_unary_hard.graph.txt','r') as csvfile:
        reader = csv.reader(csvfile,delimiter= ' ')
        for row in reader:
            label= row[0]
            src_node = row[1]
            dst_node = row[2]
            cost = int(row[3])
            G.add_edge(src_node,dst_node,weight=cost)

    path_list = nx.all_shortest_paths(G,source='1',target='199',weight='weight')
    if path_list:
        for p in path_list:
            print ("Paths are",p)




if __name__ == "__main__":
    main()