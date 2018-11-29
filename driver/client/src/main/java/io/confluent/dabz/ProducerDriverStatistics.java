package io.confluent.dabz;

import java.util.concurrent.atomic.AtomicLong;

public class ProducerDriverStatistics implements Runnable {
    private static ProducerDriverStatistics shared = new ProducerDriverStatistics();
    private AtomicLong totalNumberOfMessagesProduced = new AtomicLong(0);
    private AtomicLong totalSizeOfMessagesProduced = new AtomicLong(0);
    private Boolean minimalist = false;

    public static ProducerDriverStatistics getShared() {
        return shared;
    }

    public AtomicLong getTotalNumberOfMessageProduced() {
        return totalNumberOfMessagesProduced;
    }

    public AtomicLong getTotalSizeOfMessagesProduced() {
        return totalSizeOfMessagesProduced;
    }

    public Boolean getMinimalist() {
        return minimalist;
    }

    public void setMinimalist(Boolean minimalist) {
        this.minimalist = minimalist;
    }

    @Override
    public void run() {
        try {
            Thread.sleep(3000);
        } catch (InterruptedException e) {
        }

        long previousNumberOfMessageProduced = shared.totalNumberOfMessagesProduced.get();
        long previousSizeOfMessagesProduced = shared.totalSizeOfMessagesProduced.get();

        try {
            while (true) {
                Thread.sleep(1000);
                long deltaNumberOfMessages = shared.totalNumberOfMessagesProduced.get() - previousNumberOfMessageProduced;
                long deltaSizeOfmessages = shared.totalSizeOfMessagesProduced.get() - previousSizeOfMessagesProduced;
                previousNumberOfMessageProduced = shared.totalNumberOfMessagesProduced.get();
                previousSizeOfMessagesProduced = shared.totalSizeOfMessagesProduced.get();

                if (minimalist) {
                    printMachineReadable(deltaNumberOfMessages, deltaSizeOfmessages);
                } else {
                    printHumanReadable(deltaNumberOfMessages, deltaSizeOfmessages);
                }
            }
        } catch (InterruptedException e) {
            e.printStackTrace();
        }
    }

    public void printHumanReadable(long deltaNumberOfMessages, long deltaSizeOfmessages) {
        System.out.println(String.format("Message sent %d (%s)", deltaNumberOfMessages, humanReadableByteCount(deltaSizeOfmessages, false)));
    }

    public void printMachineReadable(long deltaNumberOfMessages, long deltaSizeOfmessages) {
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
