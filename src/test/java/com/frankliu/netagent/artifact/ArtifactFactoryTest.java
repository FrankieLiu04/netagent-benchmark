package com.frankliu.netagent.artifact;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.frankliu.netagent.adapters.llm.replay.ScriptedLlmClient;
import com.frankliu.netagent.adapters.network.replay.ReplayNetworkEnvironment;
import com.frankliu.netagent.agent.AgentLoop;
import com.frankliu.netagent.artifact.trace.AgentLoopResult;
import com.frankliu.netagent.ports.llm.LlmResponse;
import com.frankliu.netagent.ports.llm.ToolCall;
import com.frankliu.netagent.ports.network.NetworkTool;
import org.junit.jupiter.api.Test;

import java.math.BigDecimal;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class ArtifactFactoryTest {

    private final ObjectMapper objectMapper = new ObjectMapper()
            .findAndRegisterModules()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);

    @Test
    void completedArtifactUsesTheBenchmarkOwnedSchema() {
        RunArtifact artifact = ArtifactFactory.completed(
                "run-1",
                Instant.parse("2026-07-03T12:00:00Z"),
                "list all CML labs",
                "deepseek",
                "deepseek-v4-flash",
                Path.of("experiments/runs/run-1/run.json"),
                "done",
                BigDecimal.valueOf(1.25),
                10,
                5,
                new ArtifactFactory.ToolAuditCounts(3, 1, 0)
        );

        JsonNode json = objectMapper.valueToTree(artifact);

        assertThat(json.at("/schema_version").asText()).isEqualTo("1.0");
        assertThat(json.at("/run_id").asText()).isEqualTo("run-1");
        assertThat(json.at("/task/case_id").asText()).isEqualTo("run-1");
        assertThat(json.at("/agent/provider").asText()).isEqualTo("deepseek");
        assertThat(json.at("/result/final_answer").asText()).isEqualTo("done");
        assertThat(json.at("/metrics/total_tokens").asInt()).isEqualTo(15);
        assertThat(json.at("/metrics/mutating_tool_calls").asInt()).isEqualTo(1);
        assertThat(json.at("/artifacts/run_log_path").asText()).endsWith("run.json");
        assertThat(json.has("workbench_import")).isFalse();
    }

    @Test
    void loopArtifactKeepsTraceAndAuditDetails() {
        AgentLoopResult result = new AgentLoop().run(
                "list labs",
                "test",
                new ScriptedLlmClient(List.of(
                        new LlmResponse("checking", List.of(new ToolCall("call-0", "get_cml_labs", Map.of())), "tool_calls", 50, 10),
                        new LlmResponse("Done.", List.of(), "stop", 100, 30)
                )),
                new ReplayNetworkEnvironment(Map.of("get_cml_labs", "[]")),
                List.of(new NetworkTool("get_cml_labs", "mock", Map.of())),
                5
        );

        RunArtifact artifact = ArtifactFactory.completedFromLoopResult(
                "run-2",
                Instant.parse("2026-07-03T12:00:00Z"),
                "list labs",
                "deepseek",
                "loop-smoke",
                Path.of("experiments/runs/run-2/run.json"),
                result
        );

        JsonNode json = objectMapper.valueToTree(artifact);

        assertThat(json.at("/trace/steps/0/finish_reason").asText()).isEqualTo("tool_calls");
        assertThat(json.at("/trace/steps/0/tool_calls/0/name").asText()).isEqualTo("get_cml_labs");
        assertThat(json.at("/trace/steps/0/tool_audit/0/tool_name").asText()).isEqualTo("get_cml_labs");
        assertThat(json.at("/trace/tool_audit_summary/total_calls").asInt()).isEqualTo(1);
        assertThat(json.at("/trace/tool_audit_summary/successful_calls").asInt()).isEqualTo(1);
        assertThat(json.at("/metrics/total_tokens").asInt()).isEqualTo(190);
    }
}
