package com.frankliu.netagent;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.frankliu.netagent.agent.AgentLoop;
import com.frankliu.netagent.agent.SystemPrompts;
import com.frankliu.netagent.artifact.ArtifactFactory;
import com.frankliu.netagent.artifact.RunArtifact;
import com.frankliu.netagent.config.NetagentSettings;
import com.frankliu.netagent.diagnostics.DoctorService;
import com.frankliu.netagent.diagnostics.DoctorService.DoctorResult;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ScriptedLlmClient;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.llm.openai.OpenAiCompatibleLlmClient;
import com.frankliu.netagent.logging.RunLog;
import com.frankliu.netagent.logging.RunLogService;
import com.frankliu.netagent.mcp.McpTool;
import com.frankliu.netagent.mcp.CmlMcpServerSpec;
import com.frankliu.netagent.mcp.ScriptedMcpClient;
import com.frankliu.netagent.mcp.SdkCmlMcpClient;
import com.frankliu.netagent.runner.AgentRunResult;
import com.frankliu.netagent.runner.AgentRunService;

import java.io.IOException;
import java.math.BigDecimal;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public final class NetagentApplication {

    private NetagentApplication() {
    }

    public static void main(String[] args) throws IOException {
        if (args.length == 0 || "--help".equals(args[0]) || "-h".equals(args[0])) {
            printUsage();
            return;
        }
        String command = args[0];
        String task = args.length > 1 ? String.join(" ", java.util.Arrays.copyOfRange(args, 1, args.length)) : "java migration smoke";
        if ("artifact-smoke".equals(command)) {
            writeArtifactSmoke(task);
            return;
        }
        if ("loop-smoke".equals(command)) {
            writeLoopSmoke(task);
            return;
        }
        if ("llm-smoke".equals(command)) {
            writeLlmSmoke(task);
            return;
        }
        if ("run".equals(command)) {
            runWithCml(task);
            return;
        }
        if ("doctor".equals(command)) {
            runDoctor();
            return;
        }
        if ("mcp-spec".equals(command)) {
            printMcpSpec();
            return;
        }
        if ("tools".equals(command)) {
            printCmlTools();
            return;
        }
        throw new IllegalArgumentException("Unknown command: " + command);
    }

    private static void writeArtifactSmoke(String task) throws IOException {
        RunLogService runLogService = new RunLogService(new ObjectMapper());
        RunLog runLog = runLogService.startRunLog(task, Path.of("experiments", "runs"));
        RunArtifact artifact = ArtifactFactory.completed(
                runLog.runId(),
                runLog.timestamp(),
                task,
                "java-migration",
                "artifact-smoke",
                runLog.runDir().resolve("run.json"),
                "Java migration smoke artifact.",
                BigDecimal.ZERO,
                0,
                0,
                ArtifactFactory.ToolAuditSummary.empty()
        );
        Path path = runLogService.writeRunLog(runLog, artifact);
        System.out.println(path);
    }

    private static void writeLoopSmoke(String task) throws IOException {
        RunLogService runLogService = new RunLogService(new ObjectMapper());
        Map<String, String> smokeEnv = new LinkedHashMap<>(System.getenv());
        smokeEnv.put("LLM_PROVIDER", "java-migration");
        smokeEnv.put("LLM_MODEL", "loop-smoke");
        NetagentSettings settings = NetagentSettings.fromMap(smokeEnv);
        McpTool labsTool = new McpTool("get_cml_labs", "List CML labs", Map.of("type", "object", "properties", Map.of()));
        AgentRunResult result = new AgentRunService(new AgentLoop(), runLogService).run(
                settings,
                task,
                "You are a network engineering agent.",
                new ScriptedLlmClient(List.of(
                        new LlmResponse(
                                "Checking CML labs.",
                                List.of(new ToolCall("call-0", "get_cml_labs", Map.of())),
                                "tool_calls",
                                50,
                                10,
                                null
                        ),
                        new LlmResponse(
                                "Done. Found OSPF-Demo and BGP-Lab.",
                                List.of(),
                                "stop",
                                100,
                                30,
                                null
                        )
                )),
                new ScriptedMcpClient(Map.of("get_cml_labs", "[\"OSPF-Demo\", \"BGP-Lab\"]"), List.of(labsTool))
        );
        System.out.println(result.runLogPath());
    }

    private static void writeLlmSmoke(String task) throws IOException {
        ObjectMapper objectMapper = new ObjectMapper();
        RunLogService runLogService = new RunLogService(objectMapper);
        NetagentSettings settings = NetagentSettings.fromEnvironment();
        AgentRunResult result = new AgentRunService(new AgentLoop(), runLogService).run(
                settings,
                task,
                SystemPrompts.fullAccess(),
                OpenAiCompatibleLlmClient.fromSettings(settings, objectMapper),
                new ScriptedMcpClient(Map.of(), List.of())
        );
        System.out.println(result.runLogPath());
    }

    private static void runWithCml(String task) throws IOException {
        ObjectMapper objectMapper = new ObjectMapper();
        RunLogService runLogService = new RunLogService(objectMapper);
        NetagentSettings settings = NetagentSettings.fromEnvironment();
        CmlMcpServerSpec mcpSpec = CmlMcpServerSpec.fromSettings(settings);
        AgentRunResult result = new AgentRunService(new AgentLoop(), runLogService).runWithMcpFactory(
                settings,
                task,
                SystemPrompts.fullAccess(),
                OpenAiCompatibleLlmClient.fromSettings(settings, objectMapper),
                () -> SdkCmlMcpClient.start(mcpSpec)
        );
        System.out.println(result.finalAnswer());
        System.out.println();
        System.out.println("Run log: " + result.runLogPath());
    }

    private static void printMcpSpec() {
        CmlMcpServerSpec spec = CmlMcpServerSpec.fromSettings(NetagentSettings.fromEnvironment());
        System.out.println(spec.command() + " " + String.join(" ", spec.args()));
        System.out.println("timeout=" + spec.requestTimeout());
        System.out.println("envKeys=" + spec.environment().keySet());
    }

    private static void runDoctor() {
        NetagentSettings settings = NetagentSettings.fromEnvironment();
        CmlMcpServerSpec spec = CmlMcpServerSpec.fromSettings(settings);
        DoctorResult result = new DoctorService().check(settings, () -> SdkCmlMcpClient.start(spec));
        System.out.println(String.join("\n", result.messages()));
        if (result.exitCode() != 0) {
            System.exit(result.exitCode());
        }
    }

    private static void printCmlTools() {
        CmlMcpServerSpec spec = CmlMcpServerSpec.fromSettings(NetagentSettings.fromEnvironment());
        try (SdkCmlMcpClient client = SdkCmlMcpClient.start(spec)) {
            client.listTools().stream()
                    .map(McpTool::name)
                    .sorted()
                    .forEach(System.out::println);
        }
    }

    private static void printUsage() {
        System.out.println("""
                Usage:
                  java -jar netagent-benchmark.jar artifact-smoke "list all CML labs"
                  java -jar netagent-benchmark.jar loop-smoke "list all CML labs"
                  java -jar netagent-benchmark.jar llm-smoke "summarize OSPF in one sentence"
                  java -jar netagent-benchmark.jar run "list all CML labs"
                  java -jar netagent-benchmark.jar doctor
                  java -jar netagent-benchmark.jar tools
                  java -jar netagent-benchmark.jar mcp-spec

                Commands:
                  artifact-smoke   Write a workbench-compatible run.json without calling LLM or CML.
                  loop-smoke       Run the Java agent loop with scripted LLM and MCP clients.
                  llm-smoke        Run the Java loop with a real OpenAI-compatible LLM and no CML tools.
                  run              Run the Java agent with a real LLM and CML MCP tools.
                  doctor           Check Java runtime configuration and CML MCP tool discovery.
                  tools            Start cml-mcp through the MCP Java SDK and print available tools.
                  mcp-spec         Print the prepared cml-mcp stdio command without starting it.
                """);
    }
}
