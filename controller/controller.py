import pika
import boto3
import time

from pika.compat import time_now
from common.config import RABBIT_HOST

TRT = 10.0  # Tr (Target Response Time): objective time to empty the queue
WC = 10.0 # C: worker capacity per second (1 msg/100ms --> C = 10mgs/s)

def monitor_and_scale():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()

    lambda_client = boto3.client('lambda', region_name='us-east-1')
    last_backlog = 0
    
    st = time.perf_counter()
    try:
        while True:

            # Check the queue in passive mode and get the backlog
            queue = channel.queue_declare(queue='ticket_queue', durable=True, passive=True)
            backlog = queue.method.message_count
            
            if backlog > 0:
                # Arrival rate (λ) since last second
                arrival_rate = max(backlog - last_backlog, 0)
                
                # N = [B + (λ * Tr)] / C
                num_workers = (backlog + (arrival_rate * TRT)) / WC
                
                #  Limit to 200 max concurrency
                num_workers_needed = max(1, min(int(num_workers) + 1, 200))
                
                et = time.perf_counter() - st
                print(f"({et:.2f}s) [Load] Backlog (B): {backlog} | Arrival Rate (λ): {arrival_rate}/s")
                print(f"({et:.2f}s) [Scale] Workers: {num_workers_needed}.")
                
                try:
                    lambda_client.put_function_concurrency(
                            FunctionName='TicketWorkerLambda',
                            ReservedConcurrentExecutions=num_workers_needed
                            )
                except Exception as aws_err:
                    print(f" [!] AWS Error: {aws_err}")

                last_backlog = backlog
            else:
                if last_backlog > 0:
                    print(f" [>] Queue empty.")

                    try:
                        lambda_client.delete_function_concurrency(
                                FunctionName='TicketWorkerLambda'
                                )
                    except:
                        pass
                last_backlog = 0
                
            time.sleep(1)
            
    except KeyboardInterrupt:
        print(" [-] Controlador aturat.")
    finally:
        connection.close()

if __name__ == "__main__":
    monitor_and_scale()

