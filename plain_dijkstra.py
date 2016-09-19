from heapq import heappush, heappop
from itertools import count
import networkx as nx


def Copy_all_shortest_paths_plain(G, source, target, weight=None):
    if weight is not None:
        pred,dist = copy_dijkstra_predecessor_and_distance(G,source,weight=weight)
    else:
        pred = nx.predecessor(G,source)
    if target not in pred:
        raise nx.NetworkXNoPath()
    stack = [[target,0]]
    top = 0
    while top >= 0:
        node,i = stack[top]
        if node == source:
            yield [p for p,n in reversed(stack[:top+1])]
        if len(pred[node]) > i:
            top += 1
            if top == len(stack):
                stack.append([pred[node][i],0])
            else:
                stack[top] = [pred[node][i],0]
        else:
            stack[top-1][1] += 1
            top -= 1

def copy_dijkstra_predecessor_and_distance(G, source, cutoff=None,weight='weight'):
    weight = copy_weight_function(G, weight)
    pred = {source: []}  # dictionary of predecessors
    return (pred, copy_dijkstra(G, source, weight, pred=pred, cutoff=cutoff))

def copy_weight_function(G, weight):
    if callable(weight):
        return weight
    # If the weight keyword argument is not callable, we assume it is a
    # string representing the edge attribute containing the weight of
    # the edge.
    if G.is_multigraph():
        return lambda u, v, d: min(attr.get(weight, 1) for attr in d.values())
    return lambda u, v, data: data.get(weight, 1)

def copy_dijkstra(G, source, weight, pred=None, paths=None, cutoff=None,target=None):
    G_succ = G.succ if G.is_directed() else G.adj
    push = heappush
    pop = heappop
    dist = {}  # dictionary of final distances
    seen = {source: 0}
    # fringe is heapq with 3-tuples (distance,c,node)
    # use the count c to avoid comparing nodes (may not be able to)
    c = count()
    fringe = []
    push(fringe, (0, next(c), source))

    while fringe:

        (d, _, v) = pop(fringe)

        if v in dist:
            continue  # already searched this node.
        dist[v] = d

        if v == target:
            break
        for u, e in G_succ[v].items():

            cost = weight(v, u, e)
            if cost is None:
                continue
            
            vu_dist = dist[v] + cost

            if cutoff is not None:
                if vu_dist > cutoff:
                    continue
            if u in dist:
                if vu_dist < dist[u]:
                    raise ValueError('Contradictory paths found:','negative weights?')

            elif u not in seen or vu_dist < seen[u]:
                seen[u] = vu_dist
                push(fringe, (vu_dist, next(c), u))

                if paths is not None:
                    paths[u] = paths[v] + [u]

                if pred is not None:
                    pred[u] = [v]

            elif vu_dist == seen[u]:
                if pred is not None:
                    pred[u].append(v)


    # The optional predecessor and path dictionaries can be accessed
    # by the caller via the pred and paths objects passed as arguments.
    return dist
