package com.frankliu.netagent.mcp;

import io.modelcontextprotocol.client.McpClient;
import io.modelcontextprotocol.client.McpSyncClient;
import io.modelcontextprotocol.client.transport.ServerParameters;
import io.modelcontextprotocol.client.transport.StdioClientTransport;
import io.modelcontextprotocol.json.McpJsonDefaults;
import io.modelcontextprotocol.spec.McpSchema;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class SdkCmlMcpClient implements CmlMcpClient, AutoCloseable {

    private final McpSyncClient client;

    public SdkCmlMcpClient(McpSyncClient client) {
        this.client = client;
    }

    public static SdkCmlMcpClient start(CmlMcpServerSpec spec) {
        ServerParameters params = ServerParameters.builder(spec.command())
                .args(spec.args())
                .env(spec.environment())
                .build();
        StdioClientTransport transport = new StdioClientTransport(params, McpJsonDefaults.getMapper());
        McpSyncClient client = McpClient.sync(transport)
                .requestTimeout(spec.requestTimeout())
                .build();
        client.initialize();
        return new SdkCmlMcpClient(client);
    }

    @Override
    public List<McpTool> listTools() {
        return client.listTools().tools().stream()
                .map(SdkCmlMcpClient::toMcpTool)
                .toList();
    }

    @Override
    public String callTool(String name, Map<String, Object> arguments) {
        McpSchema.CallToolResult result = client.callTool(McpSchema.CallToolRequest.builder(name)
                .arguments(arguments)
                .build());
        if (Boolean.TRUE.equals(result.isError())) {
            throw new IllegalStateException(contentToText(result.content()));
        }
        return contentToText(result.content());
    }

    @Override
    public void close() {
        client.closeGracefully();
    }

    static McpTool toMcpTool(McpSchema.Tool tool) {
        return new McpTool(tool.name(), tool.description() == null ? "" : tool.description(), normalizeInputSchema(tool.inputSchema()));
    }

    private static Map<String, Object> normalizeInputSchema(Map<String, Object> inputSchema) {
        Map<String, Object> schema = inputSchema == null ? new LinkedHashMap<>() : new LinkedHashMap<>(inputSchema);
        // Keep tool schemas accepted by OpenAI-compatible tool-call APIs when MCP omits properties.
        schema.putIfAbsent("type", "object");
        schema.putIfAbsent("properties", Map.of());
        return Map.copyOf(schema);
    }

    static String contentToText(List<McpSchema.Content> content) {
        return content.stream()
                .map(SdkCmlMcpClient::contentBlockToText)
                .reduce((left, right) -> left + "\n" + right)
                .orElse("");
    }

    private static String contentBlockToText(McpSchema.Content content) {
        if (content instanceof McpSchema.TextContent textContent) {
            return textContent.text();
        }
        return content.toString();
    }
}
