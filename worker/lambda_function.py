import time
import os
import json
import base64
import psycopg2

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

def lambda_handler(event, context):
    # AWS sends data as in format:
    #   event = { "rmqMessagesByQueue": { "ticket_queue": [ {"data": "xxx"}, {"data": "yyy"} ] }}
    msg_list = event.get('rmqMessagesByQueue', {}).get('ticket_queue', [])

    # Connection with PostgreSQL
    conn = get_db_connection()
    cur = conn.cursor()

    for msg in msg_list:
        start_time = time.time()

        # When AWS reads from RabbitMQ, it sends the messages inside 'rmqMessagesByQueue'
        # The messages come encoded in Base64.
        body_data = base64.b64decode(msg['data']).decode('utf-8')
        payload = json.loads(body_data)

        time.sleep(0.1)

        if payload['action'] == 'buy_unnumbered':
            cur.execute("""
                UPDATE unnumbered_tickets
                SET sold_tickets = sold_tickets + 1
                WHERE sold_tickets < total_tickets;
            """)

        elif payload['action'] == 'buy_numbered':
            cur.execute("""
                INSERT INTO numbered_tickets (seat_number, client_id)
                VALUES (%s, %s);
            """, (
                payload['seat_number'],
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

    conn.commit() 
