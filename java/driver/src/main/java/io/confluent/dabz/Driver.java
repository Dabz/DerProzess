package io.confluent.dabz;

public abstract class Driver implements Runnable {
    private Boolean running = true;

    public void setRunning(boolean running) {
        this.running = running;
    }

    public Boolean getRunning() {
        return running;
    }

    public abstract  void run();
}
