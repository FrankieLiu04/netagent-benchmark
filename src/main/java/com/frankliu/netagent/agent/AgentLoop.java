package com.frankliu.netagent.agent;

import com.frankliu.netagent.llm.ChatMessage;
import com.frankliu.netagent.llm.LlmClient;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.mcp.CmlMcpClient;
import com.frankliu.netagent.mcp.McpTool;
import com.frankliu.netagent.mcp.ToolPolicy;
import com.frankliu.netagent.trace.AgentLoopResult;
import com.frankliu.netagent.trace.LoopState;
import com.frankliu.netagent.trace.StepTrace;
import com.frankliu.netagent.trace.ToolAuditEntry;

import java.time.Duration;
import java.time.Instant;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class AgentLoop {

    public AgentLoopResult run(
            String task,
            String systemPrompt,
            LlmClient llm,
            CmlMcpClient mcp,
            List<McpTool> tools,
            int maxSteps
    ) {
        LoopState state = new LoopState(new ArrayList<>(List.of(ChatMessage.user(task))));
        Instant loopStart = Instant.now();
        String lastResponseContent = "";

        for (int step = 0; step < maxSteps; step++) {
            Instant stepStart = Instant.now();
            LlmResponse response = llm.chat(systemPrompt, state.messages(), tools);
            state.recordTokens(response.promptTokens(), response.completionTokens());
            lastResponseContent = response.content() == null ? "" : response.content();

            if (response.toolCalls().isEmpty()) {
                state.traces().add(new StepTrace(
                        step,
                        response.finishReason(),
                        response.content(),
                        response.toolCalls(),
                        List.of(),
                        List.of(),
                        new StepTrace.Usage(response.promptTokens(), response.completionTokens()),
                        elapsedSeconds(stepStart)
                ));
                state.setFinalAnswer(lastResponseContent);
                break;
            }
            recordToolStep(state, step, stepStart, response, mcp);
        }

        if (state.finalAnswer().isBlank() && !lastResponseContent.isBlank()) {
            state.setFinalAnswer(lastResponseContent);
        }
        return new AgentLoopResult(
                state.finalAnswer().isBlank() ? "[Agent loop reached max steps without a final answer]" : state.finalAnswer(),
                state.traces().size(),
                List.copyOf(state.traces()),
                List.copyOf(state.toolAudit()),
                state.totalPromptTokens(),
                state.totalCompletionTokens(),
                elapsedSeconds(loopStart),
                List.copyOf(state.messages())
        );
    }

    private void recordToolStep(
            LoopState state,
            int step,
            Instant stepStart,
            LlmResponse response,
            CmlMcpClient mcp
    ) {
        state.messages().add(ChatMessage.assistant(response.content(), response.toolCalls()));
        List<Map<String, Object>> toolResults = new ArrayList<>();
        List<ToolAuditEntry> stepAudit = new ArrayList<>();

        for (ToolCall toolCall : response.toolCalls()) {
            ToolExecution execution = executeTool(step, toolCall, mcp);
            state.messages().add(ChatMessage.tool(toolCall.id(), execution.messageContent()));
            toolResults.add(execution.result());
            stepAudit.add(execution.auditEntry());
        }

        state.toolAudit().addAll(stepAudit);
        state.traces().add(new StepTrace(
                step,
                response.finishReason(),
                response.content(),
                response.toolCalls(),
                List.copyOf(toolResults),
                List.copyOf(stepAudit),
                new StepTrace.Usage(response.promptTokens(), response.completionTokens()),
                elapsedSeconds(stepStart)
        ));
    }

    private ToolExecution executeTool(int step, ToolCall toolCall, CmlMcpClient mcp) {
        Instant start = Instant.now();
        try {
            String resultText = mcp.callTool(toolCall.name(), toolCall.arguments());
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("tool_call_id", toolCall.id());
            result.put("tool_name", toolCall.name());
            result.put("success", true);
            result.put("result", resultText);
            return new ToolExecution(
                    result,
                    resultText,
                    auditEntry(step, toolCall, true, elapsedSeconds(start), resultText.length(), null)
            );
        } catch (RuntimeException ex) {
            String error = ex.getClass().getSimpleName() + ": " + ex.getMessage();
            Map<String, Object> result = new LinkedHashMap<>();
            result.put("tool_call_id", toolCall.id());
            result.put("tool_name", toolCall.name());
            result.put("success", false);
            result.put("error", error);
            return new ToolExecution(
                    result,
                    "Error: " + error,
                    auditEntry(step, toolCall, false, elapsedSeconds(start), 0, error)
            );
        }
    }

    private ToolAuditEntry auditEntry(
            int step,
            ToolCall toolCall,
            boolean success,
            double elapsedSeconds,
            int resultSizeChars,
            String error
    ) {
        return new ToolAuditEntry(
                step,
                toolCall.id(),
                toolCall.name(),
                toolCall.arguments(),
                ToolPolicy.isMutatingTool(toolCall.name()),
                success,
                elapsedSeconds,
                resultSizeChars,
                error
        );
    }

    private double elapsedSeconds(Instant start) {
        return Duration.between(start, Instant.now()).toNanos() / 1_000_000_000.0;
    }

    private record ToolExecution(
            Map<String, Object> result,
            String messageContent,
            ToolAuditEntry auditEntry
    ) {
    }
}
