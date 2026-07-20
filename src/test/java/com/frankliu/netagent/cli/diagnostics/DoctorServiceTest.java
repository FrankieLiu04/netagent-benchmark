package com.frankliu.netagent.cli.diagnostics;

import com.frankliu.netagent.adapters.network.replay.ReplayNetworkEnvironment;
import com.frankliu.netagent.experiment.NetagentSettings;
import com.frankliu.netagent.ports.network.NetworkTool;
import org.junit.jupiter.api.Test;

import java.util.List;
import java.util.Map;

import static org.assertj.core.api.Assertions.assertThat;

class DoctorServiceTest {

    private final DoctorService doctorService = new DoctorService();

    @Test
    void reportsHealthyRuntimeAndToolDiscovery() {
        NetagentSettings settings = NetagentSettings.fromMap(Map.of(
                "DEEPSEEK_API_KEY", "key"
        ));

        DoctorService.DoctorResult result = doctorService.check(
                settings,
                () -> new ReplayNetworkEnvironment(Map.of(), List.of(tool("get_cml_labs"), tool("read_node_state")))
        );

        assertThat(result.exitCode()).isZero();
        assertThat(result.messages()).contains("OK: DEEPSEEK_API_KEY is set");
        assertThat(result.messages()).contains("OK: CML MCP server started and exposed 2 tools");
        assertThat(result.messages()).contains("  - get_cml_labs", "  - read_node_state");
    }

    @Test
    void failsBeforeMcpDiscoveryWhenProviderKeyIsMissing() {
        NetagentSettings settings = NetagentSettings.fromMap(Map.of());

        DoctorService.DoctorResult result = doctorService.check(settings, () -> {
            throw new AssertionError("MCP should not start without a provider key");
        });

        assertThat(result.exitCode()).isEqualTo(1);
        assertThat(result.messages()).contains("FAIL: DEEPSEEK_API_KEY is missing");
    }

    @Test
    void reportsMcpStartupFailure() {
        NetagentSettings settings = NetagentSettings.fromMap(Map.of(
                "LLM_PROVIDER", "openai",
                "OPENAI_API_KEY", "key"
        ));

        DoctorService.DoctorResult result = doctorService.check(settings, () -> {
            throw new IllegalStateException("cml unavailable");
        });

        assertThat(result.exitCode()).isEqualTo(1);
        assertThat(result.messages()).contains("OK: OPENAI_API_KEY is set");
        assertThat(result.messages().getLast()).contains("cml unavailable");
    }

    private NetworkTool tool(String name) {
        return new NetworkTool(name, "test", Map.of("type", "object", "properties", Map.of()));
    }
}
