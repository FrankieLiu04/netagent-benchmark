package com.frankliu.netagent.adapters.llm.replay;

import com.frankliu.netagent.ports.llm.ChatMessage;
import com.frankliu.netagent.ports.llm.LlmClient;
import com.frankliu.netagent.ports.llm.LlmResponse;
import com.frankliu.netagent.ports.network.NetworkTool;

import java.util.ArrayDeque;
import java.util.List;
import java.util.Queue;

public class ScriptedLlmClient implements LlmClient {

    private final Queue<LlmResponse> responses;

    public ScriptedLlmClient(List<LlmResponse> responses) {
        this.responses = new ArrayDeque<>(responses);
    }

    @Override
    public LlmResponse chat(String systemPrompt, List<ChatMessage> messages, List<NetworkTool> tools) {
        if (responses.isEmpty()) {
            return new LlmResponse("No scripted response remains.", List.of(), "stop", 0, 0);
        }
        return responses.remove();
    }
}
