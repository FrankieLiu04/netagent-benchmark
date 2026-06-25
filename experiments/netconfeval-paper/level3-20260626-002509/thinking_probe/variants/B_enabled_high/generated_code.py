from collections import deque, defaultdict

def compute_routing_paths(topo, requirements=None):
    # Build graph from topology
    # Create LAN to device list mapping
    lan_to_devices = defaultdict(list)
    for device, ports in topo.items():
        for port, lan in ports.items():
            lan_to_devices[lan].append(device)
    
    # Build adjacency list for devices
    graph = defaultdict(set)
    for lan, devices in lan_to_devices.items():
        for i in range(len(devices)):
            for j in range(i+1, len(devices)):
                u = devices[i]
                v = devices[j]
                graph[u].add(v)
                graph[v].add(u)
    
    # Identify hosts (devices starting with 'h')
    hosts = [d for d in graph if d.startswith('h')]
    
    # For each host pair, find shortest path using BFS
    routing_paths = {}
    for src in hosts:
        routing_paths[src] = {}
        # BFS from src to all other nodes
        visited = {src: None}
        queue = deque([src])
        while queue:
            current = queue.popleft()
            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited[neighbor] = current
                    queue.append(neighbor)
        # For each other host, reconstruct path
        for dst in hosts:
            if dst == src:
                continue
            if dst in visited:
                # Reconstruct path from dst back to src
                path = []
                node = dst
                while node is not None:
                    path.append(node)
                    node = visited[node]
                path.reverse()
                routing_paths[src][dst] = path
    return routing_paths
