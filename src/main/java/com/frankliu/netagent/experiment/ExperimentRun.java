package com.frankliu.netagent.experiment;

import java.nio.file.Path;

public record ExperimentRun(
        String runId,
        Path runLogPath,
        String finalAnswer
) {
}
