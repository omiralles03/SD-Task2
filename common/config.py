import os
from dotenv import load_dotenv

load_dotenv()

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
RABBIT_HOST = os.getenv("RABBIT_HOST", "localhost")

REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
RABBIT_PORT = int(os.getenv("RABBIT_PORT", 5672))

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_NAME = os.getenv("DB_NAME", "ticket_system")
DB_USER = os.getenv("DB_USER", "user")
DB_PASSWORD = os.getenv("DB_PASSWORD", "123")
DB_PORT = int(os.getenv("DB_PORT", 5432))
