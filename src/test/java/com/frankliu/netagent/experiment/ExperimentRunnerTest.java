package com.frankliu.netagent.experiment;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.frankliu.netagent.agent.AgentLoop;
import com.frankliu.netagent.adapters.llm.replay.ScriptedLlmClient;
import com.frankliu.netagent.adapters.network.replay.ReplayNetworkEnvironment;
import com.frankliu.netagent.artifact.RunLogService;
import com.frankliu.netagent.ports.llm.LlmResponse;
import com.frankliu.netagent.ports.llm.ToolCall;
import com.frankliu.netagent.ports.network.NetworkTool;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;
import static org.assertj.core.api.Assertions.assertThatThrownBy;

class ExperimentRunnerTest {

    private final ObjectMapper objectMapper = new ObjectMapper()
            .findAndRegisterModules()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    @TempDir
    Path tempDir;

    @Test
    void runWritesTraceBearingBenchmarkArtifact() throws Exception {
        NetagentSettings settings = settings();
        NetworkTool labsTool = new NetworkTool("get_cml_labs", "List labs", Map.of("type", "object"));

        ExperimentRun result = runner().run(
                settings,
                "list labs",
                "system",
                new ScriptedLlmClient(List.of(
                        new LlmResponse("checking", List.of(new ToolCall("call-0", "get_cml_labs", Map.of())), "tool_calls", 5, 2),
                        new LlmResponse("Done.", List.of(), "stop", 7, 3)
                )),
                new ReplayNetworkEnvironment(Map.of("get_cml_labs", "[]"), List.of(labsTool))
        );

        JsonNode json = objectMapper.readTree(Files.readString(result.runLogPath()));
        assertThat(result.finalAnswer()).isEqualTo("Done.");
        assertThat(json.at("/schema_version").asText()).isEqualTo("1.0");
        assertThat(json.at("/run_id").asText()).isEqualTo(result.runId());
        assertThat(json.at("/agent/provider").asText()).isEqualTo("java-test");
        assertThat(json.at("/metrics/total_tokens").asInt()).isEqualTo(17);
        assertThat(json.at("/trace/steps/0/tool_calls/0/name").asText()).isEqualTo("get_cml_labs");
        assertThat(json.at("/trace/tool_audit_summary/total_calls").asInt()).isEqualTo(1);
    }

    @Test
    void runWritesFailedArtifactWhenRuntimeFails() throws Exception {
        NetagentSettings settings = settings();

        assertThatThrownBy(() -> runner().run(
                settings,
                "fail",
                "system",
                (systemPrompt, messages, tools) -> {
                    throw new IllegalStateException("model unavailable");
                },
                new ReplayNetworkEnvironment(Map.of())
        )).isInstanceOf(ExperimentRunException.class)
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

        assertThatThrownBy(() -> runner().runWithEnvironmentFactory(
                settings,
                "list labs",
                "system",
                new ScriptedLlmClient(List.of()),
                () -> {
                    throw new IllegalStateException("cml-mcp unavailable");
                }
        )).isInstanceOf(ExperimentRunException.class)
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
        CloseableReplayEnvironment environment = new CloseableReplayEnvironment(
                Map.of(),
                List.of()
        );

        runner().runWithEnvironmentFactory(
                settings,
                "answer directly",
                "system",
                new ScriptedLlmClient(List.of(new LlmResponse("Done.", List.of(), "stop", 1, 1))),
                () -> environment
        );

        assertThat(environment.closed()).isTrue();
    }

    private ExperimentRunner runner() {
        return new ExperimentRunner(new AgentLoop(), new RunLogService(objectMapper));
    }

    private NetagentSettings settings() {
        return NetagentSettings.fromMap(Map.of(
                "LLM_PROVIDER", "java-test",
                "LLM_MODEL", "scripted",
                "NETAGENT_RUNS_ROOT", tempDir.toString()
        ));
    }

    private static final class CloseableReplayEnvironment extends ReplayNetworkEnvironment implements AutoCloseable {
        private boolean closed;

        private CloseableReplayEnvironment(Map<String, String> results, List<NetworkTool> tools) {
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
