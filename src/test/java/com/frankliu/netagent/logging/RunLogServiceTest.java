package com.frankliu.netagent.logging;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.io.TempDir;

import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class RunLogServiceTest {

    private final ObjectMapper objectMapper = new ObjectMapper()
            .findAndRegisterModules()
            .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    private final RunLogService runLogService = new RunLogService(objectMapper);

    @TempDir
    Path tempDir;

    @Test
    void writeRunLogRedactsSecretFields() throws Exception {
        RunLog runLog = runLogService.startRunLog("Configure CML password", tempDir);

        Path path = runLogService.writeRunLog(runLog, Map.of(
                "task", "safe",
                "cml_password", "secret",
                "nested", Map.of("api_key", "secret", "visible", "ok")
        ));

        JsonNode json = objectMapper.readTree(Files.readString(path));
        assertThat(json.has("cml_password")).isFalse();
        assertThat(json.at("/nested").has("api_key")).isFalse();
        assertThat(json.at("/nested/visible").asText()).isEqualTo("ok");
    }

    @Test
    void makeSlugKeepsCompactFilesystemFriendlyName() {
        assertThat(RunLogService.makeSlug("List all CML labs!!!")).isEqualTo("list-all-cml-labs");
    }
}
