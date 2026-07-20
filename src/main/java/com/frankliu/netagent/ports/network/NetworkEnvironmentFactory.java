package com.frankliu.netagent.ports.network;

@FunctionalInterface
public interface NetworkEnvironmentFactory {
    NetworkEnvironment open() throws Exception;
}
