package com.frankliu.netagent.runner;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.frankliu.netagent.agent.AgentLoop;
import com.frankliu.netagent.config.NetagentSettings;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ScriptedLlmClient;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.logging.RunLogService;
import com.frankliu.netagent.mcp.McpTool;
import com.frankliu.netagent.mcp.ScriptedMcpClient;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class AgentRunServiceTest {

    private final ObjectMapper objectMapper = new ObjectMapper()
            .findAndRegisterModules()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    @TempDir
    Path tempDir;

    @Test
    void runWritesTraceBearingWorkbenchArtifact() throws Exception {
        NetagentSettings settings = settings();
        McpTool labsTool = new McpTool("get_cml_labs", "List labs", Map.of("type", "object"));

        AgentRunResult result = service().run(
                settings,
                "list labs",
                "system",
                new ScriptedLlmClient(List.of(
                        new LlmResponse("checking", List.of(new ToolCall("call-0", "get_cml_labs", Map.of())), "tool_calls", 5, 2, null),
                        new LlmResponse("Done.", List.of(), "stop", 7, 3, null)
                )),
                new ScriptedMcpClient(Map.of("get_cml_labs", "[]"), List.of(labsTool))
        );

        JsonNode json = objectMapper.readTree(Files.readString(result.runLogPath()));
        assertThat(result.finalAnswer()).isEqualTo("Done.");
        assertThat(json.at("/experimentId").asLong()).isEqualTo(42L);
        assertThat(json.at("/agentConfigId").asLong()).isEqualTo(7L);
        assertThat(json.at("/workbench_import/schema_version").asText()).isEqualTo("1.0");
        assertThat(json.at("/agent/provider").asText()).isEqualTo("java-test");
        assertThat(json.at("/metrics/total_tokens").asInt()).isEqualTo(17);
        assertThat(json.at("/steps_trace/0/tool_calls/0/name").asText()).isEqualTo("get_cml_labs");
        assertThat(json.at("/tool_audit_summary/total_calls").asInt()).isEqualTo(1);
    }

    @Test
    void runWritesFailedArtifactWhenRuntimeFails() throws Exception {
        NetagentSettings settings = settings();

        assertThatThrownBy(() -> service().run(
                settings,
                "fail",
                "system",
                (systemPrompt, messages, tools) -> {
                    throw new IllegalStateException("model unavailable");
                },
                new ScriptedMcpClient(Map.of())
        )).isInstanceOf(AgentRunServiceException.class)
                .hasMessageContaining("Run log written");

        Path runJson = Files.walk(tempDir)
                .filter(path -> path.getFileName().toString().equals("run.json"))
                .findFirst()
                .orElseThrow();
        JsonNode json = objectMapper.readTree(Files.readString(runJson));
        assertThat(json.at("/result/status").asText()).isEqualTo("failed");
        assertThat(json.at("/result/error_message").asText()).contains("model unavailable");
    }

    @Test
    void runWithFactoryWritesFailedArtifactWhenMcpStartupFails() throws Exception {
        NetagentSettings settings = settings();

        assertThatThrownBy(() -> service().runWithMcpFactory(
                settings,
                "list labs",
                "system",
                new ScriptedLlmClient(List.of()),
                () -> {
                    throw new IllegalStateException("cml-mcp unavailable");
                }
        )).isInstanceOf(AgentRunServiceException.class)
                .hasMessageContaining("Run log written");

        Path runJson = Files.walk(tempDir)
                .filter(path -> path.getFileName().toString().equals("run.json"))
                .findFirst()
                .orElseThrow();
        JsonNode json = objectMapper.readTree(Files.readString(runJson));
        assertThat(json.at("/result/status").asText()).isEqualTo("failed");
        assertThat(json.at("/result/error_message").asText()).contains("cml-mcp unavailable");
    }

    @Test
    void runWithFactoryClosesManagedMcpClient() throws Exception {
        NetagentSettings settings = settings();
        CloseableScriptedMcpClient mcp = new CloseableScriptedMcpClient(
                Map.of(),
                List.of()
        );

        service().runWithMcpFactory(
                settings,
                "answer directly",
                "system",
                new ScriptedLlmClient(List.of(new LlmResponse("Done.", List.of(), "stop", 1, 1, null))),
                () -> mcp
        );

        assertThat(mcp.closed()).isTrue();
    }

    private AgentRunService service() {
        return new AgentRunService(new AgentLoop(), new RunLogService(objectMapper));
    }

    private NetagentSettings settings() {
        return NetagentSettings.fromMap(Map.of(
                "LLM_PROVIDER", "java-test",
                "LLM_MODEL", "scripted",
                "NETAGENT_WORKBENCH_EXPERIMENT_ID", "42",
                "NETAGENT_WORKBENCH_AGENT_CONFIG_ID", "7",
                "NETAGENT_RUNS_ROOT", tempDir.toString()
        ));
    }

    private static final class CloseableScriptedMcpClient extends ScriptedMcpClient implements AutoCloseable {
        private boolean closed;

        private CloseableScriptedMcpClient(Map<String, String> results, List<McpTool> tools) {
            super(results, tools);
        }

        @Override
        public void close() {
            closed = true;
        }

        private boolean closed() {
            return closed;
        }
    }
}
