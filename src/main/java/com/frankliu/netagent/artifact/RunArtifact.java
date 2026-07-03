package com.frankliu.netagent.artifact;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.frankliu.netagent.trace.StepTrace;
import com.frankliu.netagent.trace.ToolAuditEntry;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.List;

public record RunArtifact(
        @JsonInclude(JsonInclude.Include.NON_NULL)
        Long experimentId,
        @JsonInclude(JsonInclude.Include.NON_NULL)
        Long agentConfigId,
        @JsonProperty("run_id") String runId,
        Instant timestamp,
        @JsonProperty("user_task") String userTask,
        @JsonProperty("llm_provider") String llmProvider,
        @JsonProperty("model_name") String modelName,
        @JsonProperty("tool_exposure") String toolExposure,
        @JsonProperty("final_answer") String finalAnswer,
        Integer steps,
        @JsonProperty("total_prompt_tokens") Integer totalPromptTokens,
        @JsonProperty("total_completion_tokens") Integer totalCompletionTokens,
        @JsonProperty("duration_seconds") BigDecimal durationSeconds,
        @JsonProperty("steps_trace") List<StepTrace> stepsTrace,
        @JsonProperty("tool_audit_summary") ToolAuditSummary toolAuditSummary,
        @JsonProperty("tool_audit") List<ToolAuditEntry> toolAudit,
        Benchmark benchmark,
        Agent agent,
        Result result,
        Metrics metrics,
        Artifacts artifacts,
        @JsonProperty("workbench_import") WorkbenchImport workbenchImport
) {
    public record WorkbenchImport(
            @JsonProperty("schema_version") String schemaVersion,
            @JsonProperty("run_id") String runId,
            Instant timestamp,
            String task
    ) {
    }

    public record Benchmark(
            String name,
            @JsonProperty("case_id") String caseId,
            String level
    ) {
    }

    public record Agent(
            String provider,
            String model,
            @JsonProperty("reasoning_mode") String reasoningMode
    ) {
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

    public record Artifacts(
            @JsonProperty("run_log_path") String runLogPath,
            @JsonProperty("generated_code_path") String generatedCodePath,
            @JsonProperty("verifier_output_path") String verifierOutputPath
    ) {
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
