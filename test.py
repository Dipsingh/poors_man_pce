import math

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


def tunnel_handler(path_list):
    print (path_list[0])
    print (Node_Tunnel_Tracker.head_ends)
    try:
        Node_Tunnel_Tracker.head_ends[path_list[0]]
        print("Node Already Exists")
        print (Node_Tunnel_Tracker.head_ends[path_list[0]])
        print (next(Node_Tunnel_Tracker.head_ends[path_list[0]].gen_stat))
    except:
        print ("Creating a Tunnel",Node_Tunnel_Tracker.create(path_list[0]))
        Node_Tunnel_Tracker.head_ends[path_list[0]].gen_stat = Node_Tunnel_Tracker.head_ends[path_list[0]].tunnel_nu()
        print (next(Node_Tunnel_Tracker.head_ends[path_list[0]].gen_stat))

    print (Node_Tunnel_Tracker.head_ends)
    #Node_Tunnel_Tracker.head_ends[path_list[0]].gen_stat = Node_Tunnel_Tracker.head_ends[path_list[0]].tunnel_nu()
    #print ("Tunnel Number is ",next(tunnel_nu))


def main():

    path_list = ['por','sjc','san']
    path_list2 = ['por','san','chi','sjc']
    path_list3 = ['sjc','san','por']
    tunnel_handler(path_list)
    tunnel_handler(path_list2)
    tunnel_handler(path_list3)
    tunnel_handler(path_list)
    tunnel_handler(path_list2)







if __name__ == '__main__':
    main()