package com.frankliu.netagent.llm.anthropic;

import com.anthropic.client.AnthropicClient;
import com.anthropic.client.okhttp.AnthropicOkHttpClient;
import com.anthropic.core.JsonValue;
import com.anthropic.models.messages.*;
import com.frankliu.netagent.config.NetagentSettings;
import com.frankliu.netagent.llm.ChatMessage;
import com.frankliu.netagent.llm.LlmClient;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.mcp.McpTool;

import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;
public class AnthropicLlmClient implements LlmClient {
    private static final long MAX_TOKENS = 4096L;
    private final AnthropicClient client;
    private final String model;
    public AnthropicLlmClient(AnthropicClient client, String model) {
        this.client = client;
        this.model = model;
    }
    public static AnthropicLlmClient fromSettings(NetagentSettings settings) {
        return new AnthropicLlmClient(AnthropicOkHttpClient.builder()
                .apiKey(settings.providerApiKey()).baseUrl(settings.providerBaseUrl()).build(), settings.modelName());
    }
    @Override
    public LlmResponse chat(String systemPrompt, List<ChatMessage> messages, List<McpTool> tools) {
        MessageCreateParams.Builder params = MessageCreateParams.builder()
                .model(model)
                .maxTokens(MAX_TOKENS)
                .system(systemPrompt);
        messages.forEach(message -> addMessage(params, message));
        tools.stream().map(this::tool).forEach(params::addTool);

        Message message = client.messages().create(params.build());
        Usage usage = message.usage();
        return new LlmResponse(
                text(message.content()),
                toolCalls(message.content()),
                message.stopReason().map(reason -> reason.asString()).orElse("unknown"),
                Math.toIntExact(usage.inputTokens()),
                Math.toIntExact(usage.outputTokens())
        );
    }
    private void addMessage(MessageCreateParams.Builder params, ChatMessage message) {
        switch (message.role()) {
            case "user" -> params.addUserMessage(message.content());
            case "assistant" -> params.addMessage(message(MessageParam.Role.ASSISTANT, assistantBlocks(message)));
            case "tool" -> params.addMessage(message(MessageParam.Role.USER, List.of(toolResult(message))));
            default -> throw new IllegalArgumentException("Unsupported chat role: " + message.role());
        }
    }
    private MessageParam message(MessageParam.Role role, List<ContentBlockParam> blocks) {
        return MessageParam.builder().role(role).contentOfBlockParams(blocks).build();
    }
    private List<ContentBlockParam> assistantBlocks(ChatMessage message) {
        List<ContentBlockParam> blocks = new ArrayList<>();
        if (message.content() != null && !message.content().isBlank()) {
            blocks.add(ContentBlockParam.ofText(TextBlockParam.builder().text(message.content()).build()));
        }
        message.toolCalls().stream()
                .map(toolCall -> ContentBlockParam.ofToolUse(ToolUseBlockParam.builder()
                        .id(toolCall.id())
                        .name(toolCall.name())
                        .input(input(toolCall.arguments()))
                        .build()))
                .forEach(blocks::add);
        return blocks;
    }
    private ContentBlockParam toolResult(ChatMessage message) {
        return ContentBlockParam.ofToolResult(ToolResultBlockParam.builder()
                .toolUseId(message.toolCallId())
                .content(message.content())
                .build());
    }
    private Tool tool(McpTool tool) {
        return Tool.builder()
                .name(tool.name())
                .description(tool.description())
                .inputSchema(schema(tool.inputSchema()))
                .build();
    }
    private Tool.InputSchema schema(Map<String, Object> schema) {
        return Tool.InputSchema.builder()
                .type(JsonValue.from(schema.getOrDefault("type", "object")))
                .putAllAdditionalProperties(jsonProperties(schema, "type"))
                .build();
    }
    private ToolUseBlockParam.Input input(Map<String, Object> arguments) {
        return ToolUseBlockParam.Input.builder().putAllAdditionalProperties(jsonProperties(arguments)).build();
    }
    private List<ToolCall> toolCalls(List<ContentBlock> blocks) {
        return blocks.stream()
                .filter(ContentBlock::isToolUse)
                .map(ContentBlock::asToolUse)
                .map(toolUse -> new ToolCall(toolUse.id(), toolUse.name(), arguments(toolUse)))
                .toList();
    }
    private Map<String, Object> arguments(ToolUseBlock toolUse) {
        return toolUse._input().convert(Map.class);
    }
    private String text(List<ContentBlock> blocks) {
        return blocks.stream()
                .filter(ContentBlock::isText)
                .map(block -> block.asText().text())
                .collect(Collectors.joining("\n"));
    }
    private Map<String, JsonValue> jsonProperties(Map<String, Object> values, String... ignoredKeys) {
        List<String> ignored = List.of(ignoredKeys);
        return values.entrySet().stream().filter(entry -> !ignored.contains(entry.getKey()))
                .collect(Collectors.toMap(Map.Entry::getKey, entry -> JsonValue.from(entry.getValue())));
    }
}
