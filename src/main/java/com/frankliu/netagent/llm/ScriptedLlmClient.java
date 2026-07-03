package com.frankliu.netagent.llm;

import com.frankliu.netagent.mcp.McpTool;

import java.util.ArrayDeque;
import java.util.List;
import java.util.Queue;

public class ScriptedLlmClient implements LlmClient {

    private final Queue<LlmResponse> responses;

    public ScriptedLlmClient(List<LlmResponse> responses) {
        this.responses = new ArrayDeque<>(responses);
    }

    @Override
    public LlmResponse chat(String systemPrompt, List<ChatMessage> messages, List<McpTool> tools) {
        if (responses.isEmpty()) {
            return new LlmResponse("No scripted response remains.", List.of(), "stop", 0, 0, null);
        }
        return responses.remove();
    }
}
