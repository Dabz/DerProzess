package io.confluent.dabz.driver;

import io.confluent.dabz.metrics.ProducerDriverMetrics;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.ByteArraySerializer;
import org.apache.kafka.common.serialization.IntegerSerializer;
import org.apache.log4j.Logger;

import java.io.FileReader;
import java.util.Properties;
import java.util.Random;
import java.util.concurrent.atomic.AtomicInteger;
import java.util.stream.IntStream;

public class ProducerDriver extends Driver {
    static Logger log = Logger.getLogger(ProducerDriver.class.getName());
    private String configFile;
    private String topic;
    private int expectedNumberOfThreads;
    private int expectedSizeOfPayload;
    private short numPartitions;
    private short replicationFactor;
    private ProducerDriverMetrics producerDriverMetrics = ProducerDriverMetrics.getShared();

    public ProducerDriver(String configFile, String topic, int expectedNumberOfThreads,
                          int expectedSizeOfPayload, short replicationFactor, short numPartitions) {
        this.configFile = configFile;
        this.topic = topic;
        this.expectedNumberOfThreads = expectedNumberOfThreads;
        this.expectedSizeOfPayload = expectedSizeOfPayload;
        this.replicationFactor = replicationFactor;
        this.numPartitions = numPartitions;

        try {
            createTopic(configFile, topic, replicationFactor, numPartitions);
        } catch (Exception e) {
            log.error("can not create topic", e);
            return;
        }
    }

    @Override
    public void run() {
        Properties properties = new Properties();
        try {
            properties.load(new FileReader(configFile));
            properties.put(ProducerConfig.KEY_SERIALIZER_CLASS_CONFIG, IntegerSerializer.class);
            properties.put(ProducerConfig.VALUE_SERIALIZER_CLASS_CONFIG, ByteArraySerializer.class);

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
                    try {
                        kafkaProducer.send(producerRecord, ((metadata, exception) -> {
                            if (exception != null) {
                                ProducerDriverMetrics.getShared().getTotalNumberOfMessageProduced().incrementAndGet();
                                exception.printStackTrace(System.err);
                            }
                            if (metadata != null) {
                                producerDriverMetrics.updateCounter(metadata);
                            }
                        }));
                    } catch (Exception e) {
                        e.printStackTrace(System.err);
                    }
                }
                kafkaProducer.close();
            }).start();
        }
        producerDriverMetrics.setShouldStart(true);
    }

    public byte[] generatePayload(int size) {
        byte[] results = new byte[size];
        Random random = new Random();
        random.nextBytes(results);
        return results;
    }
}
