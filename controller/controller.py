import pika
import time
import subprocess
from common.config import RABBIT_HOST

# Constantly observes the amount of messages that exist in rabbitmq and decides how many lambdas should be executed.

TRT = 10.0  # Tr (Target Response Time): objective time to empty the queue
WC = 10.0 # C: worker capacity per second (1 msg/100ms --> C = 10mgs/s)
BATCH_SIZE = 500 # num msg to send to each Lambda
MAX_WORKERS = 40

def monitor_and_scale():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()

    last_backlog = 0 # backlog: pending amount of messages

    st = time.perf_counter()

    active_workers = []
    curr_workers = 0

    try:
        while True:
            active_workers = [p for p in active_workers if p.poll() is None]
            curr_workers_count = len(active_workers)

            # Check the queue in passive mode and get the backlog
            queue = channel.queue_declare(queue='ticket_queue', durable=True, passive=True)
            backlog = queue.method.message_count

            # if there are pending messages -> calculate how many workers
            if backlog > 0:
                # Arrival rate (λ) since last second
                arrival_rate = max(backlog - last_backlog, 0)

                # N = [B + (λ * Tr)] / C
                num_workers = (backlog + (arrival_rate * TRT)) / WC

                #  Limit to 40 max concurrency
                num_workers_needed = max(1, min(int(num_workers) + 1, MAX_WORKERS))

                et = time.perf_counter() - st

                # Log
                print(f"({et:.2f}s) [Load] Backlog (B): {backlog} | Arrival Rate (λ): {arrival_rate}/s")
                print(f"({et:.2f}s) [Scale] Workers needed: {num_workers_needed}.")
                print(f"({et:.2f}s) [Active] Workers active: {curr_workers_count}.")

                # Avoid creating new processes if all available workers are in use
                # Avoids saturating the limit of PostgreSQL connections
                if num_workers_needed > curr_workers_count:
                    workers_to_launch = num_workers_needed - curr_workers_count
                    print(f"({et:.2f}s) [Scale] Workers to launch: {workers_to_launch}.")

                    for _ in range(workers_to_launch):
                        curr_workers += 1
                        worker_id = f"{curr_workers}"
                        p = subprocess.Popen(["python3", "-u", "-m", "worker.worker", worker_id])
                        active_workers.append(p)
                else:
                    print(f"({et:.2f}s) [Scale] Enough active_workers (active: {curr_workers_count}, needed: {num_workers_needed}")

                last_backlog = backlog
            else:
                last_backlog = 0

            time.sleep(1)

    except KeyboardInterrupt:
        print(" [-] Controller Stopped.")
        for p in active_workers:
            p.terminate()
    finally:
        connection.close()

if __name__ == "__main__":
    monitor_and_scale() 
