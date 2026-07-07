package com.frankliu.netagent;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.frankliu.netagent.agent.AgentLoop;
import com.frankliu.netagent.agent.SystemPrompts;
import com.frankliu.netagent.artifact.ArtifactFactory;
import com.frankliu.netagent.artifact.RunArtifact;
import com.frankliu.netagent.config.NetagentSettings;
import com.frankliu.netagent.diagnostics.DoctorService;
import com.frankliu.netagent.diagnostics.DoctorService.DoctorResult;
import com.frankliu.netagent.llm.LlmClientFactory;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ScriptedLlmClient;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.logging.RunLog;
import com.frankliu.netagent.logging.RunLogService;
import com.frankliu.netagent.mcp.CmlMcpServerSpec;
import com.frankliu.netagent.mcp.McpTool;
import com.frankliu.netagent.mcp.ScriptedMcpClient;
import com.frankliu.netagent.mcp.SdkCmlMcpClient;
import com.frankliu.netagent.runner.AgentRunResult;
import com.frankliu.netagent.runner.AgentRunService;
import picocli.CommandLine;
import picocli.CommandLine.Command;
import picocli.CommandLine.Model.CommandSpec;
import picocli.CommandLine.Parameters;
import picocli.CommandLine.Spec;

import java.io.IOException;
import java.io.PrintWriter;
import java.math.BigDecimal;
import java.nio.file.Path;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.Callable;

@Command(
        name = "netagent-benchmark",
        mixinStandardHelpOptions = true,
        subcommands = {
                NetagentApplication.ArtifactSmoke.class,
                NetagentApplication.LoopSmoke.class,
                NetagentApplication.LlmSmoke.class,
                NetagentApplication.Run.class,
                NetagentApplication.Doctor.class,
                NetagentApplication.Tools.class,
                NetagentApplication.McpSpec.class
        }
)
public final class NetagentApplication implements Runnable {

    @Spec
    CommandSpec spec;

    public static void main(String[] args) {
        PrintWriter out = new PrintWriter(System.out, true);
        CommandLine commandLine = new CommandLine(new NetagentApplication()).setOut(out).setErr(out);
        int exitCode = commandLine.execute(args);
        out.flush();
        if (exitCode != 0) {
            System.exit(exitCode);
        }
    }

    @Override
    public void run() {
        spec.commandLine().usage(spec.commandLine().getOut());
    }

    @Command(name = "artifact-smoke", description = "Write a workbench-compatible run.json without calling LLM or CML.")
    static final class ArtifactSmoke extends TaskCommand {

        @Override
        public Integer call() throws IOException {
            writeArtifactSmoke(task());
            return 0;
        }
    }

    @Command(name = "loop-smoke", description = "Run the Java agent loop with scripted LLM and MCP clients.")
    static final class LoopSmoke extends TaskCommand {

        @Override
        public Integer call() throws IOException {
            writeLoopSmoke(task());
            return 0;
        }
    }

    @Command(name = "llm-smoke", description = "Run the Java loop with the configured real LLM and no CML tools.")
    static final class LlmSmoke extends TaskCommand {

        @Override
        public Integer call() throws IOException {
            writeLlmSmoke(task());
            return 0;
        }
    }

    @Command(name = "run", description = "Run the Java agent with a real LLM and CML MCP tools.")
    static final class Run extends TaskCommand {

        @Override
        public Integer call() throws IOException {
            runWithCml(task());
            return 0;
        }
    }

    @Command(name = "doctor", description = "Check Java runtime configuration and CML MCP tool discovery.")
    static final class Doctor implements Callable<Integer> {

        @Override
        public Integer call() {
            return runDoctor();
        }
    }

    @Command(name = "tools", description = "Start cml-mcp through the MCP Java SDK and print available tools.")
    static final class Tools implements Callable<Integer> {

        @Override
        public Integer call() {
            printCmlTools();
            return 0;
        }
    }

    @Command(name = "mcp-spec", description = "Print the prepared cml-mcp stdio command without starting it.")
    static final class McpSpec implements Callable<Integer> {

        @Override
        public Integer call() {
            printMcpSpec();
            return 0;
        }
    }

    abstract static class TaskCommand implements Callable<Integer> {
        @Parameters(index = "0..*", arity = "0..*", paramLabel = "TASK")
        private List<String> taskParts = List.of();

        String task() {
            return taskParts.isEmpty() ? "java migration smoke" : String.join(" ", taskParts);
        }
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
                                10
                        ),
                        new LlmResponse(
                                "Done. Found OSPF-Demo and BGP-Lab.",
                                List.of(),
                                "stop",
                                100,
                                30
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
                LlmClientFactory.fromSettings(settings, objectMapper),
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
                LlmClientFactory.fromSettings(settings, objectMapper),
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

    private static int runDoctor() {
        NetagentSettings settings = NetagentSettings.fromEnvironment();
        CmlMcpServerSpec spec = CmlMcpServerSpec.fromSettings(settings);
        DoctorResult result = new DoctorService().check(settings, () -> SdkCmlMcpClient.start(spec));
        System.out.println(String.join("\n", result.messages()));
        return result.exitCode();
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

}
