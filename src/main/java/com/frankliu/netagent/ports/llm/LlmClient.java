package com.frankliu.netagent.ports.llm;

import com.frankliu.netagent.ports.network.NetworkTool;

import java.util.List;

public interface LlmClient {
    // LLM providers stay behind this port so the loop does not depend on a single SDK.
    LlmResponse chat(String systemPrompt, List<ChatMessage> messages, List<NetworkTool> tools);
}
