package com.frankliu.netagent.adapters.llm;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.frankliu.netagent.adapters.llm.openai.OpenAiChatLlmClient;
import com.frankliu.netagent.experiment.NetagentSettings;
import com.frankliu.netagent.ports.llm.LlmClient;

public final class LlmClientFactory {

    private LlmClientFactory() {
    }

    public static LlmClient fromSettings(NetagentSettings settings, ObjectMapper objectMapper) {
        return OpenAiChatLlmClient.fromSettings(settings, objectMapper);
    }
}
