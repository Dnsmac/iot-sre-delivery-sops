package com.demo.pulsar;

import org.apache.pulsar.client.api.*;

public class HelloPulsar {
    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = "persistent://dev/test/hello";
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build()) {
            try (Producer<String> producer = client.newProducer(Schema.STRING).topic(topic).create()) {
                producer.send("hello pulsar");
                System.out.println("Sent: hello pulsar");
            }
            try (Consumer<String> consumer = client.newConsumer(Schema.STRING)
                    .topic(topic)
                    .subscriptionName("hello-sub")
                    .subscriptionType(SubscriptionType.Exclusive)
                    .subscribe()) {
                Message<String> msg = consumer.receive(5, java.util.concurrent.TimeUnit.SECONDS);
                if (msg != null) {
                    System.out.println("Received: " + msg.getValue());
                    consumer.acknowledge(msg);
                }
            }
        }
    }
}
