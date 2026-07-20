package com.frankliu.netagent.adapters.llm.openai;

import com.fasterxml.jackson.core.type.TypeReference;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.frankliu.netagent.experiment.NetagentSettings;
import com.frankliu.netagent.ports.llm.ChatMessage;
import com.frankliu.netagent.ports.llm.LlmClient;
import com.frankliu.netagent.ports.llm.LlmResponse;
import com.frankliu.netagent.ports.llm.ToolCall;
import com.frankliu.netagent.ports.network.NetworkTool;
import com.openai.client.OpenAIClient;
import com.openai.client.okhttp.OpenAIOkHttpClient;
import com.openai.core.JsonValue;
import com.openai.models.FunctionDefinition;
import com.openai.models.FunctionParameters;
import com.openai.models.chat.completions.*;
import com.openai.models.completions.CompletionUsage;

import java.io.IOException;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
public class OpenAiChatLlmClient implements LlmClient {
    private static final TypeReference<Map<String, Object>> MAP_TYPE = new TypeReference<>() {
    };
    private final OpenAIClient client;
    private final ObjectMapper objectMapper;
    private final String model;
    public OpenAiChatLlmClient(OpenAIClient client, ObjectMapper objectMapper, String model) {
        this.client = client;
        this.objectMapper = objectMapper;
        this.model = model;
    }
    public static OpenAiChatLlmClient fromSettings(NetagentSettings settings, ObjectMapper objectMapper) {
        return new OpenAiChatLlmClient(OpenAIOkHttpClient.builder()
                .apiKey(settings.providerApiKey()).baseUrl(settings.providerBaseUrl()).build(), objectMapper, settings.modelName());
    }
    @Override
    public LlmResponse chat(String systemPrompt, List<ChatMessage> messages, List<NetworkTool> tools) {
        ChatCompletionCreateParams.Builder params = ChatCompletionCreateParams.builder()
                .model(model)
                .addSystemMessage(systemPrompt);
        messages.forEach(message -> addMessage(params, message));
        tools.stream().map(this::tool).forEach(params::addTool);

        ChatCompletion completion = client.chat().completions().create(params.build());
        ChatCompletion.Choice choice = completion.choices().getFirst();
        ChatCompletionMessage message = choice.message();
        CompletionUsage usage = completion.usage().orElse(null);
        return new LlmResponse(
                message.content().orElse(null),
                toolCalls(message),
                choice.finishReason().asString(),
                usage == null ? 0 : Math.toIntExact(usage.promptTokens()),
                usage == null ? 0 : Math.toIntExact(usage.completionTokens())
        );
    }
    private void addMessage(ChatCompletionCreateParams.Builder params, ChatMessage message) {
        switch (message.role()) {
            case "user" -> params.addUserMessage(message.content());
            case "assistant" -> params.addMessage(assistantMessage(message));
            case "tool" -> params.addMessage(ChatCompletionToolMessageParam.builder().toolCallId(message.toolCallId()).content(message.content()).build());
            default -> throw new IllegalArgumentException("Unsupported chat role: " + message.role());
        }
    }
    private ChatCompletionAssistantMessageParam assistantMessage(ChatMessage message) {
        ChatCompletionAssistantMessageParam.Builder builder = ChatCompletionAssistantMessageParam.builder();
        if (message.content() != null) {
            builder.content(message.content());
        }
        message.toolCalls().stream().map(this::sdkToolCall).forEach(builder::addToolCall);
        return builder.build();
    }
    private ChatCompletionFunctionTool tool(NetworkTool tool) {
        FunctionDefinition definition = FunctionDefinition.builder()
                .name(tool.name())
                .description(tool.description())
                .parameters(parameters(tool.inputSchema()))
                .build();
        return ChatCompletionFunctionTool.builder().function(definition).build();
    }
    private FunctionParameters parameters(Map<String, Object> schema) {
        return FunctionParameters.builder().putAllAdditionalProperties(jsonProperties(schema)).build();
    }
    private List<ToolCall> toolCalls(ChatCompletionMessage message) {
        return message.toolCalls().orElse(List.of()).stream()
                .filter(call -> call.isFunction())
                .map(call -> {
                    ChatCompletionMessageFunctionToolCall functionCall = call.asFunction();
                    ChatCompletionMessageFunctionToolCall.Function function = functionCall.function();
                    return new ToolCall(functionCall.id(), function.name(), parseArguments(function.arguments()));
                })
                .toList();
    }
    private ChatCompletionMessageFunctionToolCall sdkToolCall(ToolCall toolCall) {
        ChatCompletionMessageFunctionToolCall.Function function = ChatCompletionMessageFunctionToolCall.Function.builder()
                .name(toolCall.name())
                .arguments(jsonString(toolCall.arguments()))
                .build();
        return ChatCompletionMessageFunctionToolCall.builder()
                .id(toolCall.id())
                .function(function)
                .build();
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
    private Map<String, JsonValue> jsonProperties(Map<String, Object> values) {
        return values.entrySet().stream().collect(Collectors.toMap(Map.Entry::getKey, entry -> JsonValue.from(entry.getValue())));
    }
}
