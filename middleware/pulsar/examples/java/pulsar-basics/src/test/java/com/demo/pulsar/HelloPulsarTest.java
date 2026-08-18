package com.demo.pulsar;

import org.apache.pulsar.client.api.*;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.testcontainers.containers.GenericContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import static org.junit.jupiter.api.Assertions.*;

@Testcontainers(disabledWithoutDocker = true)
class HelloPulsarTest {
    @Container
    @SuppressWarnings("resource")
    static GenericContainer<?> pulsar = new GenericContainer<>("apachepulsar/pulsar:3.2.3")
            .withExposedPorts(6650)
            .withCommand("bin/pulsar", "standalone");

    @Test
    void produceAndConsume() throws Exception {
        String url = "pulsar://" + pulsar.getHost() + ":" + pulsar.getMappedPort(6650);
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build()) {
            String topic = "persistent://public/default/test-" + System.nanoTime();
            try (Producer<String> p = client.newProducer(Schema.STRING).topic(topic).create()) {
                p.send("ok");
            }
            try (Consumer<String> c = client.newConsumer(Schema.STRING)
                    .topic(topic).subscriptionName("t").subscribe()) {
                Message<String> m = c.receive(30, java.util.concurrent.TimeUnit.SECONDS);
                assertNotNull(m);
                assertEquals("ok", m.getValue());
                c.acknowledge(m);
            }
        }
    }
}
