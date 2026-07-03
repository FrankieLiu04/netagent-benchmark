package com.frankliu.netagent.mcp;

import java.util.List;

public final class ToolPolicy {

    private static final List<String> MUTATING_TOOL_PREFIXES = List.of(
            "add_",
            "apply_",
            "clone_",
            "configure_",
            "connect_",
            "create_",
            "delete_",
            "modify_",
            "send_",
            "set_",
            "start_",
            "stop_",
            "wipe_"
    );

    private ToolPolicy() {
    }

    public static boolean isMutatingTool(String toolName) {
        return MUTATING_TOOL_PREFIXES.stream().anyMatch(toolName::startsWith);
    }
}
