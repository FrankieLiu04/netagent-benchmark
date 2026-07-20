package com.frankliu.netagent.ports.llm;

import java.util.List;

public record LlmResponse(
        String content,
        List<ToolCall> toolCalls,
        String finishReason,
        int promptTokens,
        int completionTokens
) {
    public LlmResponse {
        toolCalls = toolCalls == null ? List.of() : List.copyOf(toolCalls);
    }
}
