package com.frankliu.netagent.runner;

import java.nio.file.Path;

public record AgentRunResult(
        String runId,
        Path runLogPath,
        String finalAnswer
) {
}
