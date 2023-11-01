from simulator.node import Node
import json
import copy


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.distance_vector = {} # destination vertex --> (cost of shortest path, [x, y, z])
        self.vertices = [] # list of all vertices in graph
        self.last_update = {} # neighbor n --> time last update sent


    # Return a string
    def __str__(self):
        i = 'node: ' + str(self.id) + '----------------------\n'
        r = 'distance vector: ' + str(self.distance_vector) + '\n'
        v = 'vertices: ' + str(self.vertices) + '\n'
        n = 'neighbors' + str(self.neighbors) + '\n'
        return i + r + v + n
    
        # return "Rewrite this function to define your node dump printout"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link

        if latency == -1:
            self.neighbors.remove(neighbor)
            self.distance_vector.pop(neighbor) # this might be an issue - come back
            self.last_update.pop(neighbor) # another potential issue

        if neighbor not in self.neighbors:
            self.neighbors.append(neighbor)
            self.last_update[neighbor] = 0

        if neighbor not in self.vertices:
            self.vertices.append(neighbor)

        self.distance_vector[neighbor] = [latency, [neighbor]]

        print('update about', neighbor, 'received at', self.id)
        print(str(self))

        message = json.dumps({
            'dv': self.distance_vector,
            'sender': self.id,
            'time': self.get_time()
        })
        self.send_to_neighbors(message)

        

    # Fill in this function
    def process_incoming_routing_message(self, m):

        message = json.loads(m)
        sent_time = message['time']
        sender = message['sender']
        new_dv = message['dv']

        # ignore message if not the most recent sent from that node
        if sent_time >= self.last_update[sender]:
            print('message received at', self.id, 'from', sender)
            print(str(self))

            self.last_update[sender] = sent_time

            for k in new_dv.keys():
                if int(k) not in self.vertices:
                    self.vertices.append(int(k))

            changed_dv = self.bellman_ford(new_dv, sender)
            print('changed', changed_dv)
            print(str(self))

            if changed_dv:
                print(str(self))
                message = json.dumps({
                'dv': self.distance_vector,
                'sender': self.id,
                'time': self.get_time()
                })
                self.send_to_neighbors(message)

        # if time of incoming message < self.last_update[sender]
        #   ignore, not most recent info
        # else
        #   run bellman ford with new info
        #   send this node's updated distance vector


    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.distance_vector:
            return self.distance_vector[destination][1][0] # returns first node in the shortest path stored in distance vector
        
        # no path to destination
        return -1
    

    def bellman_ford(self, neighbor_dv, neighbor_id):
        changed = False

        print(self.vertices)
        print(neighbor_dv)
        # print('neighborid type', type(neighbor_id))

        for v in self.vertices:
            # v = str(v) # this makes it loop infinitely
            if v in neighbor_dv:
                # print('making it here')
                # print(self.vertices)
                # print('self.id', self.id)
                # print('vertex', v)
                # print('neighbor path length', neighbor_dv[v][0])
                # print('link length', self.distance_vector[neighbor_id])

                new_path_length = neighbor_dv[v][0] + self.distance_vector[neighbor_id][0]
                neighbor_path = copy.deepcopy(neighbor_dv[v][1])

                if v not in self.distance_vector:
                    print('v not in self.distance_vector')
                    self.distance_vector[int(v)] = [new_path_length, [neighbor_id] + neighbor_path]
                    changed = True
                
                elif new_path_length < self.distance_vector[v][0] and neighbor_id not in neighbor_path:
                    print('new path')
                    # deal with infinite looping issue
                    if neighbor_id not in neighbor_path:
                        print('no loops')
                        new_path = [neighbor_id] + neighbor_path
                        self.distance_vector[int(v)] = [new_path_length, new_path]
                        changed = True

        return changed

