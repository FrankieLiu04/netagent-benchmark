package com.frankliu.netagent.llm.openai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.core.type.TypeReference;
import com.frankliu.netagent.config.NetagentSettings;
import com.frankliu.netagent.llm.ChatMessage;
import com.frankliu.netagent.llm.LlmClient;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.mcp.McpTool;

import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.util.ArrayList;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

public class OpenAiCompatibleLlmClient implements LlmClient {

    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };

    private final HttpClient httpClient;
    private final ObjectMapper objectMapper;
    private final String model;
    private final URI completionsUri;
    private final String apiKey;

    public OpenAiCompatibleLlmClient(
            HttpClient httpClient,
            ObjectMapper objectMapper,
            String model,
            URI completionsUri,
            String apiKey
    ) {
        this.httpClient = httpClient;
        this.objectMapper = objectMapper;
        this.model = model;
        this.completionsUri = completionsUri;
        this.apiKey = apiKey;
    }

    public static OpenAiCompatibleLlmClient fromSettings(NetagentSettings settings, ObjectMapper objectMapper) {
        return new OpenAiCompatibleLlmClient(
                HttpClient.newHttpClient(),
                objectMapper,
                settings.modelName(),
                chatCompletionsUri(settings.providerBaseUrl()),
                settings.providerApiKey()
        );
    }

    @Override
    public LlmResponse chat(String systemPrompt, List<ChatMessage> messages, List<McpTool> tools) {
        try {
            JsonNode requestBody = objectMapper.valueToTree(requestPayload(systemPrompt, messages, tools));
            HttpRequest request = HttpRequest.newBuilder(completionsUri)
                    .header("Authorization", "Bearer " + apiKey)
                    .header("Content-Type", "application/json")
                    .POST(HttpRequest.BodyPublishers.ofString(objectMapper.writeValueAsString(requestBody)))
                    .build();
            HttpResponse<String> response = httpClient.send(request, HttpResponse.BodyHandlers.ofString());
            if (response.statusCode() / 100 != 2) {
                throw new IllegalStateException("LLM request failed with HTTP " + response.statusCode());
            }
            return parseResponse(objectMapper.readTree(response.body()));
        } catch (IOException ex) {
            throw new IllegalStateException("LLM request failed: " + ex.getMessage(), ex);
        } catch (InterruptedException ex) {
            Thread.currentThread().interrupt();
            throw new IllegalStateException("LLM request interrupted", ex);
        }
    }

    Map<String, Object> requestPayload(String systemPrompt, List<ChatMessage> messages, List<McpTool> tools) {
        Map<String, Object> payload = new LinkedHashMap<>();
        payload.put("model", model);
        payload.put("messages", openAiMessages(systemPrompt, messages));
        if (!tools.isEmpty()) {
            payload.put("tools", openAiTools(tools));
        }
        return payload;
    }

    LlmResponse parseResponse(JsonNode root) {
        JsonNode choice = root.path("choices").path(0);
        JsonNode message = choice.path("message");
        JsonNode usage = root.path("usage");
        return new LlmResponse(
                textOrNull(message.path("content")),
                parseToolCalls(message.path("tool_calls")),
                choice.path("finish_reason").asText("unknown"),
                usage.path("prompt_tokens").asInt(0),
                usage.path("completion_tokens").asInt(0),
                objectMapper.convertValue(message, MAP_TYPE)
        );
    }

    private List<Map<String, Object>> openAiMessages(String systemPrompt, List<ChatMessage> messages) {
        List<Map<String, Object>> converted = new ArrayList<>();
        converted.add(Map.of("role", "system", "content", systemPrompt));
        for (ChatMessage message : messages) {
            converted.add(openAiMessage(message));
        }
        return converted;
    }

    private Map<String, Object> openAiMessage(ChatMessage message) {
        Map<String, Object> converted = new LinkedHashMap<>();
        converted.put("role", message.role());
        converted.put("content", message.content());
        if ("tool".equals(message.role())) {
            converted.put("tool_call_id", message.toolCallId());
        }
        if ("assistant".equals(message.role()) && !message.toolCalls().isEmpty()) {
            converted.put("tool_calls", message.toolCalls().stream().map(this::openAiToolCall).toList());
        }
        return converted;
    }

    private Map<String, Object> openAiToolCall(ToolCall toolCall) {
        return Map.of(
                "id", toolCall.id(),
                "type", "function",
                "function", Map.of(
                        "name", toolCall.name(),
                        "arguments", jsonString(toolCall.arguments())
                )
        );
    }

    private List<Map<String, Object>> openAiTools(List<McpTool> tools) {
        return tools.stream()
                .map(tool -> Map.<String, Object>of(
                        "type", "function",
                        "function", Map.of(
                                "name", tool.name(),
                                "description", tool.description(),
                                "parameters", tool.inputSchema()
                        )
                ))
                .toList();
    }

    private List<ToolCall> parseToolCalls(JsonNode toolCallsNode) {
        if (!toolCallsNode.isArray()) {
            return List.of();
        }
        List<ToolCall> toolCalls = new ArrayList<>();
        for (JsonNode node : toolCallsNode) {
            JsonNode function = node.path("function");
            toolCalls.add(new ToolCall(
                    node.path("id").asText(),
                    function.path("name").asText(),
                    parseArguments(function.path("arguments").asText("{}"))
            ));
        }
        return toolCalls;
    }

    private Map<String, Object> parseArguments(String rawArguments) {
        try {
            return objectMapper.convertValue(objectMapper.readTree(rawArguments), MAP_TYPE);
        } catch (IOException ex) {
            return Map.of();
        }
    }

    private String jsonString(Map<String, Object> value) {
        try {
            return objectMapper.writeValueAsString(value);
        } catch (IOException ex) {
            throw new IllegalArgumentException("Tool arguments are not JSON serializable", ex);
        }
    }

    private static URI chatCompletionsUri(String baseUrl) {
        String normalized = baseUrl.endsWith("/") ? baseUrl.substring(0, baseUrl.length() - 1) : baseUrl;
        return URI.create(normalized + "/chat/completions");
    }

    private static String textOrNull(JsonNode node) {
        return node == null || node.isMissingNode() || node.isNull() ? null : node.asText();
    }
}
