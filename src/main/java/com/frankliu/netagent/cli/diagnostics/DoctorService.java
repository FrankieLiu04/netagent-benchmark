package com.frankliu.netagent.cli.diagnostics;

import com.frankliu.netagent.experiment.NetagentSettings;
import com.frankliu.netagent.ports.network.NetworkEnvironment;
import com.frankliu.netagent.ports.network.NetworkEnvironmentFactory;
import com.frankliu.netagent.ports.network.NetworkTool;

import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public class DoctorService {

    public DoctorResult check(NetagentSettings settings, NetworkEnvironmentFactory environmentFactory) {
        List<String> messages = new ArrayList<>();
        messages.add("OK: loaded Java runtime configuration");

        String keyName = providerKeyName(settings);
        if (settings.providerApiKey().isBlank()) {
            messages.add("FAIL: " + keyName + " is missing");
            return new DoctorResult(1, List.copyOf(messages));
        }
        messages.add("OK: " + keyName + " is set");
        messages.add("OK: using " + settings.llmProvider() + " model " + settings.modelName());

        NetworkEnvironment environment = null;
        try {
            environment = environmentFactory.open();
            List<String> toolNames = environment.listTools().stream()
                    .map(NetworkTool::name)
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
            closeQuietly(environment);
        }
    }

    private void closeQuietly(NetworkEnvironment environment) {
        if (environment instanceof AutoCloseable closeable) {
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
