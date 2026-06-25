def compute_routing_paths(topology, requirements=None):
    import collections
    lan_to_devices = collections.defaultdict(set)
    for device, ports in topology.items():
        for port, lan in ports.items():
            lan_to_devices[lan].add(device)
    graph = collections.defaultdict(list)
    for lan, devices in lan_to_devices.items():
        dev_list = list(devices)
        for i in range(len(dev_list)):
            for j in range(i+1, len(dev_list)):
                d1 = dev_list[i]
                d2 = dev_list[j]
                graph[d1].append(d2)
                graph[d2].append(d1)
    hosts = [d for d in topology if d.startswith('h')]
    result = {}
    for src in hosts:
        result[src] = {}
        targets = {h for h in hosts if h != src}
        if not targets:
            continue
        visited = {src}
        queue = collections.deque([src])
        parent = {src: None}
        found = {}
        while queue and len(found) < len(targets):
            node = queue.popleft()
            if node in targets and node not in found:
                path = []
                cur = node
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                path.reverse()
                found[node] = path
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    parent[neighbor] = node
                    queue.append(neighbor)
        for dst, path in found.items():
            result[src][dst] = path
    return result