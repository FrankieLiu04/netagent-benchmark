package com.frankliu.netagent.artifact;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import com.frankliu.netagent.agent.AgentLoop;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ScriptedLlmClient;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.mcp.McpTool;
import com.frankliu.netagent.mcp.ScriptedMcpClient;
import com.frankliu.netagent.trace.AgentLoopResult;
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
    void completedArtifactMatchesWorkbenchImportShape() {
        RunArtifact artifact = ArtifactFactory.completed(
                "run-1",
                Instant.parse("2026-07-03T12:00:00Z"),
                "list all CML labs",
                "openai-compatible",
                "deepseek-v4-flash",
                Path.of("experiments/runs/run-1/run.json"),
                "done",
                BigDecimal.valueOf(1.25),
                10,
                5,
                new ArtifactFactory.ToolAuditSummary(3, 1, 0)
        );

        JsonNode json = objectMapper.valueToTree(artifact);

        assertThat(json.has("experimentId")).isFalse();
        assertThat(json.at("/workbench_import/schema_version").asText()).isEqualTo("1.0");
        assertThat(json.at("/workbench_import/run_id").asText()).isEqualTo("run-1");
        assertThat(json.at("/workbench_import/timestamp").asText()).isEqualTo("2026-07-03T12:00:00Z");
        assertThat(json.at("/benchmark/name").asText()).isEqualTo("netagent");
        assertThat(json.at("/benchmark/case_id").asText()).isEqualTo("run-1");
        assertThat(json.at("/agent/reasoning_mode").asText()).isEqualTo("default");
        assertThat(json.at("/result/final_answer").asText()).isEqualTo("done");
        assertThat(json.at("/metrics/total_tokens").asInt()).isEqualTo(15);
        assertThat(json.at("/metrics/mutating_tool_calls").asInt()).isEqualTo(1);
        assertThat(json.at("/artifacts/run_log_path").asText()).endsWith("run.json");
    }

    @Test
    void loopArtifactKeepsTraceAndAuditDetails() {
        AgentLoopResult result = new AgentLoop().run(
                "list labs",
                "test",
                new ScriptedLlmClient(List.of(
                        new LlmResponse(
                                "checking",
                                List.of(new ToolCall("call-0", "get_cml_labs", Map.of())),
                                "tool_calls",
                                50,
                                10,
                                null
                        ),
                        new LlmResponse("Done.", List.of(), "stop", 100, 30, null)
                )),
                new ScriptedMcpClient(Map.of("get_cml_labs", "[]")),
                List.of(new McpTool("get_cml_labs", "mock", Map.of())),
                5
        );

        RunArtifact artifact = ArtifactFactory.completedFromLoopResult(
                "run-2",
                Instant.parse("2026-07-03T12:00:00Z"),
                "list labs",
                "java-migration",
                "loop-smoke",
                Path.of("experiments/runs/run-2/run.json"),
                result
        );

        JsonNode json = objectMapper.valueToTree(artifact);

        assertThat(json.at("/run_id").asText()).isEqualTo("run-2");
        assertThat(json.at("/steps").asInt()).isEqualTo(2);
        assertThat(json.at("/steps_trace/0/finish_reason").asText()).isEqualTo("tool_calls");
        assertThat(json.at("/steps_trace/0/tool_calls/0/name").asText()).isEqualTo("get_cml_labs");
        assertThat(json.at("/steps_trace/0/tool_audit/0/tool_name").asText()).isEqualTo("get_cml_labs");
        assertThat(json.at("/tool_audit_summary/total_calls").asInt()).isEqualTo(1);
        assertThat(json.at("/tool_audit_summary/successful_calls").asInt()).isEqualTo(1);
        assertThat(json.at("/metrics/total_tokens").asInt()).isEqualTo(190);
    }

    @Test
    void workbenchIdsAreSerializedWhenConfigured() {
        RunArtifact artifact = ArtifactFactory.withWorkbenchIds(
                ArtifactFactory.completed(
                        "run-3",
                        Instant.parse("2026-07-03T12:00:00Z"),
                        "list labs",
                        "openai-compatible",
                        "deepseek-v4-flash",
                        Path.of("experiments/runs/run-3/run.json"),
                        "done",
                        BigDecimal.ONE,
                        1,
                        2,
                        ArtifactFactory.ToolAuditSummary.empty()
                ),
                42L,
                7L
        );

        JsonNode json = objectMapper.valueToTree(artifact);

        assertThat(json.at("/experimentId").asLong()).isEqualTo(42L);
        assertThat(json.at("/agentConfigId").asLong()).isEqualTo(7L);
        assertThat(json.at("/workbench_import/run_id").asText()).isEqualTo("run-3");
    }
}
