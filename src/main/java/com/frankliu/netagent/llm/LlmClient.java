package com.frankliu.netagent.llm;

import com.frankliu.netagent.mcp.McpTool;

import java.util.List;

public interface LlmClient {
    // LLM providers stay behind this port so the loop does not depend on a single SDK.
    LlmResponse chat(String systemPrompt, List<ChatMessage> messages, List<McpTool> tools);
}
