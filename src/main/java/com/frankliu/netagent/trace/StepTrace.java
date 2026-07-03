package com.frankliu.netagent.trace;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.frankliu.netagent.llm.ToolCall;

import java.util.List;
import java.util.Map;

public record StepTrace(
        int step,
        @JsonProperty("finish_reason") String finishReason,
        String content,
        @JsonProperty("tool_calls") List<ToolCall> toolCalls,
        @JsonProperty("tool_results") List<Map<String, Object>> toolResults,
        @JsonProperty("tool_audit") List<ToolAuditEntry> toolAudit,
        Usage usage,
        @JsonProperty("elapsed_seconds") double elapsedSeconds
) {
    public record Usage(
            @JsonProperty("prompt_tokens") int promptTokens,
            @JsonProperty("completion_tokens") int completionTokens
    ) {
    }
}
