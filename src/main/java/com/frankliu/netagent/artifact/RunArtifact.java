package com.frankliu.netagent.artifact;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.frankliu.netagent.artifact.trace.StepTrace;
import com.frankliu.netagent.artifact.trace.ToolAuditEntry;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

/**
 * The durable, sanitized record for one benchmark run.
 *
 * <p>This schema belongs to netagent-benchmark. Other tools may import or
 * transform it, but they must not add runtime dependencies to the runner.</p>
 */
public record RunArtifact(
        @JsonProperty("schema_version") String schemaVersion,
        @JsonProperty("run_id") String runId,
        Instant timestamp,
        Task task,
        Agent agent,
        Result result,
        Metrics metrics,
        Trace trace,
        Artifacts artifacts
) {
    public record Task(
            String description,
            @JsonProperty("case_id") String caseId,
            String mode
    ) {
    }

    public record Agent(String provider, String model) {
    }

    public record Result(
            String status,
            BigDecimal score,
            @JsonProperty("final_answer") String finalAnswer,
            @JsonProperty("error_message") String errorMessage
    ) {
    }

    public record Metrics(
            @JsonProperty("duration_seconds") BigDecimal durationSeconds,
            @JsonProperty("prompt_tokens") Integer promptTokens,
            @JsonProperty("completion_tokens") Integer completionTokens,
            @JsonProperty("total_tokens") Integer totalTokens,
            @JsonProperty("tool_calls") Integer toolCalls,
            @JsonProperty("mutating_tool_calls") Integer mutatingToolCalls,
            @JsonProperty("failed_tool_calls") Integer failedToolCalls
    ) {
    }

    public record Trace(
            List<StepTrace> steps,
            @JsonProperty("tool_audit") List<ToolAuditEntry> toolAudit,
            @JsonProperty("tool_audit_summary") ToolAuditSummary toolAuditSummary
    ) {
    }

    public record Artifacts(@JsonProperty("run_log_path") String runLogPath) {
    }

    public record ToolAuditSummary(
            @JsonProperty("total_calls") Integer totalCalls,
            @JsonProperty("mutating_calls") Integer mutatingCalls,
            @JsonProperty("read_only_calls") Integer readOnlyCalls,
            @JsonProperty("failed_calls") Integer failedCalls,
            @JsonProperty("successful_calls") Integer successfulCalls,
            @JsonProperty("tool_names") List<String> toolNames
    ) {
    }
}
