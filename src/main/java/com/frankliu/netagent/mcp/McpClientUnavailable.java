package com.frankliu.netagent.mcp;

import java.util.List;
import java.util.Map;

public class McpClientUnavailable implements CmlMcpClient {

    private final CmlMcpServerSpec spec;

    public McpClientUnavailable(CmlMcpServerSpec spec) {
        this.spec = spec;
    }

    @Override
    public List<McpTool> listTools() {
        throw unavailable();
    }

    @Override
    public String callTool(String name, Map<String, Object> arguments) {
        throw unavailable();
    }

    private IllegalStateException unavailable() {
        return new IllegalStateException(
                "No CML MCP client is attached. Use SdkCmlMcpClient with prepared stdio command: "
                        + spec.command() + " " + String.join(" ", spec.args())
        );
    }
}
