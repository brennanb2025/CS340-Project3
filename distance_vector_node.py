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
        # ^ need this bc shortest path in distance vector not necessarily the neighbor direct link

        # will need to store neighbor's dvs bc need to recalculate bellman ford when link_has_been_updated too
        # bc when neighboring links change might change what the shortest path is


        # office hours questions
        # how to handle when a link's latency is increased (including when it's deleted)
        #       how do we handle the case of a link being deleted but still being used in other nonneighboring nodes' distance vectors?
        #       do we need to implement poisoned reverse?


        # when receive new dv from another node (or just an update to this node's link)
        # if link latency has changed, need to update the length of all paths in own distance vector to represent accurate new length
        # BEFORE bellman ford is used --> routes might not be the shortest anymore, but they'll be updated by the algorithm to be accurate
        # just have to make sure info used in bellman for accurately represents the current state of the network

        self.distance_vector[self.id] = [0, []]


    # Return a string
    def __str__(self):
        i = 'node: ' + str(self.id) + '----------------------\n'
        r = 'distance vector: ' + str(self.distance_vector) + '\n'
        v = 'vertices: ' + str(self.vertices) + '\n'
        n = 'neighbors' + str(self.neighbors) + '\n'
        ndvs = 'neighbor dvs' + str(self.neighbor_dvs) + '\n'
        return i + r + v + n + ndvs
    
        # return "Rewrite this function to define your node dump printout"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link

        if latency == -1:
            # print('link deleted between', self.id, 'and', neighbor)
            self.neighbors.remove(neighbor)

            self.distance_vector[neighbor] = [float('inf'), []]
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

            
            old_latency = self.distance_vector[neighbor][0]
            path_length_change = latency - old_latency # amount to add to all paths that use this link
            # print('path length change', path_length_change)
            # print('latency', latency)
            # print('old latency', old_latency)
            # print('costs', self.cost)
            # print('dv', self.distance_vector)

            self.distance_vector[neighbor] = [latency, [neighbor]]
            self.cost[neighbor] = latency

            for k in self.distance_vector.keys():
                if k != neighbor:
                    if self.distance_vector[k][1] != [] and self.distance_vector[k][1][0] == neighbor:
                        old_length = self.distance_vector[k][0]
                        self.distance_vector[k][0] = old_length + path_length_change
            

        # need to run bellman-ford here
        self.bellman_ford()

        # print('update about', neighbor, 'received at', self.id, '-----------------------------')
        # print(str(self))

        message = json.dumps({
            'dv': self.distance_vector,
            'sender': self.id,
            'time': self.get_time()
        })
        self.send_to_neighbors(message)
        # print('node', self.id, 'sent dv to all neighbors', self.neighbors)

        

    # Fill in this function
    def process_incoming_routing_message(self, m):

        message = json.loads(m)
        sent_time = message['time']
        sender = message['sender']
        new_dv = message['dv']

        # ignore message if not the most recent sent from that node
        if sent_time >= self.neighbor_dvs[sender][1]:
            # print('message received at', self.id, 'from', sender, '-----------------------------')
            # print('new_dv', new_dv)
            # print(str(self))


            self.neighbor_dvs[sender] = [new_dv, sent_time]

            for k in new_dv.keys():
                if int(k) not in self.vertices:
                    self.vertices.append(int(k))

            changed_dv = False

            # go through and update all lengths to be accurate using newly received dv
            # all routes where next hop is the node that just sent the new dv need to be recalculated using cost[that node] + new_dv[that dest]
            for k in self.distance_vector.keys():
                if str(k) in new_dv and self.distance_vector[k][1] != [] and self.distance_vector[k][1][0] == sender:
                    if self.id in new_dv[str(k)][1]:
                        self.distance_vector[k] = [float('inf'), []]
                        changed_dv = True
                        continue


                    previous_length = self.distance_vector[k][0]
                    # print(new_dv[str(k)][0])
                    # print(self.cost[sender])

                    new_length = new_dv[str(k)][0] + self.cost[sender]

                    
                    
                    if new_length != previous_length:
                        changed_dv = True
                        self.distance_vector[k][0] = new_length

                        if new_length == float('inf'):
                            self.distance_vector[k][1] = []

            # print('updated self.dv', self.distance_vector)

            bellman_ford_changed = self.bellman_ford()
            # changed_dv = self.bellman_ford_single(new_dv, sender)


            # print('changed', changed_dv)
            # print('bellman ford changed', bellman_ford_changed)
            # print(str(self))

            # if self.distance_vector was changed, send out to neighbors
            if bellman_ford_changed:
                # print('sending message to', self.neighbors, 'from', self.id)
                # print(str(self))
                message = json.dumps({
                'dv': self.distance_vector,
                'sender': self.id,
                'time': self.get_time()
                })
                self.send_to_neighbors(message)

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.distance_vector and self.distance_vector[destination][0] != float('inf'):
            return self.distance_vector[destination][1][0] # returns first node in the shortest path stored in distance vector
        
        # no path to destination
        return -1
    

    def bellman_ford(self):
        changed = False

        # print(self.vertices)


        # problems:
        # what if not every node knows about every other node? sometimes dv won't have a node in it rn
        # ^ how to fix this? or is it fine and just check that v is in neighbor_dv
        # what if v == n
        for v in self.vertices:
            # print('v', v)

            if v not in self.distance_vector:
                # print('here')
                self.distance_vector[v] = [float('inf'), []]

            if v == self.id:
                continue

            for n in self.neighbors:
                # print('n', n)
                
            
                neighbor_dv = self.neighbor_dvs[n][0]
                # print('neighbor', n, 'dv', neighbor_dv)

                # print('neighbor_dv', neighbor_dv)
                # if neighbor_dv != None and v in neighbor_dv:

                if neighbor_dv == None or str(v) not in neighbor_dv:
                    length_through_n = float('inf')
                else:
                    length_through_n = neighbor_dv[str(v)][0]

                # print('node', self.id, 'cost of direct link to', n, ':', self.cost[n])
                # print('node', self.id, 'shortest path to ', n, ':', self.distance_vector[n])
                # if self.cost[n] < self.distance_vector[n][0]:
                #     print('not the same -------------------------------------------------------')


                if self.distance_vector[n][0] == float('inf'):    
                    self.distance_vector[n] = [self.cost[n], [n]]
                    changed = True

                # if self.cost[n] <= self.distance_vector[n][0]:
                #     length_to_n = self.cost[n]
                #     path_to_n = [n]
                # else:
                #     length_to_n = self.distance_vector[n][0] ### seems like it should be this bc what if direct link isn't shortest path to neighbor?
                #     path_to_n = self.distance_vector[n][1]

                length_to_n = self.distance_vector[n][0]
                path_to_n = self.distance_vector[n][1]

                cur_shortest_length = self.distance_vector[v][0]

                if length_through_n + length_to_n < cur_shortest_length:
                    path_through_n = copy.deepcopy(neighbor_dv[str(v)][1])

                    if self.id not in path_through_n:
                        # new_path = [n] + path_through_n
                        new_path = path_to_n + path_through_n

                        # print('path through n', n, path_through_n)

                        self.distance_vector[v] = [length_through_n + length_to_n, new_path]
                        # print('after change:', self.distance_vector)
                        
                        changed = True
                
        return changed