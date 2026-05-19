import pika
import boto3
import json
import time
from common.config import RABBIT_HOST

TRT = 10.0  # Tr (Target Response Time): objective time to empty the queue
WC = 10.0 # C: worker capacity per second (1 msg/100ms --> C = 10mgs/s)

def monitor_and_scale():
    connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
    channel = connection.channel()

    lambda_client = boto3.client('lambda', region_name='us_east-1')
    last_backlog = 0
    
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
                
                print(f" [Load] Backlog (B): {backlog} | Arrival Rate (λ): {arrival_rate}/s")
                print(f" [Scale] Workers: {num_workers_needed}.")
                
                for _ in range(num_workers_needed):
                    # auto_ack=False in case lamda crashes
                    # Get a single message from the AMQP broker. Returns a sequence with
                    # the method frame, message properties, and body.
                    method_frame, _, body = channel.basic_get(queue='ticket_queue', auto_ack=False)
                    
                    # queue empty if method_frame is None
                    if method_frame:
                        payload = json.loads(body.decode())
                        # Inject delivery_tag if worker needs ack
                        payload["delivery_tag"] = method_frame.delivery_tag
                        
                        # async launch of lambda
                        lambda_client.invoke(
                            FunctionName='TicketWorkerLambda',
                            InvocationType='Event',
                            Payload=json.dumps(payload)
                        )
                        
                        channel.basic_ack(delivery_tag=method_frame.delivery_tag)
                    else:
                        # In case we have no messages left before getting N
                        break
                
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

