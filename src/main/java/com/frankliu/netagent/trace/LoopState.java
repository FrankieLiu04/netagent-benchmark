package com.frankliu.netagent.trace;

import com.frankliu.netagent.llm.ChatMessage;

import java.util.ArrayList;
import java.util.List;

public class LoopState {

    private final List<ChatMessage> messages;
    private final List<StepTrace> traces = new ArrayList<>();
    private final List<ToolAuditEntry> toolAudit = new ArrayList<>();
    private int totalPromptTokens;
    private int totalCompletionTokens;
    private String finalAnswer = "";

    public LoopState(List<ChatMessage> messages) {
        this.messages = messages;
    }

    public List<ChatMessage> messages() {
        return messages;
    }

    public List<StepTrace> traces() {
        return traces;
    }

    public List<ToolAuditEntry> toolAudit() {
        return toolAudit;
    }

    public int totalPromptTokens() {
        return totalPromptTokens;
    }

    public int totalCompletionTokens() {
        return totalCompletionTokens;
    }

    public String finalAnswer() {
        return finalAnswer;
    }

    public void setFinalAnswer(String finalAnswer) {
        this.finalAnswer = finalAnswer == null ? "" : finalAnswer;
    }

    public void recordTokens(int promptTokens, int completionTokens) {
        totalPromptTokens += promptTokens;
        totalCompletionTokens += completionTokens;
    }
}
