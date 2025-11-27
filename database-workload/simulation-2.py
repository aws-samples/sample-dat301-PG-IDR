import psycopg2
from concurrent.futures import ThreadPoolExecutor
import time
from dotenv import load_dotenv
import os
import signal
import sys
from datetime import datetime
import threading

# Load environment variables
load_dotenv()

# Get database parameters
db_params = {
    'dbname': os.getenv('DB_NAME'),
    'user': os.getenv('DB_USER'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST'),
    'port': os.getenv('DB_PORT')
}

# Counter for successful and failed updates
update_stats = {
    'successful': 0,
    'failed': 0,
    'lock_timeout': 0
}
stats_lock = threading.Lock()

def log_message(session, message):
    """Helper function to print timestamped log messages"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {session}: {message}")

def session1_idle_transaction():
    """Session 1: Start transaction and hold it"""
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    try:
        log_message("Session 1", "Beginning transaction...")
        cur.execute("BEGIN;")
        cur.execute("UPDATE sales_data SET sale_amount=101 WHERE sale_id=1;")
        log_message("Session 1", "Update executed, now holding transaction...")

        while True:
            time.sleep(5)
            cur2 = conn.cursor()
            cur2.execute("SELECT txid_current();")
            txid = cur2.fetchone()[0]
            log_message("Session 1", f"Still holding transaction. Transaction ID: {txid}")
            cur2.close()

    except KeyboardInterrupt:
        log_message("Session 1", "Received interrupt signal")
        conn.rollback()
        log_message("Session 1", "Transaction rolled back")
    except Exception as e:
        log_message("Session 1", f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        log_message("Session 1", "Connection closed")

def session2_bulk_update(iteration):
    """Session 2: Attempt bulk update while Session 1 holds lock"""
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    try:
        # Set a statement timeout of 10 seconds
        cur.execute("SET statement_timeout = '1000s';")

        log_message(f"Session 2 ({iteration})", "Starting bulk update...")
        cur.execute("UPDATE sales_data SET sale_amount=100 WHERE sale_id!=1;")
        conn.commit()

        with stats_lock:
            update_stats['successful'] += 1
        log_message(f"Session 2 ({iteration})", "Bulk update completed")

    except psycopg2.errors.QueryCanceled as e:
        with stats_lock:
            update_stats['lock_timeout'] += 1
        log_message(f"Session 2 ({iteration})", "Query timed out due to lock wait")
    except Exception as e:
        with stats_lock:
            update_stats['failed'] += 1
        log_message(f"Session 2 ({iteration})", f"Error: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
        log_message(f"Session 2 ({iteration})", "Connection closed")

def session3_monitor():
    """Session 3: Monitor database activity and print statistics"""
    while True:
        try:
            conn = psycopg2.connect(**db_params)
            cur = conn.cursor()

            # Print current statistics
            log_message("Monitor", "\nUpdate Statistics:")
            print("=" * 50)
            print(f"Successful updates: {update_stats['successful']}")
            print(f"Failed updates: {update_stats['failed']}")
            print(f"Lock timeouts: {update_stats['lock_timeout']}")
            print("=" * 50)

            # Query to show active queries and locks
            query = """
            SELECT pid,
                   usename,
                   state,
                   wait_event_type,
                   wait_event,
                   query,
                   age(clock_timestamp(), query_start) as duration
            FROM pg_stat_activity
            WHERE state != 'idle'
            ORDER BY duration DESC;
            """

            cur.execute(query)
            results = cur.fetchall()

            if results:
                log_message("Monitor", "\nActive Sessions:")
                print("=" * 80)
                for row in results:
                    print(f"PID: {row[0]}")
                    print(f"Username: {row[1]}")
                    print(f"State: {row[2]}")
                    print(f"Wait Event Type: {row[3]}")
                    print(f"Wait Event: {row[4]}")
                    print(f"Query: {row[5]}")
                    print(f"Duration: {row[6]}")
                    print("-" * 80)

            cur.close()
            conn.close()

            time.sleep(5)  # Check every 5 seconds

        except KeyboardInterrupt:
            break
        except Exception as e:
            log_message("Monitor", f"Error: {e}")
        finally:
            if 'conn' in locals() and conn is not None:
                conn.close()

def main():
    try:
        with ThreadPoolExecutor(max_workers=102) as executor:  # 1 for session1, 1 for monitor, 100 for updates
            # Start the idle transaction (Session 1)
            future1 = executor.submit(session1_idle_transaction)

            # Start the monitoring session
            future_monitor = executor.submit(session3_monitor)

            # Wait a bit before starting Session 2 instances
            time.sleep(2)

            # Submit 1 bulk update tasks
            update_futures = []
            for i in range(1):
                future = executor.submit(session2_bulk_update, i+1)
                update_futures.append(future)
                time.sleep(60)  # Small delay between submissions

            # Wait for all updates to complete
            for future in update_futures:
                future.result()

            # Print final statistics
            log_message("Main", "\nFinal Statistics:")
            print("=" * 50)
            print(f"Successful updates: {update_stats['successful']}")
            print(f"Failed updates: {update_stats['failed']}")
            print(f"Lock timeouts: {update_stats['lock_timeout']}")
            print("=" * 50)

    except KeyboardInterrupt:
        log_message("Main", "Received interrupt signal")
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()