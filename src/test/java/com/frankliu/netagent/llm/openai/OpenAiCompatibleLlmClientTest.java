package com.frankliu.netagent.llm.openai;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.frankliu.netagent.llm.ChatMessage;
import com.frankliu.netagent.llm.LlmResponse;
import com.frankliu.netagent.llm.ToolCall;
import com.frankliu.netagent.mcp.McpTool;
import com.sun.net.httpserver.HttpServer;
import org.junit.jupiter.api.Test;

import java.io.IOException;
import java.net.InetSocketAddress;
import java.net.URI;
import java.net.http.HttpClient;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.concurrent.atomic.AtomicReference;

import static org.assertj.core.api.Assertions.assertThat;

class OpenAiCompatibleLlmClientTest {

    private final ObjectMapper objectMapper = new ObjectMapper().findAndRegisterModules();

    @Test
    void requestPayloadUsesOpenAiCompatibleToolShape() {
        OpenAiCompatibleLlmClient client = client(URI.create("http://localhost/chat/completions"));

        Map<String, Object> payload = client.requestPayload(
                "system",
                List.of(
                        ChatMessage.user("list labs"),
                        ChatMessage.assistant("checking", List.of(new ToolCall("call-0", "get_cml_labs", Map.of()))),
                        ChatMessage.tool("call-0", "[]")
                ),
                List.of(new McpTool("get_cml_labs", "List labs", Map.of("type", "object")))
        );
        JsonNode json = objectMapper.valueToTree(payload);

        assertThat(json.at("/model").asText()).isEqualTo("test-model");
        assertThat(json.at("/messages/0/role").asText()).isEqualTo("system");
        assertThat(json.at("/messages/2/tool_calls/0/type").asText()).isEqualTo("function");
        assertThat(json.at("/messages/2/tool_calls/0/function/name").asText()).isEqualTo("get_cml_labs");
        assertThat(json.at("/messages/3/tool_call_id").asText()).isEqualTo("call-0");
        assertThat(json.at("/tools/0/function/parameters/type").asText()).isEqualTo("object");
    }

    @Test
    void chatParsesToolCallsAndUsageFromLocalServer() throws Exception {
        AtomicReference<String> requestBody = new AtomicReference<>();
        HttpServer server = HttpServer.create(new InetSocketAddress("127.0.0.1", 0), 0);
        server.createContext("/chat/completions", exchange -> {
            requestBody.set(new String(exchange.getRequestBody().readAllBytes(), StandardCharsets.UTF_8));
            byte[] response = """
                    {
                      "choices": [{
                        "finish_reason": "tool_calls",
                        "message": {
                          "content": "checking",
                          "tool_calls": [{
                            "id": "call-1",
                            "type": "function",
                            "function": {
                              "name": "get_cml_labs",
                              "arguments": "{\\"limit\\": 2}"
                            }
                          }]
                        }
                      }],
                      "usage": {
                        "prompt_tokens": 11,
                        "completion_tokens": 7
                      }
                    }
                    """.getBytes(StandardCharsets.UTF_8);
            exchange.getResponseHeaders().add("Content-Type", "application/json");
            exchange.sendResponseHeaders(200, response.length);
            exchange.getResponseBody().write(response);
            exchange.close();
        });
        server.start();
        try {
            URI uri = URI.create("http://127.0.0.1:" + server.getAddress().getPort() + "/chat/completions");
            OpenAiCompatibleLlmClient client = client(uri);

            LlmResponse response = client.chat("system", List.of(ChatMessage.user("list labs")), List.of());

            assertThat(requestBody.get()).contains("\"model\":\"test-model\"");
            assertThat(response.finishReason()).isEqualTo("tool_calls");
            assertThat(response.content()).isEqualTo("checking");
            assertThat(response.promptTokens()).isEqualTo(11);
            assertThat(response.completionTokens()).isEqualTo(7);
            assertThat(response.toolCalls()).hasSize(1);
            assertThat(response.toolCalls().getFirst().name()).isEqualTo("get_cml_labs");
            assertThat(response.toolCalls().getFirst().arguments()).containsEntry("limit", 2);
        } finally {
            server.stop(0);
        }
    }

    private OpenAiCompatibleLlmClient client(URI uri) {
        return new OpenAiCompatibleLlmClient(
                HttpClient.newHttpClient(),
                objectMapper,
                "test-model",
                uri,
                "test-key"
        );
    }
}
