package io.confluent.dabz.metrics;

import org.apache.kafka.clients.producer.RecordMetadata;

import java.util.Date;
import java.util.concurrent.atomic.AtomicLong;

public class ProducerDriverMetrics extends Metrics {
    private static ProducerDriverMetrics shared = new ProducerDriverMetrics();
    private AtomicLong totalNumberOfMessagesProduced = new AtomicLong(0);
    private AtomicLong totalSizeOfMessagesProduced = new AtomicLong(0);
    private AtomicLong totalLatency = new AtomicLong(0);
    private AtomicLong tickCount = new AtomicLong(0);

    public static ProducerDriverMetrics getShared() {
        return shared;
    }

    public AtomicLong getTotalNumberOfMessageProduced() {
        return totalNumberOfMessagesProduced;
    }

    public AtomicLong getTotalSizeOfMessagesProduced() {
        return totalSizeOfMessagesProduced;
    }

    @Override
    public void run() {
        waitUntilReady();

        try {
            while (this.getRunning()) {
                Thread.sleep(1000);
                long deltaNumberOfMessages = shared.totalNumberOfMessagesProduced.getAndSet(0);
                long deltaSizeOfmessages = shared.totalSizeOfMessagesProduced.getAndSet(0);
                long deltaLatency = shared.totalLatency.getAndSet(0);
                long deltaTick = shared.tickCount.getAndSet(0);

                if (deltaTick == 0) {
                    deltaTick = 1;
                }

                if (this.getMinimalist()) {
                    printMachineReadable(deltaNumberOfMessages, deltaSizeOfmessages, deltaLatency, deltaTick);
                } else {
                    printHumanReadable(deltaNumberOfMessages, deltaSizeOfmessages, deltaLatency, deltaTick);
                }
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public void printHumanReadable(long deltaNumberOfMessages, long deltaSizeOfmessages, long deltaLatency, long deltaTick) {
        System.out.println(String.format("Message sent %d (%s)", deltaNumberOfMessages, humanReadableByteCount(deltaSizeOfmessages, false)));
        System.out.println(String.format("-> Average latency %d ms", (deltaLatency / deltaTick)));
    }

    public void printMachineReadable(long deltaNumberOfMessages, long deltaSizeOfmessages, long deltaLatency, long deltaTick) {
        System.out.println(String.format("%d,%d",deltaSizeOfmessages, (deltaLatency / deltaTick)));
    }

    public String humanReadableByteCount(long bytes, boolean si) {
        int unit = si ? 1000 : 1024;
        if (bytes < unit) return bytes + " B";
        int exp = (int) (Math.log(bytes) / Math.log(unit));
        String pre = (si ? "kMGTPE" : "KMGTPE").charAt(exp-1) + (si ? "" : "i");
        return String.format("%.1f %sB", bytes / Math.pow(unit, exp), pre);
    }

    public void updateCounter(RecordMetadata metadata) {
        long currentDate = new Date().getTime();
        this.tickCount.incrementAndGet();
        this.totalNumberOfMessagesProduced.incrementAndGet();
        this.totalSizeOfMessagesProduced.addAndGet(metadata.serializedKeySize() + metadata.serializedValueSize());
        this.totalLatency.addAndGet(currentDate - metadata.timestamp());
    }
}
