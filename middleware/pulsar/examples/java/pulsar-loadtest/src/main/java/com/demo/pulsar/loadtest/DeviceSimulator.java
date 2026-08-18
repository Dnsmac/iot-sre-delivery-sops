package com.demo.pulsar.loadtest;

import org.apache.pulsar.client.api.Producer;

public class DeviceSimulator implements Runnable {
    private final Producer<byte[]> producer;
    private final String deviceId;
    private final int intervalMs;
    private final byte[] payload;

    public DeviceSimulator(Producer<byte[]> producer, String deviceId, int intervalMs, int payloadBytes) {
        this.producer = producer;
        this.deviceId = deviceId;
        this.intervalMs = intervalMs;
        this.payload = new byte[payloadBytes];
    }

    @Override
    public void run() {
        while (!Thread.currentThread().isInterrupted()) {
            try {
                producer.newMessage().key(deviceId).value(payload).sendAsync();
                Thread.sleep(intervalMs);
            } catch (InterruptedException e) {
                Thread.currentThread().interrupt();
                break;
            } catch (Exception e) {
                throw new RuntimeException(e);
            }
        }
    }
}
