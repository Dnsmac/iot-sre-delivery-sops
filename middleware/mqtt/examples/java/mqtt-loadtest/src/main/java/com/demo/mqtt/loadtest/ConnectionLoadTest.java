package com.demo.mqtt.loadtest;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import java.util.concurrent.CountDownLatch;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

/** 多连接冒烟（本地建议 connections<=500；10W 需 EMQX+多机） */
public class ConnectionLoadTest {
    public static void main(String[] args) throws Exception {
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        int connections = args.length > 0 ? Integer.parseInt(args[0]) : 50;
        int holdSec = args.length > 1 ? Integer.parseInt(args[1]) : 30;
        AtomicInteger ok = new AtomicInteger();
        CountDownLatch latch = new CountDownLatch(connections);
        ExecutorService pool = Executors.newFixedThreadPool(Math.min(connections, 50));
        long start = System.currentTimeMillis();
        for (int i = 0; i < connections; i++) {
            final int id = i;
            pool.submit(() -> {
                try {
                    MqttClient c = new MqttClient(broker, "load-" + id + "-" + System.nanoTime(), new MemoryPersistence());
                    MqttConnectOptions o = new MqttConnectOptions();
                    o.setCleanSession(true);
                    o.setKeepAliveInterval(60);
                    o.setAutomaticReconnect(false);
                    c.connect(o);
                    ok.incrementAndGet();
                    Thread.sleep(holdSec * 1000L);
                    c.disconnect();
                    c.close();
                } catch (Exception e) {
                    System.err.println("fail id=" + id + ": " + e.getMessage());
                } finally {
                    latch.countDown();
                }
            });
        }
        latch.await();
        pool.shutdown();
        long elapsed = System.currentTimeMillis() - start;
        System.out.printf("connections=%d ok=%d elapsed=%dms%n", connections, ok.get(), elapsed);
    }
}
