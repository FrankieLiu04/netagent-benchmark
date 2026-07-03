package com.frankliu.netagent.agent;

import org.junit.jupiter.api.Test;

import static org.assertj.core.api.Assertions.assertThat;

class SystemPromptsTest {

    @Test
    void fullAccessPromptDescribesCmlToolUseContract() {
        String prompt = SystemPrompts.fullAccess();

        assertThat(prompt).contains("CML network lab assistant");
        assertThat(prompt).contains("Do not invent lab names");
        assertThat(prompt).contains("call the relevant MCP tool");
        assertThat(prompt).contains("When a CML tool fails");
    }
}
