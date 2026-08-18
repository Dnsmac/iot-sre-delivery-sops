package com.demo.pulsar.tuning;

import org.apache.pulsar.client.api.*;

import java.util.concurrent.TimeUnit;

public class BatchCompareBenchmark {
    private static final int COUNT = 10_000;
    private static final String TOPIC_PREFIX = "persistent://dev/test/bench-";

    public static void main(String[] args) throws Exception {
        String url = System.getenv().getOrDefault("PULSAR_URL", "pulsar://localhost:6650");
        String topic = TOPIC_PREFIX + System.nanoTime();
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build()) {
            benchmark(client, topic + "-no-batch", false, CompressionType.NONE);
            benchmark(client, topic + "-batch", true, CompressionType.LZ4);
        }
    }

    private static void benchmark(PulsarClient client, String topic, boolean batching, CompressionType compression)
            throws Exception {
        try (Producer<byte[]> producer = client.newProducer()
                .topic(topic)
                .enableBatching(batching)
                .batchingMaxPublishDelay(10, TimeUnit.MILLISECONDS)
                .compressionType(compression)
                .create()) {
            byte[] payload = new byte[256];
            long start = System.currentTimeMillis();
            for (int i = 0; i < COUNT; i++) {
                producer.newMessage().value(payload).sendAsync();
            }
            producer.flush();
            long elapsed = Math.max(1, System.currentTimeMillis() - start);
            long tps = COUNT * 1000L / elapsed;
            System.out.printf("batching=%s compression=%s elapsed=%dms TPS=%d%n",
                    batching, compression, elapsed, tps);
        }
    }
}
