package com.frankliu.netagent.mcp;

import java.util.Map;

public record McpTool(
        String name,
        String description,
        Map<String, Object> inputSchema
) {
    public McpTool {
        inputSchema = inputSchema == null ? Map.of() : Map.copyOf(inputSchema);
    }
}
