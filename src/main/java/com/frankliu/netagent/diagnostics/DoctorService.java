package com.frankliu.netagent.diagnostics;

import com.frankliu.netagent.config.NetagentSettings;
import com.frankliu.netagent.mcp.CmlMcpClient;
import com.frankliu.netagent.mcp.CmlMcpClientFactory;
import com.frankliu.netagent.mcp.McpTool;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class DoctorService {

    public DoctorResult check(NetagentSettings settings, CmlMcpClientFactory mcpFactory) {
        List<String> messages = new ArrayList<>();
        messages.add("OK: loaded Java runtime configuration");

        String keyName = providerKeyName(settings);
        if (settings.providerApiKey().isBlank()) {
            messages.add("FAIL: " + keyName + " is missing");
            return new DoctorResult(1, List.copyOf(messages));
        }
        messages.add("OK: " + keyName + " is set");
        messages.add("OK: using " + settings.llmProvider() + " model " + settings.modelName());

        CmlMcpClient client = null;
        try {
            client = mcpFactory.open();
            List<String> toolNames = client.listTools().stream()
                    .map(McpTool::name)
                    .sorted(Comparator.naturalOrder())
                    .toList();
            messages.add("OK: CML MCP server started and exposed " + toolNames.size() + " tools");
            toolNames.forEach(tool -> messages.add("  - " + tool));
            return new DoctorResult(0, List.copyOf(messages));
        } catch (Exception ex) {
            messages.add("FAIL: could not start or query CML MCP server: "
                    + ex.getClass().getSimpleName() + ": " + ex.getMessage());
            return new DoctorResult(1, List.copyOf(messages));
        } finally {
            closeQuietly(client);
        }
    }

    private void closeQuietly(CmlMcpClient client) {
        if (client instanceof AutoCloseable closeable) {
            try {
                closeable.close();
            } catch (Exception ignored) {
                // Diagnostics are based on startup and tool discovery; close errors add little signal.
            }
        }
    }

    private String providerKeyName(NetagentSettings settings) {
        if ("openai".equalsIgnoreCase(settings.llmProvider())) {
            return "OPENAI_API_KEY";
        }
        return "DEEPSEEK_API_KEY";
    }

    public record DoctorResult(int exitCode, List<String> messages) {
    }
}
