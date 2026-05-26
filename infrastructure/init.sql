CREATE TABLE IF NOT EXISTS unnumbered_tickets (
    id SERIAL PRIMARY KEY,
    total_tickets INT NOT NULL DEFAULT 100000,
    sold_tickets INT NOT NULL DEFAULT 0
);

INSERT INTO unnumbered_tickets (total_tickets, sold_tickets)
SELECT 100000, 0 WHERE NOT EXISTS (SELECT 1 FORM unnumbered_tickets);

CREATE TABLE IF NOT EXISTS numbered_tickets (
    seat_number INT PRIMARY KEY,
    client_id VARCHAR(50) NOT NULL,
    sold_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS metrics (
    id SERIAL PRIMARY KEY,
    request_id VARCHAR(100),
    action_type VARCHAR(50),
    start_time DOUBLE PRECISION,
    end_time DOUBLE PRECISION,
    latency DOUBLE PRECISION
);
