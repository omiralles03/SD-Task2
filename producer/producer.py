from common.config import RABBIT_HOST
from common.parser import parse_benchmark_line

import pika
import json
import sys

def start_producer(benchmark, num_consumers):
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        
        channel = connection.channel()
        channel.queue_declare(queue='ticket_queue', durable=True)

        print(f" [*] Reading file: {benchmark}")

        count = 0
        with open(benchmark, 'r') as f:

            for line in f:
                data = parse_benchmark_line(line)

                if data:
                    # 10: Impodency request_id

                    if "request_id" not in data or not data["request_id"]:
                        data["request_id"] = f"req_{count}_{data.get('seat_id', 'un')}"


                    # Send line as JSON message
                    channel.basic_publish(
                        exchange='',
                        routing_key='ticket_queue',
                        body=json.dumps(data),
                        properties=pika.BasicProperties(
                            delivery_mode=2,    # Persistent message
                            content_type='application/json'
                        )
                    )
                    count += 1
                    if count % 1000 == 0:
                        print(f" [x] Sent {count} requests...")

        print(f" [v] Finished! Total sent: {count} messages.")

        connection.close()

    except FileNotFoundError:
        print(f" [!] Error: File {benchmark} not found.")
    except Exception as e:
        print(f" [!] Error: {e}")
        

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f" [!] Error: Invalid arguments.")
        print(f" [>] Usage: python3 producer.py <benchmark> [num_consumers].")
        sys.exit(1)
    
    benchmark = sys.argv[1]
    num_consumers = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    start_producer(benchmark, num_consumers)

