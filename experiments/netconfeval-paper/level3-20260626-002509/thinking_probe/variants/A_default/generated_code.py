from collections import defaultdict, deque

def compute_routing_paths(topology, requirements=None):
    # Build adjacency list: device -> list of neighbor devices
    adjacency = defaultdict(list)
    # Collect devices per LAN
    lan_devices = defaultdict(list)
    for device, ports in topology.items():
        for port, lan in ports.items():
            lan_devices[lan].append(device)
    # Add edges between devices sharing a LAN
    for lan, devices in lan_devices.items():
        for i in range(len(devices)):
            for j in range(i+1, len(devices)):
                d1, d2 = devices[i], devices[j]
                adjacency[d1].append(d2)
                adjacency[d2].append(d1)
    
    # Identify all hosts (names starting with 'h')
    hosts = [dev for dev in topology if dev.startswith('h')]
    hosts.sort()  # to ensure deterministic order
    
    # Compute shortest paths between all host pairs using BFS
    paths = {}
    for src in hosts:
        paths[src] = {}
        # BFS from src
        visited = {src}
        parent = {src: None}
        queue = deque([src])
        while queue:
            current = queue.popleft()
            for neighbor in adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = current
                    queue.append(neighbor)
        # Reconstruct paths to each other host
        for dst in hosts:
            if dst == src:
                continue
            if dst not in parent:
                continue  # unreachable, skip
            # Reconstruct path from src to dst
            path = []
            node = dst
            while node is not None:
                path.append(node)
                node = parent[node]
            path.reverse()
            # path includes src and dst and intermediate devices (all are hosts/switches)
            # No need to filter LANs as they are not in node list
            paths[src][dst] = path
    return paths