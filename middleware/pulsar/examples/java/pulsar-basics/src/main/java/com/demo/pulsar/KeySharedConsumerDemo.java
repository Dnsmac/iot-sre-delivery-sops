package com.demo.pulsar;

import org.apache.pulsar.client.api.*;

import java.util.concurrent.TimeUnit;

public class KeySharedConsumerDemo {
    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = "persistent://dev/test/key-shared-demo";
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build();
             Consumer<String> consumer = client.newConsumer(Schema.STRING)
                     .topic(topic)
                     .subscriptionName("key-shared-sub")
                     .subscriptionType(SubscriptionType.Key_Shared)
                     .keySharedPolicy(KeySharedPolicy.stickyHashRange())
                     .receiverQueueSize(100)
                     .subscribe()) {
            for (int i = 0; i < 10; i++) {
                Message<String> msg = consumer.receive(2, TimeUnit.SECONDS);
                if (msg == null) break;
                System.out.println("key=" + msg.getKey() + " value=" + msg.getValue());
                consumer.acknowledge(msg);
            }
        }
    }
}
