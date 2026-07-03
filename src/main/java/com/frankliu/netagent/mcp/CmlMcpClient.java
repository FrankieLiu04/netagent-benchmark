package com.frankliu.netagent.mcp;

import java.util.Map;
import java.util.List;

public interface CmlMcpClient {
    // MCP transport details live in adapters; the loop only needs tools and calls.
    List<McpTool> listTools();

    String callTool(String name, Map<String, Object> arguments);
}
