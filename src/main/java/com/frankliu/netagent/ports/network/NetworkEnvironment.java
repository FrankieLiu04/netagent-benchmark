package com.frankliu.netagent.ports.network;

import java.util.Map;
import java.util.List;

public interface NetworkEnvironment {
    // Transport details live in adapters; the agent only needs available tools and calls.
    List<NetworkTool> listTools();

    String callTool(String name, Map<String, Object> arguments);
}
