package com.frankliu.netagent.artifact;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.time.ZoneOffset;
import java.time.format.DateTimeFormatter;
import java.util.UUID;
import java.util.regex.Pattern;

public class RunLogService {

    private static final DateTimeFormatter RUN_ID_TIMESTAMP =
            DateTimeFormatter.ofPattern("yyyyMMdd'T'HHmmss'Z'").withZone(ZoneOffset.UTC);
    private static final Pattern SLUG_PATTERN = Pattern.compile("[^a-zA-Z0-9]+");

    private final ObjectMapper objectMapper;

    public RunLogService(ObjectMapper objectMapper) {
        this.objectMapper = objectMapper
                .findAndRegisterModules()
                .disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    }

    public RunLog startRunLog(String task, Path root) throws IOException {
        Instant timestamp = Instant.now();
        String runId = RUN_ID_TIMESTAMP.format(timestamp) + "-" + UUID.randomUUID().toString().replace("-", "").substring(0, 8);
        Path runDir = root.resolve(runId + "-" + makeSlug(task));
        Files.createDirectories(runDir);
        return new RunLog(runId, runDir, timestamp);
    }

    public Path writeRunLog(RunLog runLog, Object payload) throws IOException {
        Path path = runLog.runDir().resolve("run.json");
        JsonNode sanitized = SecretRedactor.sanitize(objectMapper.valueToTree(payload));
        objectMapper.writerWithDefaultPrettyPrinter().writeValue(path.toFile(), sanitized);
        return path;
    }

    static String makeSlug(String text) {
        String slug = SLUG_PATTERN.matcher(text.strip().toLowerCase()).replaceAll("-").replaceAll("(^-+|-+$)", "");
        String clipped = slug.isBlank() ? "run" : slug.substring(0, Math.min(48, slug.length()));
        return clipped.replaceAll("-+$", "");
    }
}
