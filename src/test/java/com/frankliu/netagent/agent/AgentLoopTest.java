package com.frankliu.netagent.agent;

import com.frankliu.netagent.adapters.llm.replay.ScriptedLlmClient;
import com.frankliu.netagent.adapters.network.replay.ReplayNetworkEnvironment;
import com.frankliu.netagent.artifact.trace.AgentLoopResult;
import com.frankliu.netagent.ports.llm.ChatMessage;
import com.frankliu.netagent.ports.llm.LlmResponse;
import com.frankliu.netagent.ports.llm.ToolCall;
import com.frankliu.netagent.ports.network.NetworkTool;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class AgentLoopTest {

    private final AgentLoop loop = new AgentLoop();

    @Test
    void runsToolCallingLoopUntilFinalAnswer() {
        AgentLoopResult result = loop.run(
                "list labs",
                "test",
                new ScriptedLlmClient(List.of(
                        response("checking", List.of(new ToolCall("call-0", "get_cml_labs", Map.of())), 50, 10),
                        response("Done. Found 2 labs.", List.of(), 100, 30)
                )),
                new ReplayNetworkEnvironment(Map.of("get_cml_labs", "[\"OSPF-Demo\", \"BGP-Lab\"]")),
                List.of(tool("get_cml_labs")),
                5
        );

        assertThat(result.steps()).isEqualTo(2);
        assertThat(result.finalAnswer()).contains("2 labs");
        assertThat(result.totalPromptTokens()).isEqualTo(150);
        assertThat(result.totalCompletionTokens()).isEqualTo(40);
        assertThat(result.messages()).extracting(ChatMessage::role)
                .containsExactly("user", "assistant", "tool");
        assertThat(result.traces().getFirst().toolResults().getFirst())
                .containsEntry("success", true)
                .containsEntry("tool_name", "get_cml_labs");
        assertThat(result.toolAudit()).hasSize(1);
        assertThat(result.toolAudit().getFirst().mutating()).isFalse();
        assertThat(result.toolAuditCounts().totalCalls()).isEqualTo(1);
    }

    @Test
    void recordsMutatingToolCalls() {
        AgentLoopResult result = loop.run(
                "delete a lab",
                "test",
                new ScriptedLlmClient(List.of(
                        response("deleting", List.of(new ToolCall("call-0", "delete_cml_lab", Map.of("lab_id", "x"))), 20, 5),
                        response("Deletion request sent.", List.of(), 30, 6)
                )),
                new ReplayNetworkEnvironment(Map.of("delete_cml_lab", "deleted")),
                List.of(tool("delete_cml_lab")),
                5
        );

        assertThat(result.toolAudit().getFirst().mutating()).isTrue();
        assertThat(result.toolAuditCounts().mutatingCalls()).isEqualTo(1);
    }

    @Test
    void returnsToolFailuresAsObservations() {
        AgentLoopResult result = loop.run(
                "unknown tool",
                "test",
                new ScriptedLlmClient(List.of(
                        response("calling", List.of(new ToolCall("call-0", "missing_tool", Map.of())), 20, 5),
                        response("The tool failed.", List.of(), 30, 6)
                )),
                new ReplayNetworkEnvironment(Map.of()),
                List.of(tool("missing_tool")),
                5
        );

        assertThat(result.toolAudit().getFirst().success()).isFalse();
        assertThat(result.toolAudit().getFirst().error()).contains("No scripted MCP result");
        assertThat(result.messages().get(2).content()).startsWith("Error:");
        assertThat(result.toolAuditCounts().failedCalls()).isEqualTo(1);
    }

    @Test
    void preservesLastModelTextWhenMaxStepsIsExhausted() {
        AgentLoopResult result = loop.run(
                "loop forever",
                "test",
                new ScriptedLlmClient(List.of(
                        response("checking-1", List.of(new ToolCall("call-0", "get_cml_labs", Map.of())), 10, 1),
                        response("checking-2", List.of(new ToolCall("call-1", "get_cml_labs", Map.of())), 10, 1)
                )),
                new ReplayNetworkEnvironment(Map.of("get_cml_labs", "[]")),
                List.of(tool("get_cml_labs")),
                2
        );

        assertThat(result.steps()).isEqualTo(2);
        assertThat(result.finalAnswer()).isEqualTo("checking-2");
    }

    private LlmResponse response(String content, List<ToolCall> toolCalls, int promptTokens, int completionTokens) {
        return new LlmResponse(content, toolCalls, toolCalls.isEmpty() ? "stop" : "tool_calls", promptTokens, completionTokens);
    }

    private NetworkTool tool(String name) {
        return new NetworkTool(name, "mock", Map.of("type", "object", "properties", Map.of()));
    }
}
