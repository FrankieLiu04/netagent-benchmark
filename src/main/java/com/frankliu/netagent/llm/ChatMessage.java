package com.frankliu.netagent.llm;

import java.util.List;

public record ChatMessage(
        String role,
        String content,
        String toolCallId,
        List<ToolCall> toolCalls
) {
    public static ChatMessage user(String content) {
        return new ChatMessage("user", content, null, List.of());
    }

    public static ChatMessage assistant(String content, List<ToolCall> toolCalls) {
        return new ChatMessage("assistant", content, null, List.copyOf(toolCalls));
    }

    public static ChatMessage tool(String toolCallId, String content) {
        return new ChatMessage("tool", content, toolCallId, List.of());
    }
}
