package com.frankliu.netagent.adapters.network.cml;

import com.frankliu.netagent.ports.network.NetworkEnvironment;
import com.frankliu.netagent.ports.network.NetworkTool;

import java.util.List;
import java.util.Map;

public class CmlMcpUnavailableEnvironment implements NetworkEnvironment {

    private final CmlMcpServerSpec spec;

    public CmlMcpUnavailableEnvironment(CmlMcpServerSpec spec) {
        this.spec = spec;
    }

    @Override
    public List<NetworkTool> listTools() {
        throw unavailable();
    }

    @Override
    public String callTool(String name, Map<String, Object> arguments) {
        throw unavailable();
    }

    private IllegalStateException unavailable() {
        return new IllegalStateException(
                "No CML MCP environment is attached. Use CmlMcpEnvironment with prepared stdio command: "
                        + spec.command() + " " + String.join(" ", spec.args())
        );
    }
}
