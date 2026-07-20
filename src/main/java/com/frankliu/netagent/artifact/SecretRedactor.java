package com.frankliu.netagent.artifact;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.util.Locale;
import java.util.Set;

public final class SecretRedactor {

    private static final ObjectMapper MAPPER = new ObjectMapper();
    private static final Set<String> SECRET_FIELD_NAMES = Set.of(
            "openai_api_key",
            "deepseek_api_key",
            "cml_password"
    );
    private static final Set<String> SECRET_MARKERS = Set.of("api_key", "apikey", "password", "secret");

    private SecretRedactor() {
    }

    public static JsonNode sanitize(JsonNode node) {
        if (node == null || node.isNull() || node.isValueNode()) {
            return node;
        }
        if (node.isArray()) {
            ArrayNode clean = MAPPER.createArrayNode();
            node.forEach(item -> clean.add(sanitize(item)));
            return clean;
        }
        ObjectNode clean = MAPPER.createObjectNode();
        node.properties().forEach(entry -> {
            if (!isSecretField(entry.getKey())) {
                clean.set(entry.getKey(), sanitize(entry.getValue()));
            }
        });
        return clean;
    }

    static boolean isSecretField(String fieldName) {
        String normalized = fieldName.toLowerCase(Locale.ROOT);
        return SECRET_FIELD_NAMES.contains(normalized)
                || "token".equals(normalized)
                || normalized.endsWith("_token")
                || normalized.startsWith("token_")
                || SECRET_MARKERS.stream().anyMatch(normalized::contains);
    }
}
