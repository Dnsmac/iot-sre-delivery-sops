package com.demo.mqtt.troubleshoot;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

/**
 * B9 场景7：Clean Session=false + 稳定 ClientId，断线后重连可收 QoS1 离线消息（需 Broker persistence）。
 * 运行后按提示：Ctrl+C 断开 sub，再 mosquitto_pub 发布，再运行本程序。
 */
public class OfflineSessionDemo {
    private static final String CLIENT_ID = "offline-demo-device001";

    public static void main(String[] args) throws Exception {
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        String topic = "dev/session/offline";
        boolean subscribeOnly = args.length > 0 && "sub".equalsIgnoreCase(args[0]);

        MqttConnectOptions opts = new MqttConnectOptions();
        opts.setCleanSession(false);
        opts.setAutomaticReconnect(false);

        MqttClient client = new MqttClient(broker, CLIENT_ID, new MemoryPersistence());
        client.setCallback(new MqttCallback() {
            public void connectionLost(Throwable cause) {
                System.out.println("connectionLost: " + cause);
            }
            public void messageArrived(String t, MqttMessage m) {
                System.out.println("OFFLINE-DEMO received: " + new String(m.getPayload()));
            }
            public void deliveryComplete(IMqttDeliveryToken token) {}
        });

        client.connect(opts);
        client.subscribe(topic, 1);
        System.out.println("Connected ClientId=" + CLIENT_ID + " cleanSession=false topic=" + topic);
        if (subscribeOnly) {
            System.out.println("Waiting 30s for messages (publish while away with mosquitto_pub)...");
            Thread.sleep(30_000);
        } else {
            System.out.println("Subscribed. Disconnect (Ctrl+C), publish with:");
            System.out.println("  mosquitto_pub -h localhost -t " + topic + " -m offline-payload -q 1");
            System.out.println("Then re-run: mvn ... -Dexec.args=sub");
            Thread.sleep(60_000);
        }
        client.disconnect();
        client.close();
    }
}
