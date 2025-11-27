import psycopg2
from concurrent.futures import ThreadPoolExecutor
import time
from dotenv import load_dotenv
import os
import sys
from datetime import datetime

# ============================================================================
# Database Connection Load Tester
# ============================================================================

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

def print_banner():
    """Print application banner"""
    print("\n" + "="*80)
    print(" 🔥 DATABASE LOAD TESTING TOOL")
    print("="*80)
    print(f" 📅 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def print_summary(stats):
    """Print execution summary"""
    print("\n" + "="*80)
    print(" 📊 EXECUTION SUMMARY")
    print("="*80)
    print(f" ✓ Total Sessions      : {stats['total_sessions']}")
    print(f" ✓ Successful Sessions : {stats['successful']}")
    print(f" ✗ Failed Sessions     : {stats['failed']}")
    print(f" ⏱  Total Duration     : {stats['duration']:.2f} seconds")
    if stats['total_sessions'] > 0:
        print(f" 📈 Success Rate       : {(stats['successful']/stats['total_sessions']*100):.1f}%")
    print("="*80)
    print(f" 🏁 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80 + "\n")

def log_message(session, message, level='INFO'):
    """
    Helper function to print formatted log messages
    
    Args:
        session: Session identifier
        message: Log message
        level: Log level (INFO, SUCCESS, ERROR, WARNING, etc.)
    """
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
    
    icons = {
        'INFO': '📘',
        'SUCCESS': '✅',
        'ERROR': '❌',
        'WARNING': '⚠️',
        'PROGRESS': '⚙️',
        'START': '🚀',
        'FINISH': '🎯'
    }
    
    icon = icons.get(level, '📝')
    print(f"[{timestamp}] {icon} [{session:^15}] {message}")

def run_query(iteration):
    """
    Execute multiple queries in single transaction
    
    Args:
        iteration: Session number
        
    Returns:
        dict: Execution statistics
    """
    session_name = f"Session-{iteration:02d}"
    start_time = time.time()
    
    conn = None
    cur = None
    
    try:
        log_message(session_name, "Establishing database connection...", 'START')
        conn = psycopg2.connect(**db_params)
        conn.autocommit = False  # Ensure we're in a transaction
        cur = conn.cursor()
        
        log_message(session_name, "Connection established successfully", 'SUCCESS')
        
        cur.execute("SET statement_timeout = '300s';")
        log_message(session_name, "Statement timeout set to 300s", 'INFO')
        
        cur.execute("BEGIN;")
        log_message(session_name, "Transaction started", 'INFO')
        
        query = """
        SELECT count(*) 
        FROM generate_series(1, 10000) a, 
             generate_series(1, 100000) b 
        WHERE a > b;
        """
        
        # Run query multiple times in same transaction
        for i in range(3):
            query_start = time.time()
            log_message(session_name, f"Executing query {i+1}/3...", 'PROGRESS')
            
            cur.execute(query)
            result = cur.fetchone()
            query_duration = time.time() - query_start
            
            log_message(session_name, 
                       f"Query {i+1}/3 completed in {query_duration:.2f}s | Result: {result[0]:,} rows", 
                       'SUCCESS')
        
        conn.commit()
        total_duration = time.time() - start_time
        log_message(session_name, 
                   f"Transaction committed successfully | Total time: {total_duration:.2f}s", 
                   'FINISH')
        
        return {'success': True, 'duration': total_duration, 'session': session_name}
        
    except Exception as e:
        total_duration = time.time() - start_time
        error_msg = str(e)[:100] + ('...' if len(str(e)) > 100 else '')
        log_message(session_name, f"Error: {error_msg}", 'ERROR')
        
        try:
            if conn:
                conn.rollback()
                log_message(session_name, "Transaction rolled back", 'WARNING')
        except Exception as rollback_error:
            log_message(session_name, f"Rollback failed: {rollback_error}", 'ERROR')
        
        return {'success': False, 'duration': total_duration, 'session': session_name}
        
    finally:
        try:
            if cur:
                cur.close()
            if conn:
                conn.close()
            log_message(session_name, "Connection closed", 'INFO')
        except Exception as e:
            log_message(session_name, f"Error closing connection: {e}", 'WARNING')

def main():
    """Main execution function"""
    print_banner()
    
    num_connections = int(os.getenv('NUM_CONNECTIONS', 2))
    
    log_message("MAIN", f"Starting load test with {num_connections} parallel connections", 'INFO')
    log_message("MAIN", f"Target: {db_params['user']}@{db_params['host']}:{db_params['port']}/{db_params['dbname']}", 'INFO')
    print()
    
    start_time = time.time()
    results = []
    
    try:
        log_message("MAIN", f"Launching {num_connections} worker threads...", 'START')
        print()
        
        with ThreadPoolExecutor(max_workers=num_connections) as executor:
            futures = [
                executor.submit(run_query, i+1)
                for i in range(num_connections)
            ]
            
            for future in futures:
                result = future.result()
                results.append(result)
        
        # Calculate statistics
        total_duration = time.time() - start_time
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        stats = {
            'total_sessions': num_connections,
            'successful': successful,
            'failed': failed,
            'duration': total_duration
        }
        
        print_summary(stats)
        
        log_message("MAIN", "All queries completed", 'FINISH')
        
    except KeyboardInterrupt:
        print("\n")
        log_message("MAIN", "Received interrupt signal (Ctrl+C)", 'WARNING')
        log_message("MAIN", "Shutting down gracefully...", 'WARNING')
        sys.exit(130)
        
    except Exception as e:
        log_message("MAIN", f"Fatal error: {str(e)}", 'ERROR')
        sys.exit(1)
        
    finally:
        sys.exit(0)

if __name__ == "__main__":
    main()