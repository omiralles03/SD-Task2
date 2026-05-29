import time
import pika
import os
import json
import sys
import psycopg2

from common.config import RABBIT_HOST

DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")
DB_PORT = os.environ.get("DB_PORT")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        port=DB_PORT
    )

def worker_proc():
    worker_id = sys.argv[1] if len(sys.argv) > 1 else "???"
    conn = None
    cur = None
    rabbit_conn = None

    try:
        # Connection with PostgreSQL
        conn = get_db_connection()
        cur = conn.cursor()

        rabbit_conn = pika.BlockingConnection(pika.ConnectionParameters(host=RABBIT_HOST))
        channel = rabbit_conn.channel()

        processed = 0
        BATCH_SIZE = 500

        for _ in range (BATCH_SIZE):
            start_time = time.time()

            method, properties, body = channel.basic_get(queue='ticket_queue', auto_ack=False)

            if not method:
                break

            # When AWS reads from RabbitMQ, it sends the messages inside 'rmqMessagesByQueue'
            # The messages come encoded in Base64.
            body_data = body.decode('utf-8')
            payload = json.loads(body_data)

            time.sleep(0.1)

            try:
                if payload['action'] == 'buy_unnumbered':
                    cur.execute("""
                        UPDATE unnumbered_tickets
                        SET sold_tickets = sold_tickets + 1
                        WHERE sold_tickets < total_tickets;
                    """)

                elif payload['action'] == 'buy_numbered':
                    cur.execute("""
                        INSERT INTO numbered_tickets (seat_id, client_id)
                        VALUES (%s, %s);
                    """, (
                        payload['seat_id'],
                        payload['client_id']
                    ))

                end_time = time.time()

                cur.execute("""
                    INSERT INTO metrics (request_id, action_type, start_time, end_time, latency)
                    VALUES (%s, %s, %s, %s, %s);
                """, (
                    payload['request_id'],
                    payload['action'],
                    start_time,
                    end_time,
                    end_time - start_time
                ))

                processed += 1
                conn.commit()
                channel.basic_ack(delivery_tag=method.delivery_tag)

            except psycopg2.errors.UniqueViolation:
                print(f" [Worker {worker_id}] seat {payload.get('seat_id')} OCCUPIED.")
                conn.rollback()
                end_time = time.time()

                try:
                    cur.execute("""
                        INSERT INTO metrics (request_id, action_type, start_time, end_time, latency)
                        VALUES (%s, %s, %s, %s, %s);
                    """, (
                        payload['request_id'],
                        "OCCUPIED",
                        start_time,
                        end_time,
                        end_time - start_time
                    ))
                    conn.commit()
                except Exception as e:
                    print(f" [!] Err SQL: {e}")
                    conn.rollback()

                channel.basic_ack(delivery_tag=method.delivery_tag)

        if processed > 0:
            print(f" [Worker {worker_id}]: processed data > {processed}")

    except Exception as err:
        print(f" [!] Worker err: {err}")
        if conn:
            conn.rollback()

    finally:
        if cur : cur.close()
        if conn: conn.close()
        if rabbit_conn: rabbit_conn.close()

if __name__ == "__main__":
    worker_proc()
