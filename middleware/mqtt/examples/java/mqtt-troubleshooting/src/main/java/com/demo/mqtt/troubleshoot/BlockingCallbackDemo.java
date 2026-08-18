package com.demo.mqtt.troubleshoot;

import org.eclipse.paho.client.mqttv3.*;
import org.eclipse.paho.client.mqttv3.persist.MemoryPersistence;

import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.LinkedBlockingQueue;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

/**
 * B9 场景4：对比 callback 内同步 sleep（错误）与线程池异步（正确）。
 * 运行: mvn -q exec:java -Dexec.mainClass=...BlockingCallbackDemo [-Dexec.args=sync|async]
 */
public class BlockingCallbackDemo {
    public static void main(String[] args) throws Exception {
        boolean sync = args.length == 0 || "sync".equalsIgnoreCase(args[0]);
        String broker = System.getenv().getOrDefault("MQTT_BROKER", "tcp://localhost:1883");
        String topic = "dev/blocking/demo";
        ExecutorService pool = new ThreadPoolExecutor(2, 4, 60, TimeUnit.SECONDS,
                new LinkedBlockingQueue<>(100), r -> {
            Thread t = new Thread(r, "mqtt-worker");
            t.setDaemon(true);
            return t;
        }, new ThreadPoolExecutor.CallerRunsPolicy());

        MqttClient client = new MqttClient(broker, "blocking-demo-" + System.nanoTime(), new MemoryPersistence());
        MqttConnectOptions opts = new MqttConnectOptions();
        opts.setCleanSession(true);
        opts.setKeepAliveInterval(10);
        client.connect(opts);
        client.subscribe(topic, 1);
        client.setCallback(new MqttCallback() {
            public void connectionLost(Throwable cause) {
                System.err.println("connectionLost: " + cause);
            }
            public void messageArrived(String t, MqttMessage m) {
                if (sync) {
                    System.out.println("[SYNC] slow work start");
                    try { Thread.sleep(5000); } catch (InterruptedException ignored) {}
                    System.out.println("[SYNC] done (blocks Paho thread)");
                } else {
                    pool.submit(() -> {
                        System.out.println("[ASYNC] slow work start");
                        try { Thread.sleep(5000); } catch (InterruptedException ignored) {}
                        System.out.println("[ASYNC] done");
                    });
                }
            }
            public void deliveryComplete(IMqttDeliveryToken token) {}
        });

        MqttClient pub = new MqttClient(broker, "blocking-pub-" + System.nanoTime(), new MemoryPersistence());
        pub.connect(new MqttConnectOptions() {{ setCleanSession(true); }});
        for (int i = 0; i < 3; i++) {
            pub.publish(topic, new MqttMessage(("msg-" + i).getBytes()) {{ setQos(1); }});
            Thread.sleep(300);
        }
        System.out.println("Mode=" + (sync ? "sync (bad)" : "async (good)") + "; watch PING/callback behavior");
        Thread.sleep(8000);
        pool.shutdown();
        pub.disconnect();
        pub.close();
        client.disconnect();
        client.close();
    }
}
