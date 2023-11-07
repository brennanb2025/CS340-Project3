from simulator.node import Node
import json
import copy


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.distance_vector = {} # destination vertex --> (cost of shortest path, [x, y, z])
        self.vertices = [] # list of all vertices in graph
        self.neighbor_dvs = {} # neighbor n --> [distance vector, time sent]
        self.cost = {} # neighbor n --> link cost
  
        self.distance_vector[self.id] = [0, []]


    # Return a string
    def __str__(self):
        i = 'node: ' + str(self.id) + '----------------------\n'
        r = 'distance vector: ' + str(self.distance_vector) + '\n'
        v = 'vertices: ' + str(self.vertices) + '\n'
        n = 'neighbors' + str(self.neighbors) + '\n'
        c = 'costs' + str(self.cost) + '\n'
        ndvs = 'neighbor dvs' + str(self.neighbor_dvs) + '\n'
        return i + r + v + n + c + ndvs
    
        # return "Rewrite this function to define your node dump printout"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link

        dv_copy = copy.deepcopy(self.distance_vector) # save to check for change later

        if latency == -1:
            # print('link deleted between', self.id, 'and', neighbor)
            self.neighbors.remove(neighbor)

            # self.distance_vector[neighbor] = [float('inf'), []]
            self.cost[neighbor] = float('inf')

            # set length of all paths in dv that used this link to inf bc link no longer exists so neither do those paths
            for k in self.distance_vector.keys():
                    if self.distance_vector[k][1] != [] and self.distance_vector[k][1][0] == neighbor:
                        self.distance_vector[k] = [float('inf'), []]

        else:

            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)
                # self.last_update[neighbor] = 0

                self.neighbor_dvs[neighbor] = [None, 0] # intialize so in table at least
                
                # should store None in neighbor_dvs and then check for this in bellman_ford

            if neighbor not in self.vertices:
                self.vertices.append(neighbor)

            
            if neighbor not in self.distance_vector:
                self.distance_vector[neighbor] = [latency, [neighbor]]

            self.distance_vector[neighbor] = [latency, [neighbor]]
            self.cost[neighbor] = latency


        # need to run bellman-ford here
        self.bellman_ford()

        if self.distance_vector != dv_copy:
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
        if sent_time >= self.neighbor_dvs[sender][1]:
            dv_copy = copy.deepcopy(self.distance_vector) # save to check for change later



            self.neighbor_dvs[sender] = [new_dv, sent_time]

            for k in new_dv.keys():
                if int(k) not in self.vertices:
                    self.vertices.append(int(k))

            self.bellman_ford()

            # if self.distance_vector was changed, send out to neighbors
            if self.distance_vector != dv_copy:
                # print('sending message to', self.neighbors, 'from', self.id)
                # print(str(self))
                message = json.dumps({
                'dv': self.distance_vector,
                'sender': self.id,
                'time': self.get_time()
                })


                if len(self.vertices) < 5:
                    self.send_to_neighbors(message)
                else:
                    for n in self.neighbors:
                        if n != sender:
                            self.send_to_neighbor(n, message)
                # self.send_to_neighbors(message)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.distance_vector and self.distance_vector[destination][0] != float('inf'):
            return self.distance_vector[destination][1][0] # returns first node in the shortest path stored in distance vector
        
        # no path to destination
        return -1
    

    def bellman_ford(self):

        # set all non-neighbors to inf and all neighbors to direct link cost
        for v in self.vertices:
            if v in self.neighbors:
                self.distance_vector[v] = [self.cost[v], [v]]
            else:
                self.distance_vector[v] = [float('inf'), []]
    

        for v in self.vertices:

            # if v not in self.distance_vector:
            #     self.distance_vector[v] = [float('inf'), []]

            if v == self.id:
                continue

            for n in self.neighbors:
  
                neighbor_dv = self.neighbor_dvs[n][0]

                if neighbor_dv == None or str(v) not in neighbor_dv:
                    continue

                # if no path from neighbor to destination or if no path from here to neighbor, don't bother
                if neighbor_dv[str(v)][0] == float('inf') or self.distance_vector[n][0] == float('inf'):
                    continue

                

                length_from_n = neighbor_dv[str(v)][0]
                length_to_n = self.distance_vector[n][0]
                length_through_n = length_from_n + length_to_n


                cur_shortest_length = self.distance_vector[v][0]


                if length_through_n <= cur_shortest_length:

                    path_to_n = self.distance_vector[n][1]
                    path_from_n =neighbor_dv[str(v)][1]
                    path_through_n = path_to_n + path_from_n

                    if self.id not in path_through_n:

                    
                        self.distance_vector[v] = [length_through_n, path_through_n]
