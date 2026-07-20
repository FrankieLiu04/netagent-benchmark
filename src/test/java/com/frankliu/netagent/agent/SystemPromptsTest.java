package com.frankliu.netagent.agent;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class SystemPromptsTest {

    @Test
    void cmlAssistantPromptDescribesToolUseContract() {
        String prompt = SystemPrompts.cmlAssistant();

        assertThat(prompt).contains("CML network lab assistant");
        assertThat(prompt).contains("Do not invent lab names");
        assertThat(prompt).contains("only use the tools made available");
        assertThat(prompt).contains("When a CML tool fails");
    }
}
