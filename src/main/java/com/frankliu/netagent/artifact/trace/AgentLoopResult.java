package com.frankliu.netagent.artifact.trace;

import com.frankliu.netagent.artifact.ArtifactFactory;
import com.frankliu.netagent.ports.llm.ChatMessage;

import java.util.List;

public record AgentLoopResult(
        String finalAnswer,
        int steps,
        List<StepTrace> traces,
        List<ToolAuditEntry> toolAudit,
        int totalPromptTokens,
        int totalCompletionTokens,
        double durationSeconds,
        List<ChatMessage> messages
) {
    public ArtifactFactory.ToolAuditCounts toolAuditCounts() {
        return new ArtifactFactory.ToolAuditCounts(
                toolAudit.size(),
                (int) toolAudit.stream().filter(ToolAuditEntry::mutating).count(),
                (int) toolAudit.stream().filter(entry -> !entry.success()).count()
        );
    }
}
