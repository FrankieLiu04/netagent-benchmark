package com.frankliu.netagent.artifact;

import com.frankliu.netagent.trace.AgentLoopResult;
import com.frankliu.netagent.trace.ToolAuditEntry;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;

public final class ArtifactFactory {

    private ArtifactFactory() {
    }

    public static RunArtifact completed(
            String runId,
            Instant timestamp,
            String task,
            String provider,
            String model,
            Path runLogPath,
            String finalAnswer,
            BigDecimal durationSeconds,
            Integer promptTokens,
            Integer completionTokens,
            ToolAuditSummary toolAuditSummary
    ) {
        return build(
                runId,
                timestamp,
                task,
                provider,
                model,
                runLogPath,
                "completed",
                finalAnswer,
                null,
                durationSeconds,
                promptTokens,
                completionTokens,
                toolAuditSummary
        );
    }

    public static RunArtifact completedFromLoopResult(
            String runId,
            Instant timestamp,
            String task,
            String provider,
            String model,
            Path runLogPath,
            AgentLoopResult result
    ) {
        RunArtifact artifact = completed(
                runId,
                timestamp,
                task,
                provider,
                model,
                runLogPath,
                result.finalAnswer(),
                BigDecimal.valueOf(result.durationSeconds()).setScale(3, RoundingMode.HALF_UP),
                result.totalPromptTokens(),
                result.totalCompletionTokens(),
                result.toolAuditSummary()
        );
        return withLoopDetails(artifact, runId, timestamp, task, provider, model, result);
    }

    public static RunArtifact failed(
            String runId,
            Instant timestamp,
            String task,
            String provider,
            String model,
            Path runLogPath,
            String errorMessage,
            BigDecimal durationSeconds,
            ToolAuditSummary toolAuditSummary
    ) {
        return build(
                runId,
                timestamp,
                task,
                provider,
                model,
                runLogPath,
                "failed",
                null,
                errorMessage,
                durationSeconds,
                null,
                null,
                toolAuditSummary
        );
    }

    private static RunArtifact build(
            String runId,
            Instant timestamp,
            String task,
            String provider,
            String model,
            Path runLogPath,
            String status,
            String finalAnswer,
            String errorMessage,
            BigDecimal durationSeconds,
            Integer promptTokens,
            Integer completionTokens,
            ToolAuditSummary toolAuditSummary
    ) {
        ToolAuditSummary audit = toolAuditSummary == null ? ToolAuditSummary.empty() : toolAuditSummary;
        return new RunArtifact(
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                null,
                new RunArtifact.Benchmark("netagent", runId, "agent-run"),
                new RunArtifact.Agent(provider, model, "default"),
                new RunArtifact.Result(status, null, finalAnswer, errorMessage),
                new RunArtifact.Metrics(
                        durationSeconds,
                        promptTokens,
                        completionTokens,
                        totalTokens(promptTokens, completionTokens),
                        audit.totalCalls(),
                        audit.mutatingCalls(),
                        audit.failedCalls()
                ),
                new RunArtifact.Artifacts(runLogPath.toString(), null, null),
                new RunArtifact.WorkbenchImport("1.0", runId, timestamp, task)
        );
    }

    public static RunArtifact withLoopDetails(
            RunArtifact artifact,
            String runId,
            Instant timestamp,
            String task,
            String provider,
            String model,
            AgentLoopResult result
    ) {
        return new RunArtifact(
                artifact.experimentId(),
                artifact.agentConfigId(),
                runId,
                timestamp,
                task,
                provider,
                model,
                "all",
                result.finalAnswer(),
                result.steps(),
                result.totalPromptTokens(),
                result.totalCompletionTokens(),
                BigDecimal.valueOf(result.durationSeconds()).setScale(3, RoundingMode.HALF_UP),
                result.traces(),
                toolAuditSummary(result.toolAudit()),
                result.toolAudit(),
                artifact.benchmark(),
                artifact.agent(),
                artifact.result(),
                artifact.metrics(),
                artifact.artifacts(),
                artifact.workbenchImport()
        );
    }

    public static RunArtifact withWorkbenchIds(
            RunArtifact artifact,
            Long experimentId,
            Long agentConfigId
    ) {
        return new RunArtifact(
                experimentId,
                agentConfigId,
                artifact.runId(),
                artifact.timestamp(),
                artifact.userTask(),
                artifact.llmProvider(),
                artifact.modelName(),
                artifact.toolExposure(),
                artifact.finalAnswer(),
                artifact.steps(),
                artifact.totalPromptTokens(),
                artifact.totalCompletionTokens(),
                artifact.durationSeconds(),
                artifact.stepsTrace(),
                artifact.toolAuditSummary(),
                artifact.toolAudit(),
                artifact.benchmark(),
                artifact.agent(),
                artifact.result(),
                artifact.metrics(),
                artifact.artifacts(),
                artifact.workbenchImport()
        );
    }

    private static Integer totalTokens(Integer promptTokens, Integer completionTokens) {
        if (promptTokens == null && completionTokens == null) {
            return null;
        }
        return (promptTokens == null ? 0 : promptTokens) + (completionTokens == null ? 0 : completionTokens);
    }

    public record ToolAuditSummary(Integer totalCalls, Integer mutatingCalls, Integer failedCalls) {
        public static ToolAuditSummary empty() {
            return new ToolAuditSummary(0, 0, 0);
        }
    }

    private static RunArtifact.ToolAuditSummary toolAuditSummary(List<ToolAuditEntry> audit) {
        int totalCalls = audit.size();
        int mutatingCalls = (int) audit.stream().filter(ToolAuditEntry::mutating).count();
        int failedCalls = (int) audit.stream().filter(entry -> !entry.success()).count();
        List<String> toolNames = audit.stream()
                .map(ToolAuditEntry::toolName)
                .distinct()
                .sorted(Comparator.naturalOrder())
                .toList();
        return new RunArtifact.ToolAuditSummary(
                totalCalls,
                mutatingCalls,
                totalCalls - mutatingCalls,
                failedCalls,
                totalCalls - failedCalls,
                toolNames
        );
    }
}
