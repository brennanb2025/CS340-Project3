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
        i = 'node: ' + str(self.id) + '----------------------\n'
        l = 'links: \n' + str(self.links).replace(', f', ', \nf') + '\n'
        r = 'routing table: ' + str(self.routing_table) + '\n'
        v = 'vertices: ' + str(self.vertices) + '\n'
        n = 'neighbors' + str(self.neighbors) + '\n'
        return i + l + r + v + n

    # Fill in this function
    def link_has_been_updated(self, neighbor, latency):
        # latency = -1 if delete a link

        seq = 0

        # delete link
        if latency == -1:
            # remove from neighbors
            self.neighbors.remove(neighbor)

            link = frozenset([self.id, neighbor])
            seq = self.links[link][1] + 1
 
            self.links[link] = [latency, seq]

        else:
            if neighbor not in self.vertices:
                self.vertices.append(neighbor)

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

        for n in self.neighbors:
            self.send_to_neighbor(n, message)

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


        elif new_seq < old_seq:
            message['cost'] = self.links[link][0]
            message['seq'] = old_seq
            self.send_to_neighbor(sender, json.dumps(message))

        

    # Return a neighbor, -1 if no path to destination
    def get_next_hop(self, destination):
        if destination in self.routing_table:
            curr = self.routing_table[destination]
            prev = destination
            while curr != self.id and curr != None:
                prev = curr
                curr = self.routing_table[prev]

            if curr == None:
                return -1
            
            return prev
            
        else:
            return -1 # no path to destination
        

    def update_state(self):
        prev = self.dijkstra()
        self.routing_table = prev
        

    def dijkstra(self):
        dist = {}
        prev = {}

        for v in self.vertices:
            dist[v] = float('inf')
            prev[v] = None

        dist[self.id] = 0

        vert = self.vertices.copy()

        while len(vert) > 0:
            cur_min = float('inf')
            curr = None 
            for v in vert:
                if dist[v] < cur_min:
                    curr = v
                    cur_min = dist[v]

            if curr == None:
                return prev
            
            vert.remove(curr)

            neighbors = []
  
            for v in vert:
                cur_link = frozenset([curr, v])

                # only consider pairs with cost != -1 (link exists)
                if cur_link in self.links and self.links[cur_link][0] != -1:
                    neighbors.append(v)

            for n in neighbors:
                temp = dist[curr] + self.links[frozenset([curr, n])][0]
                if temp < dist[n]:
                    dist[n] = temp
                    prev[n] = curr

        return prev

            
