package com.frankliu.netagent.llm;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.frankliu.netagent.config.NetagentSettings;
import com.frankliu.netagent.llm.anthropic.AnthropicLlmClient;
import com.frankliu.netagent.llm.openai.OpenAiChatLlmClient;

public final class LlmClientFactory {

    private LlmClientFactory() {
    }

    public static LlmClient fromSettings(NetagentSettings settings, ObjectMapper objectMapper) {
        if ("anthropic".equalsIgnoreCase(settings.llmProvider())) {
            return AnthropicLlmClient.fromSettings(settings);
        }
        return OpenAiChatLlmClient.fromSettings(settings, objectMapper);
    }
}
