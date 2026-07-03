package com.frankliu.netagent.mcp;

@FunctionalInterface
public interface CmlMcpClientFactory {
    CmlMcpClient open() throws Exception;
}
