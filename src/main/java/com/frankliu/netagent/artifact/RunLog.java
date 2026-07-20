package com.frankliu.netagent.artifact;

import java.nio.file.Path;
import java.time.Instant;

public record RunLog(String runId, Path runDir, Instant timestamp) {
}
