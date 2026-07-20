package com.frankliu.netagent.artifact;

import com.frankliu.netagent.artifact.trace.AgentLoopResult;
import com.frankliu.netagent.artifact.trace.ToolAuditEntry;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.nio.file.Path;
import java.time.Instant;
import java.util.Comparator;
import java.util.List;

/** Creates the single run.json schema used by the benchmark. */
public final class ArtifactFactory {

    private static final String SCHEMA_VERSION = "1.0";
    private static final String DEFAULT_MODE = "agent-run";

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
            ToolAuditCounts toolAuditCounts
    ) {
        return build(
                runId, timestamp, task, provider, model, runLogPath, "completed", finalAnswer, null,
                durationSeconds, promptTokens, completionTokens, toolAuditCounts, emptyTrace(toolAuditCounts)
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
        ToolAuditCounts counts = result.toolAuditCounts();
        RunArtifact.Trace trace = new RunArtifact.Trace(
                result.traces(), result.toolAudit(), toolAuditSummary(result.toolAudit())
        );
        return build(
                runId, timestamp, task, provider, model, runLogPath, "completed", result.finalAnswer(), null,
                rounded(result.durationSeconds()), result.totalPromptTokens(), result.totalCompletionTokens(), counts, trace
        );
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
            ToolAuditCounts toolAuditCounts
    ) {
        return build(
                runId, timestamp, task, provider, model, runLogPath, "failed", null, errorMessage,
                durationSeconds, null, null, toolAuditCounts, emptyTrace(toolAuditCounts)
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
            ToolAuditCounts toolAuditCounts,
            RunArtifact.Trace trace
    ) {
        ToolAuditCounts counts = toolAuditCounts == null ? ToolAuditCounts.empty() : toolAuditCounts;
        return new RunArtifact(
                SCHEMA_VERSION,
                runId,
                timestamp,
                new RunArtifact.Task(task, runId, DEFAULT_MODE),
                new RunArtifact.Agent(provider, model),
                new RunArtifact.Result(status, null, finalAnswer, errorMessage),
                new RunArtifact.Metrics(
                        durationSeconds,
                        promptTokens,
                        completionTokens,
                        totalTokens(promptTokens, completionTokens),
                        counts.totalCalls(),
                        counts.mutatingCalls(),
                        counts.failedCalls()
                ),
                trace,
                new RunArtifact.Artifacts(runLogPath.toString())
        );
    }

    private static RunArtifact.Trace emptyTrace(ToolAuditCounts counts) {
        return new RunArtifact.Trace(List.of(), List.of(), new RunArtifact.ToolAuditSummary(
                counts.totalCalls(), counts.mutatingCalls(), counts.totalCalls() - counts.mutatingCalls(),
                counts.failedCalls(), counts.totalCalls() - counts.failedCalls(), List.of()
        ));
    }

    private static BigDecimal rounded(double durationSeconds) {
        return BigDecimal.valueOf(durationSeconds).setScale(3, RoundingMode.HALF_UP);
    }

    private static Integer totalTokens(Integer promptTokens, Integer completionTokens) {
        if (promptTokens == null && completionTokens == null) {
            return null;
        }
        return (promptTokens == null ? 0 : promptTokens) + (completionTokens == null ? 0 : completionTokens);
    }

    public record ToolAuditCounts(Integer totalCalls, Integer mutatingCalls, Integer failedCalls) {
        public static ToolAuditCounts empty() {
            return new ToolAuditCounts(0, 0, 0);
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
                totalCalls, mutatingCalls, totalCalls - mutatingCalls, failedCalls,
                totalCalls - failedCalls, toolNames
        );
    }
}
