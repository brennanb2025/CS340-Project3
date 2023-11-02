from simulator.node import Node
import json
import copy


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.distance_vector = {} # destination vertex --> (cost of shortest path, [x, y, z])
        self.vertices = [] # list of all vertices in graph
        self.last_update = {} # neighbor n --> time last update sent
        self.neighbor_dvs = {} # neighbor n --> [distance vector, time sent]

        # will need to store neighbor's dvs bc need to recalculate bellman ford when link_has_been_updated too
        # bc when neighboring links change might change what the shortest path is


        # office hours questions
        # how to handle when a link's latency is increased (including when it's deleted)
        #       how do we handle the case of a link being deleted but still being used in other nonneighboring nodes' distance vectors?
        #       do we need to implement poisoned reverse?


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

            # self.distance_vector.pop(neighbor) # this might be an issue - come back
            # ^ I think we shouldn't do this bc what if still reachable through another node? not sure how to handle - I think make distance inf when deleted bc unreachable
            # how to handle existing shortest paths in self.distance_vector that used this link?
            # ^ set all paths in current self.dv that have that node as the next hop to inf -- will be updated when other nodes send responses
            self.distance_vector[neighbor] = [float('inf'), []]

            # self.last_update.pop(neighbor) # another potential issue
            # ^ not sure about this one, should potentially remove from the neighbor_dvs list? doesn't really matter bc will be gone from self.neighbors
            # just leave in for now

        else:

            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)
                # self.last_update[neighbor] = 0

                self.neighbor_dvs[neighbor] = [None, 0] # intialize so in table at least
                
                # should store None in neighbor_dvs and then check for this in bellman_ford

            if neighbor not in self.vertices:
                self.vertices.append(neighbor)

            # if latency is being increased
            # if neighbor in self.distance_vector and self.distance_vector[neighbor][0] < latency:
            #     self.distance_vector[neighbor] = [float('inf'), []] # probably won't work
            # else:
            # ^ broke path finding but seems like something like this has to happen, otherwise neighbor's paths won't be updated to reflect change
            
            self.distance_vector[neighbor] = [latency, [neighbor]]

        # need to run bellman-ford here
        self.bellman_ford()

        print('update about', neighbor, 'received at', self.id, '-----------------------------')
        print(str(self))

        message = json.dumps({
            'dv': self.distance_vector,
            'sender': self.id,
            'time': self.get_time()
        })
        self.send_to_neighbors(message)
        print('node', self.id, 'sent dv to all neighbors', self.neighbors)

        

    # Fill in this function
    def process_incoming_routing_message(self, m):

        # when receive new dv should first update list of all vertices and add them to self.distance_vector with length inf if not there yet

        message = json.loads(m)
        sent_time = message['time']
        sender = message['sender']
        new_dv = message['dv']

        # ignore message if not the most recent sent from that node
        if sent_time >= self.neighbor_dvs[sender][1]:
            print('message received at', self.id, 'from', sender, '-----------------------------')
            print('new_dv', new_dv)
            print(str(self))

            # self.last_update[sender] = sent_time

            self.neighbor_dvs[sender] = [new_dv, sent_time]

            for k in new_dv.keys():
                if int(k) not in self.vertices:
                    self.vertices.append(int(k))
            # ^ don't need, can handle in bellman ford function (loop by neighbor_dvs and then by nodes contained in them, if not in self.dv then add)

            changed_dv = self.bellman_ford()
            print('changed', changed_dv)
            print(str(self))

            # if self.distance_vector was changed, send out to neighbors
            if changed_dv:
                print(str(self))
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

        print(self.vertices)
        # print(neighbor_dv)
        # print('neighborid type', type(neighbor_id))

        # for v in self.vertices:
        #     # v = str(v) # this makes it loop infinitely
        #     if v in neighbor_dv:
        #         # print('making it here')
        #         # print(self.vertices)
        #         # print('self.id', self.id)
        #         # print('vertex', v)
        #         # print('neighbor path length', neighbor_dv[v][0])
        #         # print('link length', self.distance_vector[neighbor_id])

        #         new_path_length = neighbor_dv[v][0] + self.distance_vector[neighbor_id][0]
        #         neighbor_path = copy.deepcopy(neighbor_dv[v][1])

        #         if v not in self.distance_vector:
        #             print('v not in self.distance_vector')
        #             self.distance_vector[int(v)] = [new_path_length, [neighbor_id] + neighbor_path]
        #             changed = True
                
        #         elif new_path_length < self.distance_vector[v][0] and neighbor_id not in neighbor_path:
        #             print('new path')
        #             # deal with infinite looping issue
        #             if neighbor_id not in neighbor_path:
        #                 print('no loops')
        #                 new_path = [neighbor_id] + neighbor_path
        #                 self.distance_vector[int(v)] = [new_path_length, new_path]
        #                 changed = True


        # problems:
        # what if not every node knows about every other node? sometimes dv won't have a node in it rn
        # ^ how to fix this? or is it fine and just check that v is in neighbor_dv
        # what if v == n
        for v in self.vertices:
            # print('v', v)

            if v not in self.distance_vector:
                # print('here')
                self.distance_vector[v] = [float('inf'), []]

            for n in self.neighbors:
                # print('n', n)
                
                if n != v: # ? I think this will work
                    neighbor_dv = self.neighbor_dvs[n][0]

                    # print('neighbor_dv', neighbor_dv)
                    # if neighbor_dv != None and v in neighbor_dv:

                    if neighbor_dv == None or str(v) not in neighbor_dv:
                        length_through_n = float('inf')
                    else:
                        length_through_n = neighbor_dv[str(v)][0]

                    length_to_n = self.distance_vector[n][0]

                    

                    cur_shortest_length = self.distance_vector[v][0]

                    if length_through_n + length_to_n < cur_shortest_length:
                        path_through_n = copy.deepcopy(neighbor_dv[str(v)][1])
                        new_path = [n] + path_through_n

                        self.distance_vector[v] = [length_through_n + length_to_n, new_path]
                        
                        changed = True
                    
        return changed

