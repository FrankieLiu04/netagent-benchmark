package com.frankliu.netagent.mcp;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class ScriptedMcpClient implements CmlMcpClient {

    private final Map<String, String> results;
    private final List<McpTool> tools;

    public ScriptedMcpClient(Map<String, String> results) {
        this(results, List.of());
    }

    public ScriptedMcpClient(Map<String, String> results, List<McpTool> tools) {
        this.results = new LinkedHashMap<>(results);
        this.tools = List.copyOf(tools);
    }

    @Override
    public List<McpTool> listTools() {
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
