package com.frankliu.netagent.trace;

import com.fasterxml.jackson.annotation.JsonProperty;

import java.util.Map;

public record ToolAuditEntry(
        int step,
        @JsonProperty("tool_call_id")
        String toolCallId,
        @JsonProperty("tool_name")
        String toolName,
        Map<String, Object> arguments,
        boolean mutating,
        boolean success,
        @JsonProperty("elapsed_seconds")
        double elapsedSeconds,
        @JsonProperty("result_size_chars")
        int resultSizeChars,
        String error
) {
}
