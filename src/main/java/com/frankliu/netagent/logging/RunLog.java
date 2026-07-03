package com.frankliu.netagent.logging;

import java.nio.file.Path;
import java.time.Instant;

public record RunLog(String runId, Path runDir, Instant timestamp) {
}
