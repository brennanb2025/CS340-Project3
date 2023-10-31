from simulator.node import Node
import json


class Link_State_Node(Node):
    def __init__(self, id):
        super().__init__(id)
        self.links = {} # (src, dest) ---> [cost, seq_num]
        self.routing_table = {} # dest node --> next_hop
        self.vertices = [self.id] # list of all vertices in network

    # Return a string
    def __str__(self):
        # l = 'links: ' + json.dumps(self.links) + '\n'
        # r = 'routing table: ' + json.dumps(self.routing_table) + '\n'
        # v = 'vertices: ' + json.dumps(self.vertices) + '\n'
        # return l + r + v
        return "replace with real string ouput"

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link


        seq = 0

        # potential issue if delete nonexistent node ########################################
        # delete link
        if latency == -1 and neighbor in self.neighbors:
            # print('node ' + str(neighbor) + ' deleted')
            # remove from neighbors
            self.neighbors.remove(neighbor)
            self.vertices.remove(neighbor)

            link = frozenset([self.id, neighbor])
            seq = self.links[link][1] + 1

            # remove from links dictionary (used by dijkstra's)
            keys = self.links.keys()  
            for k in list(keys):
                if neighbor in k:
                    self.links.pop(k)

        else:
            # print('new link')
            if neighbor not in self.vertices:
                self.vertices.append(neighbor)
                # print('new node added', self.vertices)


            if neighbor not in self.neighbors:
                self.neighbors.append(neighbor)

                if neighbor not in self.routing_table:
                    for link in self.links.keys():
                        help = list(link)
                        message = json.dumps({
                        "src": help[0],
                        "dst": help[1],
                        "cost": self.links[link][0],
                        "seq": self.links[link][1],
                        'sender': self.id
                        })
                        self.send_to_neighbor(neighbor, message)
                        # print('sent message from ' + str(self.id) + ' to ' + str(neighbor))

            link = frozenset([self.id, neighbor])
            if link in self.links:
                seq = self.links[link][1] + 1
            else:
                seq = 0
            
            self.links[frozenset([self.id, neighbor])] = [latency, seq]

        self.logging.debug('link update, neighbor %d, latency %d, time %d' % (neighbor, latency, self.get_time()))

        message = json.dumps({
            "src": self.id,
            "dst": neighbor,
            "cost": latency,
            "seq": seq,
            'sender': self.id
        })
        self.send_to_neighbors(message)
        # print('sent messages from ' + str(self.id))


        # REREUN DIJKSTRAS
        self.update_state()

    # Fill in this function
    def process_incoming_routing_message(self, m):
        # for now skipping added nodes case

        message = json.loads(m)

        src = message['src']
        dst = message['dst']
        cost = message['cost']
        new_seq = message['seq']
        sender = message['sender']
        message['sender'] = self.id
        
        link = frozenset([src, dst])
        # print('links', self.links)

        if link in self.links:
            old_seq = self.links[link][1]
        else:
            old_seq = -1

        if new_seq > old_seq:
            if src not in self.vertices:
                self.vertices.append(src)

            if dst not in self.vertices:
                self.vertices.append(dst)

            self.links[link] = [cost, new_seq]
            # REREUN DIJKSTRAS
            self.update_state()

            for n in self.neighbors:
                if n != message['sender']:
                    self.send_to_neighbor(n, json.dumps(message))
                    # print('sent message from ' + str(self.id) + ' to ' + str(n))


        elif new_seq < old_seq:
            message['cost'] = self.links[link][0]
            message['seq'] = old_seq
            self.send_to_neighbor(sender, json.dumps(message))
            # print('sent message from ' + str(self.id) + ' to ' + str(sender))


        

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.routing_table:
            curr = self.routing_table[destination]
            # print('curr:', curr)
            prev = destination
            while curr != self.id:
                prev = curr
                curr = self.routing_table[prev]

            # print('next step from node ' + str(self.id) + ': ' + str(prev))
            # print(self.routing_table)
            return prev
            
        else:
            return -1 # no path to destination
        

    def update_state(self):
        self.routing_table = self.dijkstra()
        # print('routing table', self.routing_table)


    def dijkstra(self):
        dist = {}
        prev = {}
        # print('routing table', self.routing_table)
        # print('links', self.links)

        for v in self.vertices:
            dist[v] = float('inf')
            prev[v] = None

        dist[self.id] = 0

        vert = self.vertices.copy()
        # print(vert)
        # print(dist)

        while len(vert) > 0:
            cur_min = float('inf')
            curr = None 
            for v in vert:
                if dist[v] < cur_min:
                    curr = v
                    cur_min = dist[v]

            # print('curr', curr)
            # print('prev', prev)
            if curr == None:
                return prev
            
            vert.remove(curr)
            # print(vert)
            # print(dist)

            neighbors = []
            for v in vert:
                if frozenset([curr, v]) in self.links:
                    neighbors.append(v)

            for n in neighbors:
                temp = dist[curr] + self.links[frozenset([curr, n])][0]
                if temp < dist[n]:
                    dist[n] = temp
                    prev[n] = curr

        return prev

            
