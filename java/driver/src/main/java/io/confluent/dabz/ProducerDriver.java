package io.confluent.dabz;

import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.ByteArraySerializer;
import org.apache.kafka.common.serialization.BytesSerializer;
import org.apache.kafka.common.serialization.IntegerSerializer;
import org.apache.log4j.Logger;

import java.io.FileReader;
import java.io.IOException;
import java.util.Properties;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;

public class ProducerDriver extends Driver {
    static Logger log = Logger.getLogger(ProducerDriver.class.getName());
    private String configFile;
    private String topic;
    private int expectedNumberOfThreads;
    private int expectedSizeOfPayload;
    private boolean running = true;

    public ProducerDriver(String configFile, String topic, int expectedNumberOfThreads, int expectedSizeOfPayload) {
        this.configFile = configFile;
        this.topic = topic;
        this.expectedNumberOfThreads = expectedNumberOfThreads;
        this.expectedSizeOfPayload = expectedSizeOfPayload;
    }

    @Override
    public void run() {
        Properties properties = new Properties();
        try {
            properties.load(new FileReader(configFile));
            properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, IntegerSerializer.class);
            properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, ByteArraySerializer.class);
            properties.put(ProducerConfig.INTERCEPTOR_CLASSES_CONFIG,
                    "io.confluent.monitoring.clients.interceptor.MonitoringProducerInterceptor");

        } catch (Exception e) {
            log.error("can not read properties file", e);
            return;
        }

        for (int numThread = 0; numThread < expectedNumberOfThreads; numThread++) {
            new Thread(() -> {
                KafkaProducer kafkaProducer = new KafkaProducer(properties);
                byte[] payload = generatePayload(expectedSizeOfPayload);
                AtomicInteger key = new AtomicInteger(0);

                while (this.getRunning()) {
                    ProducerRecord<Integer, byte[]> producerRecord = new ProducerRecord<>(topic, key.getAndIncrement(), payload);
                    kafkaProducer.send(producerRecord, ((metadata, exception) -> {
                        ProducerDriverStatistics.getShared().getTotalNumberOfMessageProduced().incrementAndGet();
                        ProducerDriverStatistics.getShared().getTotalSizeOfMessagesProduced().addAndGet(metadata.serializedKeySize() + metadata.serializedValueSize());
                    }));
                }
                kafkaProducer.close();
            }).start();
        }
    }

    public byte[] generatePayload(int size) {
        byte[] results = new byte[size];
        Random random = new Random();
        random.nextBytes(results);
        return results;
    }
}
