package com.frankliu.netagent.adapters.network.cml;

import com.frankliu.netagent.ports.network.NetworkTool;
import io.modelcontextprotocol.spec.McpSchema;
import org.junit.jupiter.api.Test;

import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class CmlMcpEnvironmentTest {

    @Test
    void mapsSdkToolsToLocalToolPort() {
        Map<String, Object> schema = Map.of(
                "type", "object",
                "properties", Map.of("lab_id", Map.of("type", "string"))
        );
        McpSchema.Tool sdkTool = sdkTool("get_cml_lab", "Get a CML lab", schema);

        NetworkTool tool = CmlMcpEnvironment.toNetworkTool(sdkTool);

        assertThat(tool.name()).isEqualTo("get_cml_lab");
        assertThat(tool.description()).isEqualTo("Get a CML lab");
        assertThat(tool.inputSchema()).isEqualTo(schema);
    }

    @Test
    void joinsTextContentBlocksAsToolObservation() {
        String text = CmlMcpEnvironment.contentToText(McpSchema.CallToolResult.builder()
                .addTextContent("first")
                .addTextContent("second")
                .build()
                .content());

        assertThat(text).isEqualTo("first\nsecond");
    }

    @Test
    void addsEmptyPropertiesWhenSdkToolOmitsThem() {
        McpSchema.Tool sdkTool = sdkTool("list_cml_labs", "List labs", Map.of("type", "object"));

        NetworkTool tool = CmlMcpEnvironment.toNetworkTool(sdkTool);

        assertThat(tool.inputSchema())
                .containsEntry("type", "object")
                .containsKey("properties");
    }

    @SuppressWarnings("deprecation")
    private McpSchema.Tool sdkTool(String name, String description, Map<String, Object> inputSchema) {
        // The SDK test fixture needs a Tool instance without opening a real MCP session.
        return new McpSchema.Tool(name, null, description, inputSchema, null, null, null);
    }
}
