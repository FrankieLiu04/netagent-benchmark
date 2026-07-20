package com.frankliu.netagent.experiment;

import java.nio.file.Path;
import java.time.Duration;
import java.util.Arrays;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public record NetagentSettings(
        String llmProvider,
        String modelName,
        String providerBaseUrl,
        String providerApiKey,
        String cmlUrl,
        String cmlUsername,
        String cmlPassword,
        boolean cmlVerifySsl,
        String cmlMcpCommand,
        List<String> cmlMcpArgs,
        int maxTurns,
        Duration mcpTimeout,
        Path runsRoot
) {
    public static NetagentSettings fromEnvironment() {
        return fromMap(System.getenv());
    }

    public static NetagentSettings fromMap(Map<String, String> env) {
        String provider = value(env, "LLM_PROVIDER", "deepseek");
        return new NetagentSettings(
                provider,
                value(env, "LLM_MODEL", defaultModel(provider)),
                providerBaseUrl(env, provider),
                providerApiKey(env, provider),
                env.getOrDefault("CML_URL", ""),
                env.getOrDefault("CML_USERNAME", ""),
                env.getOrDefault("CML_PASSWORD", ""),
                Boolean.parseBoolean(value(env, "CML_VERIFY_SSL", "false")),
                value(env, "NETAGENT_CML_MCP_COMMAND", "python"),
                listValue(env, "NETAGENT_CML_MCP_ARGS", List.of("-m", "cml_mcp")),
                intValue(env, "NETAGENT_MAX_TURNS", 20),
                Duration.ofSeconds(intValue(env, "NETAGENT_MCP_TIMEOUT_SECONDS", 30)),
                Path.of(value(env, "NETAGENT_RUNS_ROOT", "experiments/runs"))
        );
    }

    public Map<String, String> cmlEnvironment() {
        Map<String, String> env = new LinkedHashMap<>();
        env.put("CML_URL", cmlUrl);
        env.put("CML_USERNAME", cmlUsername);
        env.put("CML_PASSWORD", cmlPassword);
        env.put("CML_VERIFY_SSL", Boolean.toString(cmlVerifySsl));
        env.put("NETAGENT_MCP_TIMEOUT_SECONDS", Long.toString(mcpTimeout.toSeconds()));
        return env;
    }

    private static String providerBaseUrl(Map<String, String> env, String provider) {
        if ("openai".equalsIgnoreCase(provider)) {
            return env.getOrDefault("OPENAI_BASE_URL", "https://api.openai.com/v1");
        }
        return env.getOrDefault("DEEPSEEK_BASE_URL", "https://api.deepseek.com");
    }

    private static String providerApiKey(Map<String, String> env, String provider) {
        if ("openai".equalsIgnoreCase(provider)) {
            return env.getOrDefault("OPENAI_API_KEY", "");
        }
        return env.getOrDefault("DEEPSEEK_API_KEY", "");
    }

    private static String defaultModel(String provider) {
        return "deepseek-v4-flash";
    }

    private static String value(Map<String, String> env, String key, String fallback) {
        String value = env.get(key);
        return value == null || value.isBlank() ? fallback : value;
    }

    private static int intValue(Map<String, String> env, String key, int fallback) {
        String value = env.get(key);
        if (value == null || value.isBlank()) {
            return fallback;
        }
        return Integer.parseInt(value);
    }

    private static List<String> listValue(Map<String, String> env, String key, List<String> fallback) {
        String value = env.get(key);
        if (value == null || value.isBlank()) {
            return fallback;
        }
        return Arrays.stream(value.split(","))
                .map(String::strip)
                .filter(part -> !part.isEmpty())
                .toList();
    }
}
