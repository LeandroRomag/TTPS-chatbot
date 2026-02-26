from dotenv import load_dotenv
import os
load_dotenv()
for k in ('DB_SCHEMA','DB_USER','DB_PASSWORD','DB_HOST','DB_PORT','DB_NAME'):
    v = os.getenv(k)
    print(f"{k}: {repr(v)}")
