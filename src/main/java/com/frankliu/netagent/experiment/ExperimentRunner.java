package com.frankliu.netagent.experiment;

import com.frankliu.netagent.agent.AgentLoop;
import com.frankliu.netagent.artifact.ArtifactFactory;
import com.frankliu.netagent.artifact.RunArtifact;
import com.frankliu.netagent.artifact.RunLog;
import com.frankliu.netagent.artifact.RunLogService;
import com.frankliu.netagent.artifact.trace.AgentLoopResult;
import com.frankliu.netagent.ports.llm.LlmClient;
import com.frankliu.netagent.ports.network.NetworkEnvironment;
import com.frankliu.netagent.ports.network.NetworkEnvironmentFactory;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Path;

public class ExperimentRunner {

    private final AgentLoop agentLoop;
    private final RunLogService runLogService;

    public ExperimentRunner(AgentLoop agentLoop, RunLogService runLogService) {
        this.agentLoop = agentLoop;
        this.runLogService = runLogService;
    }

    public ExperimentRun run(
            NetagentSettings settings,
            String task,
            String systemPrompt,
            LlmClient llm,
            NetworkEnvironment environment
    ) throws IOException {
        return runWithEnvironmentFactory(settings, task, systemPrompt, llm, () -> environment, false);
    }

    public ExperimentRun runWithEnvironmentFactory(
            NetagentSettings settings,
            String task,
            String systemPrompt,
            LlmClient llm,
            NetworkEnvironmentFactory environmentFactory
    ) throws IOException {
        return runWithEnvironmentFactory(settings, task, systemPrompt, llm, environmentFactory, true);
    }

    private ExperimentRun runWithEnvironmentFactory(
            NetagentSettings settings,
            String task,
            String systemPrompt,
            LlmClient llm,
            NetworkEnvironmentFactory environmentFactory,
            boolean closeClient
    ) throws IOException {
        RunLog runLog = runLogService.startRunLog(task, settings.runsRoot());
        Path runLogPath = runLog.runDir().resolve("run.json");
        NetworkEnvironment environment = null;
        try {
            environment = environmentFactory.open();
            AgentLoopResult result = agentLoop.run(
                    task,
                    systemPrompt,
                    llm,
                    environment,
                    environment.listTools(),
                    settings.maxTurns()
            );
            RunArtifact artifact = ArtifactFactory.completedFromLoopResult(
                    runLog.runId(),
                    runLog.timestamp(),
                    task,
                    settings.llmProvider(),
                    settings.modelName(),
                    runLogPath,
                    result
            );
            Path path = runLogService.writeRunLog(runLog, artifact);
            return new ExperimentRun(runLog.runId(), path, result.finalAnswer());
        } catch (Exception ex) {
            RunArtifact artifact = ArtifactFactory.failed(
                    runLog.runId(),
                    runLog.timestamp(),
                    task,
                    settings.llmProvider(),
                    settings.modelName(),
                    runLogPath,
                    ex.getClass().getSimpleName() + ": " + ex.getMessage(),
                    BigDecimal.ZERO,
                    ArtifactFactory.ToolAuditCounts.empty()
            );
            Path path = runLogService.writeRunLog(runLog, artifact);
            throw new ExperimentRunException("Agent run failed. Run log written to " + path, ex);
        } finally {
            if (closeClient) {
                closeQuietly(environment);
            }
        }
    }

    private void closeQuietly(NetworkEnvironment environment) {
        if (environment instanceof AutoCloseable closeable) {
            try {
                closeable.close();
            } catch (Exception ignored) {
                // The run artifact is already authoritative; close failures should not mask it.
            }
        }
    }
}
