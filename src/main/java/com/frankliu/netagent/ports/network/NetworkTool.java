package com.frankliu.netagent.ports.network;

import java.util.Map;

public record NetworkTool(
        String name,
        String description,
        Map<String, Object> inputSchema
) {
    public NetworkTool {
        inputSchema = inputSchema == null ? Map.of() : Map.copyOf(inputSchema);
    }
}
