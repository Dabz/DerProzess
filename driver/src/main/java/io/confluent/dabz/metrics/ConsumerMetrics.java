package io.confluent.dabz.metrics;

import java.util.concurrent.atomic.AtomicLong;

public class ConsumerMetrics extends Metrics {
    private static ConsumerMetrics shared = new ConsumerMetrics();
    private AtomicLong totalNumberOfMessagesConsumed = new AtomicLong(0);
    private AtomicLong totalSizeOfMessagesConsumed = new AtomicLong(0);
    private AtomicLong totalTimePartionHasBeenReset = new AtomicLong(0);

    public static ConsumerMetrics getShared() {
        return shared;
    }

    public AtomicLong getTotalNumberOfMessagesConsumed() {
        return totalNumberOfMessagesConsumed;
    }

    public AtomicLong getTotalSizeOfMessagesConsumed() {
        return totalSizeOfMessagesConsumed;
    }

    public AtomicLong getTotalTimePartionHasBeenReset() {
        return totalTimePartionHasBeenReset;
    }

    @Override
    public void run() {
        waitUntilReady();

        long previousNumberOfMessageProduced = shared.totalNumberOfMessagesConsumed.get();
        long previousSizeOfMessagesProduced = shared.totalSizeOfMessagesConsumed.get();

        try {
            while (this.getRunning()) {
                Thread.sleep(1000);
                long deltaNumberOfMessages = shared.totalNumberOfMessagesConsumed.get() - previousNumberOfMessageProduced;
                long deltaSizeOfmessages = shared.totalSizeOfMessagesConsumed.get() - previousSizeOfMessagesProduced;
                previousNumberOfMessageProduced = shared.totalNumberOfMessagesConsumed.get();
                previousSizeOfMessagesProduced = shared.totalSizeOfMessagesConsumed.get();

                if (this.getMinimalist()) {
                    printMachineReadable(deltaSizeOfmessages);
                } else {
                    printHumanReadable(deltaNumberOfMessages, deltaSizeOfmessages);
                }
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public void printHumanReadable(long deltaNumberOfMessages, long deltaSizeOfmessages) {
        System.out.println(String.format("Message received %d (%s)", deltaNumberOfMessages, humanReadableByteCount(deltaSizeOfmessages, false)));
    }

    public void printMachineReadable(long deltaSizeOfmessages) {
        System.out.println(String.valueOf(deltaSizeOfmessages));
    }

    public String humanReadableByteCount(long bytes, boolean si) {
        int unit = si ? 1000 : 1024;
        if (bytes < unit) return bytes + " B";
        int exp = (int) (Math.log(bytes) / Math.log(unit));
        String pre = (si ? "kMGTPE" : "KMGTPE").charAt(exp-1) + (si ? "" : "i");
        return String.format("%.1f %sB", bytes / Math.pow(unit, exp), pre);
    }
}
