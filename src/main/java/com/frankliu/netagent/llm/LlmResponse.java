package com.frankliu.netagent.llm;

import java.util.List;
import java.util.Map;

public record LlmResponse(
        String content,
        List<ToolCall> toolCalls,
        String finishReason,
        int promptTokens,
        int completionTokens,
        Map<String, Object> rawMessage
) {
    public LlmResponse {
        toolCalls = toolCalls == null ? List.of() : List.copyOf(toolCalls);
        rawMessage = rawMessage == null ? Map.of() : Map.copyOf(rawMessage);
    }
}
