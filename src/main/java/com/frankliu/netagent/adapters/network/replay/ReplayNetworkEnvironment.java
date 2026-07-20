package com.frankliu.netagent.adapters.network.replay;

import com.frankliu.netagent.ports.network.NetworkEnvironment;
import com.frankliu.netagent.ports.network.NetworkTool;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class ReplayNetworkEnvironment implements NetworkEnvironment {

    private final Map<String, String> results;
    private final List<NetworkTool> tools;

    public ReplayNetworkEnvironment(Map<String, String> results) {
        this(results, List.of());
    }

    public ReplayNetworkEnvironment(Map<String, String> results, List<NetworkTool> tools) {
        this.results = new LinkedHashMap<>(results);
        this.tools = List.copyOf(tools);
    }

    @Override
    public List<NetworkTool> listTools() {
        return tools;
    }

    @Override
    public String callTool(String name, Map<String, Object> arguments) {
        if (!results.containsKey(name)) {
            throw new IllegalArgumentException("No scripted MCP result for tool: " + name);
        }
        return results.get(name);
    }
}
