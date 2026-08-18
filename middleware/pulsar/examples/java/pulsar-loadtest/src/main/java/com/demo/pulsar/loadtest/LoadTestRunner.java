package com.demo.pulsar.loadtest;

import org.apache.pulsar.client.api.*;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.Properties;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;
import java.util.concurrent.atomic.AtomicLong;

public class LoadTestRunner {
    public static void main(String[] args) throws Exception {
        Properties props = new Properties();
        try (InputStream in = LoadTestRunner.class.getResourceAsStream("/loadtest.properties")) {
            if (in != null) props.load(in);
        }
        String url = props.getProperty("pulsar.url", "pulsar://localhost:6650");
        String topic = props.getProperty("topic", "persistent://dev/test/device-telemetry");
        int deviceCount = Integer.parseInt(props.getProperty("device.count", "1000"));
        int threads = Integer.parseInt(props.getProperty("threads", "50"));
        int intervalMs = Integer.parseInt(props.getProperty("interval.ms", "1000"));
        int payloadBytes = Integer.parseInt(props.getProperty("payload.bytes", "512"));
        int durationSec = args.length > 0 ? Integer.parseInt(args[0]) : 30;

        AtomicLong sent = new AtomicLong();
        try (PulsarClient client = PulsarClient.builder().serviceUrl(url).build();
             Producer<byte[]> producer = client.newProducer()
                     .topic(topic)
                     .enableBatching(true)
                     .compressionType(CompressionType.LZ4)
                     .blockIfQueueFull(true)
                     .create()) {
            ExecutorService pool = Executors.newFixedThreadPool(threads);
            List<DeviceSimulator> simulators = new ArrayList<>();
            for (int i = 0; i < deviceCount; i++) {
                String deviceId = "device-" + i;
                DeviceSimulator sim = new DeviceSimulator(producer, deviceId, intervalMs, payloadBytes);
                simulators.add(sim);
                pool.submit(sim);
            }
            long start = System.currentTimeMillis();
            Thread.sleep(durationSec * 1000L);
            pool.shutdownNow();
            pool.awaitTermination(5, TimeUnit.SECONDS);
            producer.flush();
            long elapsed = Math.max(1, System.currentTimeMillis() - start);
            long estimated = (long) deviceCount * durationSec * 1000L / intervalMs;
            System.out.printf("devices=%d threads=%d duration=%ds estimatedMsgs~%d elapsed=%dms%n",
                    deviceCount, threads, durationSec, estimated, elapsed);
        }
    }
}
