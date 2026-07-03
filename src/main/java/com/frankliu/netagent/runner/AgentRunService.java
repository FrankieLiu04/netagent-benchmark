package com.frankliu.netagent.runner;

import com.frankliu.netagent.agent.AgentLoop;
import com.frankliu.netagent.artifact.ArtifactFactory;
import com.frankliu.netagent.artifact.RunArtifact;
import com.frankliu.netagent.config.NetagentSettings;
import com.frankliu.netagent.llm.LlmClient;
import com.frankliu.netagent.logging.RunLog;
import com.frankliu.netagent.logging.RunLogService;
import com.frankliu.netagent.mcp.CmlMcpClient;
import com.frankliu.netagent.mcp.CmlMcpClientFactory;
import com.frankliu.netagent.trace.AgentLoopResult;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Path;

public class AgentRunService {

    private final AgentLoop agentLoop;
    private final RunLogService runLogService;

    public AgentRunService(AgentLoop agentLoop, RunLogService runLogService) {
        this.agentLoop = agentLoop;
        this.runLogService = runLogService;
    }

    public AgentRunResult run(
            NetagentSettings settings,
            String task,
            String systemPrompt,
            LlmClient llm,
            CmlMcpClient mcp
    ) throws IOException {
        return runWithMcpFactory(settings, task, systemPrompt, llm, () -> mcp, false);
    }

    public AgentRunResult runWithMcpFactory(
            NetagentSettings settings,
            String task,
            String systemPrompt,
            LlmClient llm,
            CmlMcpClientFactory mcpFactory
    ) throws IOException {
        return runWithMcpFactory(settings, task, systemPrompt, llm, mcpFactory, true);
    }

    private AgentRunResult runWithMcpFactory(
            NetagentSettings settings,
            String task,
            String systemPrompt,
            LlmClient llm,
            CmlMcpClientFactory mcpFactory,
            boolean closeClient
    ) throws IOException {
        RunLog runLog = runLogService.startRunLog(task, settings.runsRoot());
        Path runLogPath = runLog.runDir().resolve("run.json");
        CmlMcpClient mcp = null;
        try {
            mcp = mcpFactory.open();
            AgentLoopResult result = agentLoop.run(
                    task,
                    systemPrompt,
                    llm,
                    mcp,
                    mcp.listTools(),
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
            artifact = ArtifactFactory.withWorkbenchIds(
                    artifact,
                    settings.workbenchExperimentId(),
                    settings.workbenchAgentConfigId()
            );
            Path path = runLogService.writeRunLog(runLog, artifact);
            return new AgentRunResult(runLog.runId(), path, result.finalAnswer());
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
                    ArtifactFactory.ToolAuditSummary.empty()
            );
            artifact = ArtifactFactory.withWorkbenchIds(
                    artifact,
                    settings.workbenchExperimentId(),
                    settings.workbenchAgentConfigId()
            );
            Path path = runLogService.writeRunLog(runLog, artifact);
            throw new AgentRunServiceException("Agent run failed. Run log written to " + path, ex);
        } finally {
            if (closeClient) {
                closeQuietly(mcp);
            }
        }
    }

    private void closeQuietly(CmlMcpClient mcp) {
        if (mcp instanceof AutoCloseable closeable) {
            try {
                closeable.close();
            } catch (Exception ignored) {
                // The run artifact is already authoritative; close failures should not mask it.
            }
        }
    }
}
