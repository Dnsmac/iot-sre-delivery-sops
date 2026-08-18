package com.demo.mqtt;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

public class SubscribeDemo {
    public static void main(String[] args) throws Exception {
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        MqttClient client = new MqttClient(broker, "sub-demo-" + System.nanoTime(), new MemoryPersistence());
        MqttConnectOptions opts = new MqttConnectOptions();
        opts.setCleanSession(true);
        opts.setAutomaticReconnect(true);
        client.setCallback(new MqttCallback() {
            public void connectionLost(Throwable cause) {
                System.err.println("lost: " + cause);
            }
            public void messageArrived(String topic, MqttMessage message) {
                System.out.println(topic + " => " + new String(message.getPayload()) + " qos=" + message.getQos());
            }
            public void deliveryComplete(IMqttDeliveryToken token) {}
        });
        client.connect(opts);
        client.subscribe("dev/test/#", 1);
        System.out.println("Subscribed dev/test/# ... 10s");
        Thread.sleep(10000);
        client.disconnect();
        client.close();
    }
}
