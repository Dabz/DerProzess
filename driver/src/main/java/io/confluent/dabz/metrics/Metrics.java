package io.confluent.dabz.metrics;

public abstract class Metrics implements Runnable {
    private Boolean shouldStart = false;

    public Boolean getShouldStart() {
        return shouldStart;
    }

    public void setShouldStart(Boolean shouldStart) {
        this.shouldStart = shouldStart;
    }

    public void waitUntilReady() {
        while (! shouldStart) {
            try {
                Thread.sleep(50);
            } catch (InterruptedException e) {
            }
        }
    }
}
