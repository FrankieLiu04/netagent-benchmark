from collections import defaultdict, deque
from typing import Dict, List, Optional

def compute_routing_paths(topology: Dict[str, Dict[int, str]], network_requirements: Optional[None] = None) -> Dict[str, Dict[str, List[str]]]:
    # Build graph: adjacency list of devices (nodes) connected via LANs
    # First, group devices by LAN
    lan_to_devices = defaultdict(list)
    for device, ports in topology.items():
        for port, lan in ports.items():
            lan_to_devices[lan].append(device)

    # Build adjacency: for each LAN, connect all devices in that LAN (fully connected)
    adj = defaultdict(set)
    for lan, devices in lan_to_devices.items():
        for i in range(len(devices)):
            for j in range(i+1, len(devices)):
                d1 = devices[i]
                d2 = devices[j]
                adj[d1].add(d2)
                adj[d2].add(d1)

    # Identify hosts (names starting with 'h')
    hosts = [device for device in topology if device.startswith('h')]

    # For each host, compute shortest paths to all other hosts using BFS
    paths_dict = {}
    for src in hosts:
        # BFS from src to all other nodes
        visited = {src}
        queue = deque([(src, [src])])
        paths = {}
        while queue:
            current, path = queue.popleft()
            if current.startswith('h') and current != src:
                paths[current] = path
            for neighbor in adj[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append((neighbor, path + [neighbor]))
        if paths:
            paths_dict[src] = paths

    return paths_dict
