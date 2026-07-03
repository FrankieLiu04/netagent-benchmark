package com.frankliu.netagent.config;

import org.junit.jupiter.api.Test;

import java.nio.file.Path;
import java.time.Duration;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class NetagentSettingsTest {

    @Test
    void defaultsMatchCurrentBenchmarkRuntime() {
        NetagentSettings settings = NetagentSettings.fromMap(Map.of());

        assertThat(settings.llmProvider()).isEqualTo("deepseek");
        assertThat(settings.modelName()).isEqualTo("deepseek-v4-flash");
        assertThat(settings.providerBaseUrl()).isEqualTo("https://api.deepseek.com");
        assertThat(settings.maxTurns()).isEqualTo(20);
        assertThat(settings.mcpTimeout()).isEqualTo(Duration.ofSeconds(30));
        assertThat(settings.cmlMcpCommand()).isEqualTo("python");
        assertThat(settings.cmlMcpArgs()).containsExactly("-m", "cml_mcp");
        assertThat(settings.runsRoot()).isEqualTo(Path.of("experiments/runs"));
    }

    @Test
    void openAiProviderUsesOpenAiKeyAndBaseUrl() {
        NetagentSettings settings = NetagentSettings.fromMap(Map.of(
                "LLM_PROVIDER", "openai",
                "LLM_MODEL", "gpt-test",
                "OPENAI_API_KEY", "key",
                "OPENAI_BASE_URL", "https://example.test/v1",
                "NETAGENT_MAX_TURNS", "7",
                "NETAGENT_CML_MCP_COMMAND", "/opt/cml-mcp",
                "NETAGENT_CML_MCP_ARGS", "--stdio,--debug",
                "NETAGENT_RUNS_ROOT", "tmp/runs",
                "NETAGENT_WORKBENCH_EXPERIMENT_ID", "42",
                "NETAGENT_WORKBENCH_AGENT_CONFIG_ID", "7"
        ));

        assertThat(settings.llmProvider()).isEqualTo("openai");
        assertThat(settings.modelName()).isEqualTo("gpt-test");
        assertThat(settings.providerApiKey()).isEqualTo("key");
        assertThat(settings.providerBaseUrl()).isEqualTo("https://example.test/v1");
        assertThat(settings.maxTurns()).isEqualTo(7);
        assertThat(settings.cmlMcpCommand()).isEqualTo("/opt/cml-mcp");
        assertThat(settings.cmlMcpArgs()).containsExactly("--stdio", "--debug");
        assertThat(settings.runsRoot()).isEqualTo(Path.of("tmp/runs"));
        assertThat(settings.workbenchExperimentId()).isEqualTo(42L);
        assertThat(settings.workbenchAgentConfigId()).isEqualTo(7L);
    }

    @Test
    void cmlEnvironmentContainsOnlyRuntimeMcpValues() {
        NetagentSettings settings = NetagentSettings.fromMap(Map.of(
                "CML_URL", "https://cml.example",
                "CML_USERNAME", "user",
                "CML_PASSWORD", "secret",
                "CML_VERIFY_SSL", "true",
                "NETAGENT_MCP_TIMEOUT_SECONDS", "45"
        ));

        assertThat(settings.cmlEnvironment()).containsEntry("CML_URL", "https://cml.example");
        assertThat(settings.cmlEnvironment()).containsEntry("CML_USERNAME", "user");
        assertThat(settings.cmlEnvironment()).containsEntry("CML_PASSWORD", "secret");
        assertThat(settings.cmlEnvironment()).containsEntry("CML_VERIFY_SSL", "true");
        assertThat(settings.cmlEnvironment()).containsEntry("NETAGENT_MCP_TIMEOUT_SECONDS", "45");
        assertThat(settings.cmlEnvironment()).doesNotContainKey("DEEPSEEK_API_KEY");
    }
}
