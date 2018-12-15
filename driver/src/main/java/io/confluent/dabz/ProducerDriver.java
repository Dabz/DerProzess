package io.confluent.dabz;

import org.apache.kafka.clients.admin.AdminClient;
import org.apache.kafka.clients.admin.DescribeTopicsResult;
import org.apache.kafka.clients.admin.KafkaAdminClient;
import org.apache.kafka.clients.producer.KafkaProducer;
import org.apache.kafka.clients.producer.ProducerConfig;
import org.apache.kafka.clients.producer.ProducerRecord;
import org.apache.kafka.common.serialization.ByteArraySerializer;
import org.apache.kafka.common.serialization.BytesSerializer;
import org.apache.kafka.common.serialization.IntegerSerializer;
import org.apache.log4j.Logger;

import java.io.FileNotFoundException;
import java.io.FileReader;
import java.io.IOException;
import java.util.Arrays;
import java.util.Properties;
import java.util.Random;
import java.util.concurrent.ExecutionException;
import java.util.concurrent.atomic.AtomicInteger;

public class ProducerDriver extends Driver {
    static Logger log = Logger.getLogger(ProducerDriver.class.getName());
    private String configFile;
    private String topic;
    private int expectedNumberOfThreads;
    private int expectedSizeOfPayload;
    private short numPartitions;
    private short replicationFactor;
    private boolean running = true;

    public ProducerDriver(String configFile, String topic, int expectedNumberOfThreads,
                          int expectedSizeOfPayload, short replicationFactor, short numPartitions) {
        this.configFile = configFile;
        this.topic = topic;
        this.expectedNumberOfThreads = expectedNumberOfThreads;
        this.expectedSizeOfPayload = expectedSizeOfPayload;
        this.replicationFactor = replicationFactor;
        this.numPartitions = numPartitions;
    }

    @Override
    public void run() {
        try {
            createTopic(configFile, topic, replicationFactor, numPartitions);
        } catch (Exception e) {
            log.error("can not create topic", e);
            return;
        }
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
