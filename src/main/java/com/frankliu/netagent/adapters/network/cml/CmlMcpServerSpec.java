package com.frankliu.netagent.adapters.network.cml;

import com.frankliu.netagent.experiment.NetagentSettings;

import java.time.Duration;
import java.util.List;
import java.util.Map;

public record CmlMcpServerSpec(
        String command,
        List<String> args,
        Map<String, String> environment,
        Duration requestTimeout
) {
    public static CmlMcpServerSpec fromSettings(NetagentSettings settings) {
        return new CmlMcpServerSpec(
                settings.cmlMcpCommand(),
                settings.cmlMcpArgs(),
                settings.cmlEnvironment(),
                settings.mcpTimeout()
        );
    }
}
