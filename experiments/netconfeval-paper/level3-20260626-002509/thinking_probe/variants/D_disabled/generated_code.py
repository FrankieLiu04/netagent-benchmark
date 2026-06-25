def compute_routing_paths(topo, requirements=None):
    import itertools
    from collections import defaultdict

    # Build adjacency list: device -> list of (neighbor_device, port)
    adj = defaultdict(list)
    # Also track hosts
    hosts = set()
    devices = set()

    # First, identify all devices and hosts
    for device, ports in topo.items():
        devices.add(device)
        if device.startswith('h'):
            hosts.add(device)

    # For each LAN, we need to find all devices connected to it
    lan_to_devices = defaultdict(list)
    for device, ports in topo.items():
        for port, lan in ports.items():
            lan_to_devices[lan].append(device)

    # Build adjacency links
    for lan, devs in lan_to_devices.items():
        # All devices on the same LAN are connected to each other
        for d1, d2 in itertools.combinations(devs, 2):
            adj[d1].append(d2)
            adj[d2].append(d1)
        # If a LAN has only one device, it's an endpoint, but we still need to consider self? Not needed.

    # Find all pairs of hosts
    host_pairs = list(itertools.combinations(hosts, 2))

    # BFS to find shortest path between two nodes
    def bfs_shortest_path(start, end):
        visited = {start}
        queue = [[start]]
        while queue:
            path = queue.pop(0)
            node = path[-1]
            if node == end:
                return path
            for neighbour in adj[node]:
                if neighbour not in visited:
                    visited.add(neighbour)
                    new_path = list(path)
                    new_path.append(neighbour)
                    queue.append(new_path)
        return None

    # Build result dictionary
    result = {}
    for host in hosts:
        result[host] = {}

    for h1, h2 in host_pairs:
        path = bfs_shortest_path(h1, h2)
        if path:
            result[h1][h2] = path
            result[h2][h1] = list(reversed(path))
        else:
            # No path - may not happen in connected network
            result[h1][h2] = []
            result[h2][h1] = []

    # Convert to dict of dicts as required (already)
    return dict(result)