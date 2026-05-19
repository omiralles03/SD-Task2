import time
import os
import json
import base64
import psycopg2
from psycopg2 import IntegrityError

# Database connection (Outside the handler to reuse it between executions and be more efficient)
DB_HOST = os.environ.get("DB_HOST")
DB_NAME = os.environ.get("DB_NAME")
DB_USER = os.environ.get("DB_USER")
DB_PASSWORD = os.environ.get("DB_PASSWORD")

def get_db_connection():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )

def lambda_handler(event, context):
    # Start time for metrics
    start_time = time.time()
    
    # Artificial Delay: external payment latency
    time.sleep(0.1)
    
    conn = None
    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        # When AWS reads from RabbitMQ, it sends the messages inside 'rmqMessagesByQueue'
        # The messages come encoded in Base64.
        if "rmqMessagesByQueue" in event:
            for queue_name, messages in event["rmqMessagesByQueue"].items():
                for msg in messages:
                    # Decode the message sent by producer.py
                    decoded_data = base64.b64decode(msg['data']).decode('utf-8')
                    ticket_data = json.loads(decoded_data)
                    
                    process_ticket(cur, conn, ticket_data)
        else:
            # Fallback for manual testing sending a direct JSON from the AWS console
            process_ticket(cur, conn, event)
            
        conn.commit()

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Transaction error: {e}")
        raise e
        
    finally:
        # Metrics: record transaction time
        end_time = time.time()
        duration = end_time - start_time
        
        if conn:
            try:
                cur = conn.cursor()
                # Save to the database to compute Throughput and Latency later
                cur.execute("""
                    INSERT INTO transaction_metrics (start_time, end_time, duration) 
                    VALUES (to_timestamp(%s), to_timestamp(%s), %s);
                """, (start_time, end_time, duration))
                conn.commit()
            except Exception as metric_err:
                print(f"Error saving metrics: {metric_err}")
            finally:
                cur.close()
                conn.close()

    return {
        'statusCode': 200,
        'body': json.dumps('Processing completed successfully')
    }

# Purchase and concurrency logic
def process_ticket(cur, conn, ticket_data):
    ticket_type = ticket_data.get("type")
    request_id = ticket_data.get("request_id") # Key for idempotency
    
    if ticket_type == "unnumbered":
        # We do an UPDATE. The condition "available > 0" ensures no overselling
        cur.execute("""
            UPDATE unnumbered_tickets 
            SET available = available - 1 
            WHERE id = 1 AND available > 0 
            RETURNING available;
        """)
        result = cur.fetchone()
        if not result:
            print(f"[{request_id}] Denied: No unnumbered tickets left.")
            
    elif ticket_type == "numbered":
        seat_id = ticket_data.get("seat_id")
        try:
            # We do an INSERT. If the seat already exists, it will raise an IntegrityError 
            # assuming the seat_id column has a UNIQUE constraint in PostgreSQL.
            cur.execute("""
                INSERT INTO occupied_seats (seat_id, request_id) 
                VALUES (%s, %s);
            """, (seat_id, request_id))
        except IntegrityError:
            # We handle the error to avoid double-selling and rollback the failed insert
            conn.rollback()
            print(f"[{request_id}] Denied: Seat {seat_id} is already sold.")