from simulator.node import Node
import json
import copy


class Distance_Vector_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.distance_vector = {} # destination vertex --> (cost of shortest path, [x, y, z])
        self.vertices = [self.id] # list of all vertices in graph
        self.last_update = {} # neighbor n --> time last update sent

    # Return a string
    def __str__(self):
        return "Rewrite this function to define your node dump printout"

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

        self.distance_vector[neighbor] = [latency, [neighbor]]

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

        # ignore message if not the last sent from that node
        if sent_time >= self.last_update[sender]:
            changed_dv = self.bellman_ford(new_dv, sender)

            if changed_dv:
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

        for v in self.vertices:
            new_path_length = neighbor_dv[v] + self.distance_vector[neighbor_id]
            
            if new_path_length < self.distance_vector[v]:
                neighbor_path = copy.deepcopy(neighbor_dv[v][1])
                new_path = [neighbor_id] + neighbor_path
                self.distance_vector[v] = [new_path_length, new_path]
                changed = True

        return changed

