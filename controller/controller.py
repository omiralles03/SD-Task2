import base64
import pika
import boto3
import time
import json
from common.config import RABBIT_HOST

TRT = 10.0  # Tr (Target Response Time): objective time to empty the queue
WC = 10.0 # C: worker capacity per second (1 msg/100ms --> C = 10mgs/s)
BATCH_SIZE = 500 # num msg to send to each Lambda

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

                #  Limit to 10 max concurrency
                num_workers_needed = max(1, min(int(num_workers) + 1, 8))

                et = time.perf_counter() - st

                print(f"({et:.2f}s) [Load] Backlog (B): {backlog} | Arrival Rate (λ): {arrival_rate}/s")
                print(f"({et:.2f}s) [Scale] Workers: {num_workers_needed}.")

                for _ in range(num_workers_needed):
                    ticket_batch = []

                    for _ in range(BATCH_SIZE):
                        method, properties, body = channel.basic_get(queue='ticket_queue', auto_ack=True)

                        if method:
                            body_b64 = base64.b64encode(body).decode('utf-8')
                            ticket_batch.append({"data": body_b64})
                        else:
                            break


                    if ticket_batch:
                        payload = {
                            "rmqMessagesByQueue": { 
                                "ticket_queue": ticket_batch
                            }
                        }

                        try:
                            lambda_client.invoke(
                                FunctionName='TicketWorkerLambda',
                                InvocationType='Event',
                                Payload=json.dumps(payload)
                            )

                            # lambda_client.put_function_concurrency(
                            #         FunctionName='TicketWorkerLambda',
                            #         ReservedConcurrentExecutions=num_workers_needed
                            #         )

                        except Exception as aws_err:
                            print(f" [!] AWS Error: {aws_err}")

                last_backlog = backlog
            else:
                last_backlog = 0

            time.sleep(1)

    except KeyboardInterrupt:
        print(" [-] Controlador aturat.")
    finally:
        connection.close()

if __name__ == "__main__":
    monitor_and_scale() 
