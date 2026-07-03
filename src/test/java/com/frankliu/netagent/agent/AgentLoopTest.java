package com.frankliu.netagent.agent;

import com.frankliu.netagent.llm.ChatMessage;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ScriptedLlmClient;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.mcp.McpTool;
import com.frankliu.netagent.mcp.ScriptedMcpClient;
import com.frankliu.netagent.trace.AgentLoopResult;
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
                new ScriptedMcpClient(Map.of("get_cml_labs", "[\"OSPF-Demo\", \"BGP-Lab\"]")),
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
        assertThat(result.toolAuditSummary().totalCalls()).isEqualTo(1);
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
                new ScriptedMcpClient(Map.of("delete_cml_lab", "deleted")),
                List.of(tool("delete_cml_lab")),
                5
        );

        assertThat(result.toolAudit().getFirst().mutating()).isTrue();
        assertThat(result.toolAuditSummary().mutatingCalls()).isEqualTo(1);
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
                new ScriptedMcpClient(Map.of()),
                List.of(tool("missing_tool")),
                5
        );

        assertThat(result.toolAudit().getFirst().success()).isFalse();
        assertThat(result.toolAudit().getFirst().error()).contains("No scripted MCP result");
        assertThat(result.messages().get(2).content()).startsWith("Error:");
        assertThat(result.toolAuditSummary().failedCalls()).isEqualTo(1);
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
                new ScriptedMcpClient(Map.of("get_cml_labs", "[]")),
                List.of(tool("get_cml_labs")),
                2
        );

        assertThat(result.steps()).isEqualTo(2);
        assertThat(result.finalAnswer()).isEqualTo("checking-2");
    }

    private LlmResponse response(String content, List<ToolCall> toolCalls, int promptTokens, int completionTokens) {
        return new LlmResponse(content, toolCalls, toolCalls.isEmpty() ? "stop" : "tool_calls", promptTokens, completionTokens, null);
    }

    private McpTool tool(String name) {
        return new McpTool(name, "mock", Map.of("type", "object", "properties", Map.of()));
    }
}
