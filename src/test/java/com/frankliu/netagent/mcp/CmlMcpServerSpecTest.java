package com.frankliu.netagent.mcp;

import com.frankliu.netagent.config.NetagentSettings;
import org.junit.jupiter.api.Test;

import java.time.Duration;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class CmlMcpServerSpecTest {

    @Test
    void buildsCmlMcpStdioSpecFromSettings() {
        NetagentSettings settings = NetagentSettings.fromMap(Map.of(
                "NETAGENT_CML_MCP_COMMAND", "/opt/cml-mcp",
                "NETAGENT_CML_MCP_ARGS", "--stdio,--log-level,debug",
                "CML_URL", "https://cml.example",
                "CML_USERNAME", "user",
                "CML_PASSWORD", "secret",
                "CML_VERIFY_SSL", "true",
                "NETAGENT_MCP_TIMEOUT_SECONDS", "45"
        ));

        CmlMcpServerSpec spec = CmlMcpServerSpec.fromSettings(settings);

        assertThat(spec.command()).isEqualTo("/opt/cml-mcp");
        assertThat(spec.args()).containsExactly("--stdio", "--log-level", "debug");
        assertThat(spec.requestTimeout()).isEqualTo(Duration.ofSeconds(45));
        assertThat(spec.environment()).containsEntry("CML_URL", "https://cml.example");
        assertThat(spec.environment()).containsEntry("CML_PASSWORD", "secret");
    }

    @Test
    void unavailableClientFailsWithPreparedCommand() {
        CmlMcpServerSpec spec = new CmlMcpServerSpec("python", java.util.List.of("-m", "cml_mcp"), Map.of(), Duration.ofSeconds(30));
        McpClientUnavailable client = new McpClientUnavailable(spec);

        assertThatThrownBy(client::listTools)
                .isInstanceOf(IllegalStateException.class)
                .hasMessageContaining("No CML MCP client is attached")
                .hasMessageContaining("python -m cml_mcp");
    }
}
