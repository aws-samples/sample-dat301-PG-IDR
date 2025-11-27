#!/usr/bin/env python3
"""
Postgres Query Provider MCP Server
Provides PostgreSQL diagnostic queries and workflows that can be executed
through the PostgreSQL MCP server's run_query tool.
"""
import json
import boto3
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP
from typing import List, Dict, Optional

mcp = FastMCP("Postgres-Query-Provider")

@mcp.tool()
def analyze_user_intent(user_query: str) -> dict:
    """
    Analyze user query to suggest appropriate workflows and detect multi-workflow scenarios
    
    Args:
        user_query: The user's diagnostic question
        
    Returns:
        Analysis of intent with workflow recommendations
    """
    query_lower = user_query.lower()
    
    # Define workflow triggers with confidence scores
    workflow_triggers = {
        'vacuum_analysis_diagnostic': {
            'keywords': ['vacuum', 'bloat', 'autovacuum', 'dead tuple', 'removable cutoff'],
            'patterns': ['vacuum.*not.*working', 'autovacuum.*blocked', 'table.*bloated'],
            'confidence': 0
        },
        'query_performance_diagnostic': {
            'keywords': ['slow', 'performance', 'explain', 'index', 'stats', 'query.*slow'],
            'patterns': ['query.*running.*slow', 'performance.*bad', 'explain.*plan'],
            'confidence': 0
        },
        'lock_analysis_diagnostic': {
            'keywords': ['lock', 'blocking', 'blocked', 'deadlock'],
            'patterns': ['blocking.*query', 'lock.*contention', 'sessions.*blocked'],
            'confidence': 0
        },
        'connection_analysis_diagnostic': {
            'keywords': ['connection', 'session', 'too many connections'],
            'patterns': ['connection.*limit', 'too.*many.*connection', 'session.*analysis'],
            'confidence': 0
        }
    }
    
    # Calculate confidence scores
    import re
    for workflow, triggers in workflow_triggers.items():
        score = 0
        
        # Keyword matching
        for keyword in triggers['keywords']:
            if '.*' in keyword:
                if re.search(keyword, query_lower):
                    score += 2
            else:
                if keyword in query_lower:
                    score += 1
        
        # Pattern matching (higher weight)
        for pattern in triggers['patterns']:
            if re.search(pattern, query_lower):
                score += 3
        
        triggers['confidence'] = score
    
    # Sort by confidence
    sorted_workflows = sorted(workflow_triggers.items(), 
                            key=lambda x: x[1]['confidence'], 
                            reverse=True)
    
    # Filter workflows with confidence > 0
    recommended_workflows = [(name, data) for name, data in sorted_workflows if data['confidence'] > 0]
    
    # Determine scenario type
    if len(recommended_workflows) == 0:
        scenario = "custom_query_needed"
        primary_workflow = None
    elif len(recommended_workflows) == 1:
        scenario = "single_workflow"
        primary_workflow = recommended_workflows[0][0]
    else:
        scenario = "multi_workflow"
        primary_workflow = recommended_workflows[0][0]  # Highest confidence
    
    return {
        "user_query": user_query,
        "scenario_type": scenario,
        "primary_workflow": primary_workflow,
        "all_recommended_workflows": [name for name, _ in recommended_workflows],
        "workflow_confidence_scores": {name: data['confidence'] for name, data in recommended_workflows},
        "execution_strategy": {
            "single_workflow": "Execute primary workflow only",
            "multi_workflow": "Execute primary workflow, then supplement with secondary workflows",
            "custom_query_needed": "No workflow match - use custom queries"
        }.get(scenario, "unknown"),
        "recommended_approach": f"Primary: {primary_workflow}" if primary_workflow else "Custom analysis required"
    }

@mcp.tool()
def orchestrate_mcp_servers(user_query: str, scenario_type: str = "unknown") -> dict:
    """
    Intelligent MCP server orchestration for complex diagnostic scenarios
    
    Args:
        user_query: The user's diagnostic question
        scenario_type: Type of scenario (performance, infrastructure, logs, configuration, etc.)
        
    Returns:
        Orchestration plan with specific MCP server usage strategy
    """
    
    query_lower = user_query.lower()
    
    # Define orchestration patterns for different scenarios
    orchestration_patterns = {
        'performance_deep_dive': {
            'triggers': ['slow', 'performance', 'cpu', 'memory', 'io', 'bottleneck'],
            'servers': ['postgres_query_provider', 'postgres', 'performance_insights', 'cloudwatch'],
            'sequence': [
                {'server': 'postgres_query_provider', 'action': 'query_performance_diagnostic()', 'purpose': 'Get structured diagnostic steps'},
                {'server': 'postgres', 'action': 'run_query()', 'purpose': 'Execute database performance queries'},
                {'server': 'performance_insights', 'action': 'get_top_sql()', 'purpose': 'Get Performance Insights top SQL'},
                {'server': 'performance_insights', 'action': 'get_resource_metrics()', 'purpose': 'Get CPU/memory/IO metrics'},
                {'server': 'cloudwatch', 'action': 'get_log_events()', 'purpose': 'Search for slow query logs'},
                {'server': 'cloudwatch', 'action': 'get_metric_statistics()', 'purpose': 'Get CloudWatch database metrics'}
            ]
        },
        'infrastructure_analysis': {
            'triggers': ['cluster', 'instance', 'configuration', 'parameter', 'setting', 'infrastructure'],
            'servers': ['aws_api', 'postgres', 'cloudwatch', 'aws_docs'],
            'sequence': [
                {'server': 'aws_api', 'action': 'describe_db_clusters()', 'purpose': 'Get RDS cluster configuration'},
                {'server': 'aws_api', 'action': 'describe_db_instances()', 'purpose': 'Get instance details and status'},
                {'server': 'postgres', 'action': 'run_query(pg_settings)', 'purpose': 'Check PostgreSQL configuration'},
                {'server': 'cloudwatch', 'action': 'get_metric_statistics()', 'purpose': 'Get infrastructure metrics'},
                {'server': 'aws_docs', 'action': 'search_documentation()', 'purpose': 'Find configuration best practices'}
            ]
        },
        'log_forensics': {
            'triggers': ['log', 'error', 'fatal', 'crash', 'restart', 'forensic'],
            'servers': ['cloudwatch', 'postgres_query_provider', 'postgres', 'aws_api'],
            'sequence': [
                {'server': 'postgres_query_provider', 'action': 'get_vacuum_log_analysis_queries()', 'purpose': 'Get log search patterns'},
                {'server': 'cloudwatch', 'action': 'get_log_events(ERROR|FATAL)', 'purpose': 'Search for error logs'},
                {'server': 'cloudwatch', 'action': 'get_log_events(duration)', 'purpose': 'Find slow query logs'},
                {'server': 'postgres', 'action': 'run_query(pg_stat_activity)', 'purpose': 'Check current database state'},
                {'server': 'aws_api', 'action': 'describe_db_clusters()', 'purpose': 'Check cluster events and status'}
            ]
        },
        'security_audit': {
            'triggers': ['security', 'permission', 'role', 'user', 'auth', 'audit'],
            'servers': ['postgres', 'aws_api', 'cloudwatch', 'aws_docs'],
            'sequence': [
                {'server': 'postgres', 'action': 'run_query(pg_roles)', 'purpose': 'Check database roles and permissions'},
                {'server': 'postgres', 'action': 'run_query(pg_hba_file_rules)', 'purpose': 'Check authentication rules'},
                {'server': 'aws_api', 'action': 'describe_db_clusters()', 'purpose': 'Check RDS security configuration'},
                {'server': 'cloudwatch', 'action': 'get_log_events(authentication)', 'purpose': 'Search for auth-related logs'},
                {'server': 'aws_docs', 'action': 'search_documentation(security)', 'purpose': 'Find security best practices'}
            ]
        },
        'replication_analysis': {
            'triggers': ['replication', 'replica', 'standby', 'wal', 'lag', 'streaming'],
            'servers': ['postgres', 'cloudwatch', 'aws_api', 'performance_insights'],
            'sequence': [
                {'server': 'postgres', 'action': 'run_query(pg_stat_replication)', 'purpose': 'Check replication status'},
                {'server': 'postgres', 'action': 'run_query(pg_replication_slots)', 'purpose': 'Check replication slots'},
                {'server': 'cloudwatch', 'action': 'get_metric_statistics(ReplicaLag)', 'purpose': 'Get replication lag metrics'},
                {'server': 'aws_api', 'action': 'describe_db_clusters()', 'purpose': 'Check cluster replication config'},
                {'server': 'performance_insights', 'action': 'get_resource_metrics()', 'purpose': 'Check replication performance impact'}
            ]
        }
    }
    
    # Determine best orchestration pattern
    best_pattern = None
    max_matches = 0
    
    for pattern_name, pattern_config in orchestration_patterns.items():
        matches = sum(1 for trigger in pattern_config['triggers'] if trigger in query_lower)
        if matches > max_matches:
            max_matches = matches
            best_pattern = pattern_name
    
    # Default to performance analysis if no specific pattern matches
    if not best_pattern or max_matches == 0:
        best_pattern = 'performance_deep_dive'
    
    selected_pattern = orchestration_patterns[best_pattern]
    
    return {
        "user_query": user_query,
        "selected_orchestration": best_pattern,
        "confidence_score": max_matches,
        "servers_to_use": selected_pattern['servers'],
        "execution_sequence": selected_pattern['sequence'],
        "orchestration_strategy": f"Multi-server {best_pattern.replace('_', ' ')} approach",
        "expected_insights": {
            'performance_deep_dive': "Comprehensive performance analysis with database queries, metrics, and logs",
            'infrastructure_analysis': "Infrastructure configuration review with AWS API and documentation",
            'log_forensics': "Deep log analysis with pattern matching and correlation",
            'security_audit': "Security posture assessment with permissions and configuration review",
            'replication_analysis': "Replication health check with lag analysis and configuration review"
        }.get(best_pattern, "Custom diagnostic approach"),
        "estimated_steps": len(selected_pattern['sequence']),
        "complexity": "high" if len(selected_pattern['sequence']) > 4 else "medium"
    }

@mcp.tool()
def suggest_custom_diagnostic_approach(user_query: str, context: str = "") -> dict:
    """
    Suggest a custom diagnostic approach for scenarios not covered by existing workflows
    
    Args:
        user_query: The user's question that didn't match existing workflows
        context: Additional context about the database or environment
        
    Returns:
        Suggested diagnostic steps and queries for unknown scenarios
    """
    
    # Analyze the query for database concepts
    query_lower = user_query.lower()
    
    # Common PostgreSQL diagnostic areas
    diagnostic_areas = {
        'configuration': ['config', 'setting', 'parameter', 'postgresql.conf'],
        'replication': ['replica', 'standby', 'streaming', 'wal', 'lag'],
        'backup_recovery': ['backup', 'restore', 'recovery', 'pitr', 'archive'],
        'security': ['permission', 'role', 'user', 'grant', 'security', 'auth'],
        'storage': ['disk', 'space', 'tablespace', 'storage', 'size'],
        'memory': ['memory', 'shared_buffers', 'work_mem', 'oom'],
        'network': ['network', 'connection', 'timeout', 'ssl'],
        'extensions': ['extension', 'plugin', 'module'],
        'partitioning': ['partition', 'partitioned', 'inheritance'],
        'statistics': ['statistics', 'analyze', 'histogram', 'correlation'],
        'maintenance': ['maintenance', 'checkpoint', 'wal', 'cleanup'],
        'monitoring': ['monitor', 'alert', 'metric', 'dashboard']
    }
    
    # Find relevant areas
    relevant_areas = []
    for area, keywords in diagnostic_areas.items():
        if any(keyword in query_lower for keyword in keywords):
            relevant_areas.append(area)
    
    # Generate custom diagnostic steps based on detected areas
    custom_steps = []
    
    if 'configuration' in relevant_areas:
        custom_steps.extend([
            {
                "step": "Check PostgreSQL configuration settings",
                "tool": "run_query",
                "query": "SELECT name, setting, unit, context, short_desc FROM pg_settings WHERE name ILIKE '%{}%' ORDER BY name;".format('%'),
                "description": "Review current PostgreSQL configuration"
            }
        ])
    
    if 'replication' in relevant_areas:
        custom_steps.extend([
            {
                "step": "Check replication status and lag",
                "tool": "run_query", 
                "query": "SELECT * FROM pg_stat_replication;",
                "description": "Analyze replication connections and lag"
            },
            {
                "step": "Check replication slots",
                "tool": "run_query",
                "query": "SELECT slot_name, slot_type, database, active, xmin, restart_lsn FROM pg_replication_slots;",
                "description": "Review replication slot status"
            }
        ])
    
    if 'security' in relevant_areas:
        custom_steps.extend([
            {
                "step": "Check database roles and permissions",
                "tool": "run_query",
                "query": "SELECT rolname, rolsuper, rolinherit, rolcreaterole, rolcreatedb, rolcanlogin FROM pg_roles ORDER BY rolname;",
                "description": "Review database roles and privileges"
            }
        ])
    
    if 'storage' in relevant_areas:
        custom_steps.extend([
            {
                "step": "Analyze database and table sizes",
                "tool": "run_query",
                "query": """
                    SELECT 
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as total_size,
                        pg_size_pretty(pg_relation_size(schemaname||'.'||tablename)) as table_size,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename) - pg_relation_size(schemaname||'.'||tablename)) as index_size
                    FROM pg_tables 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog')
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC
                    LIMIT 20;
                """,
                "description": "Check largest tables and their storage usage"
            }
        ])
    
    # Default exploratory steps if no specific area detected
    if not custom_steps:
        custom_steps = [
            {
                "step": "General database activity overview",
                "tool": "run_query",
                "query": """
                    SELECT 
                        datname,
                        numbackends,
                        xact_commit,
                        xact_rollback,
                        blks_read,
                        blks_hit,
                        tup_returned,
                        tup_fetched,
                        tup_inserted,
                        tup_updated,
                        tup_deleted
                    FROM pg_stat_database 
                    WHERE datname NOT IN ('template0', 'template1')
                    ORDER BY numbackends DESC;
                """,
                "description": "Get overall database activity and statistics"
            },
            {
                "step": "Check current database activity",
                "tool": "run_query",
                "query": """
                    SELECT 
                        pid,
                        datname,
                        usename,
                        application_name,
                        state,
                        EXTRACT(EPOCH FROM (now() - query_start))::integer AS query_duration_seconds,
                        LEFT(query, 100) AS query_preview
                    FROM pg_stat_activity 
                    WHERE state != 'idle' 
                    AND pid != pg_backend_pid()
                    ORDER BY query_start;
                """,
                "description": "Review current active sessions and queries"
            }
        ]
    
    # Add log analysis suggestions
    log_suggestions = []
    if 'error' in query_lower or 'fail' in query_lower:
        log_suggestions.append({
            "tool": "get_log_events",
            "pattern": "ERROR|FATAL|PANIC",
            "description": "Search for error messages in PostgreSQL logs"
        })
    
    if 'performance' in query_lower or 'slow' in query_lower:
        log_suggestions.append({
            "tool": "get_log_events", 
            "pattern": "duration.*ms",
            "description": "Find slow query logs"
        })
    
    return {
        "user_query": user_query,
        "detected_areas": relevant_areas,
        "custom_diagnostic_steps": custom_steps,
        "log_analysis_suggestions": log_suggestions,
        "recommended_approach": "Execute custom diagnostic steps, then analyze results to build understanding",
        "next_steps": [
            "Execute the suggested diagnostic queries",
            "Analyze results for patterns or anomalies", 
            "Search logs for related events if needed",
            "Consider creating a new workflow if this becomes a common scenario"
        ],
        "workflow_creation_suggestion": {
            "should_create_workflow": len(custom_steps) >= 3,
            "suggested_workflow_name": f"custom_{relevant_areas[0] if relevant_areas else 'general'}_diagnostic",
            "rationale": "This scenario has enough complexity to warrant a dedicated workflow"
        }
    }

@mcp.tool()
def list_available_workflows() -> list[dict]:
    """
    List all available diagnostic workflows in the Postgres Query Provider.
    
    Returns:
        List of available workflow functions with descriptions
    """
    return [
        {
            "name": "vacuum_analysis_diagnostic",
            "description": "Comprehensive vacuum and bloat analysis workflow",
            "use_case": "Check vacuum status, identify bloated tables, analyze autovacuum settings, find vacuum blockers"
        },
        {
            "name": "query_performance_diagnostic", 
            "description": "Query performance and explain plan analysis workflow",
            "use_case": "Analyze slow queries, table statistics, index usage, and performance bottlenecks"
        },
        {
            "name": "lock_analysis_diagnostic", 
            "description": "Database lock contention analysis workflow",
            "use_case": "Identify blocking queries, analyze lock waits and contention"
        },
        {
            "name": "slow_query_diagnostic",
            "description": "Slow query performance analysis workflow", 
            "use_case": "Identify slow queries, analyze query performance patterns"
        },
        {
            "name": "connection_analysis_diagnostic",
            "description": "Database connection and session analysis workflow",
            "use_case": "Analyze connections, identify long-running transactions"
        }
    ]

class PostgreSQLRunbooks:
    """PostgreSQL diagnostic runbooks with predefined queries"""

    @staticmethod
    def get_slow_query_diagnostic(DatabaseInstance: Optional[str] = None) -> List[Dict[str, str]]:
        """Returns comprehensive diagnostic steps for slow query analysis including vacuum and lock root causes"""
        return [
            {
                "step": "Check currently running slow queries and their blocking status",
                "tool": "run_query",
                "action": "Identify slow queries and check if they're blocked by locks or waiting",
                "query": """
                    SELECT 
                        datname, 
                        pid, 
                        usename, 
                        application_name, 
                        client_addr, 
                        state,
                        wait_event_type,
                        wait_event,
                        EXTRACT(EPOCH FROM (now() - query_start))::integer AS duration_seconds,
                        EXTRACT(EPOCH FROM (now() - xact_start))::integer AS xact_duration_seconds,
                        CASE 
                            WHEN wait_event_type = 'Lock' THEN 'BLOCKED - Waiting for lock'
                            WHEN wait_event_type = 'IO' THEN 'IO BOUND - Disk/network wait'
                            WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'LONG TRANSACTION - May block vacuum'
                            WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 1800 THEN 'MODERATE TRANSACTION - Monitor for vacuum impact'
                            ELSE 'ACTIVE'
                        END as query_status,
                        CASE
                            WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'CRITICAL - Long transaction blocking vacuum'
                            WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 1800 THEN 'WARNING - Transaction may impact vacuum'
                            WHEN wait_event_type = 'Lock' THEN 'BLOCKED - Query waiting for lock'
                            ELSE 'ACTIVE - Normal operation'
                        END as vacuum_impact_assessment,
                        LEFT(query, 150) AS query_preview
                    FROM pg_stat_activity 
                    WHERE backend_type = 'client backend' 
                    AND state = 'active' 
                    AND EXTRACT(EPOCH FROM (now() - query_start)) > 30
                    ORDER BY duration_seconds DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Analyze vacuum blockers that may cause slow queries",
                "tool": "run_query",
                "action": "Find transactions blocking vacuum, which leads to table bloat and slow queries",
                "query": """
                    WITH potential_vacuum_blockers AS (
                        SELECT 
                            pid,
                            datname,
                            usename,
                            application_name,
                            state,
                            EXTRACT(EPOCH FROM (now() - query_start))::integer AS query_duration_seconds,
                            EXTRACT(EPOCH FROM (now() - xact_start))::integer AS xact_duration_seconds,
                            xact_start,
                            query_start,
                            LEFT(query, 100) AS query_preview,
                            CASE
                                WHEN state = 'idle in transaction' THEN 'CRITICAL - Idle in transaction (blocks vacuum immediately)'
                                WHEN state = 'idle in transaction (aborted)' THEN 'CRITICAL - Aborted transaction (blocks vacuum)'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'CRITICAL - Long transaction >1hr (causes severe bloat)'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 1800 THEN 'WARNING - Long transaction >30min (causes bloat)'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 900 THEN 'MODERATE - Transaction >15min (monitor for vacuum impact)'
                                ELSE 'OK'
                            END as vacuum_impact,
                            CASE
                                WHEN state = 'idle in transaction' THEN 'TERMINATE_IMMEDIATELY'
                                WHEN state = 'idle in transaction (aborted)' THEN 'TERMINATE_IMMEDIATELY'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'CONSIDER_TERMINATING'
                                ELSE 'MONITOR'
                            END as recommended_action
                        FROM pg_stat_activity
                        WHERE (state != 'idle' OR state LIKE '%in transaction%')
                        AND xact_start IS NOT NULL
                        AND backend_type = 'client backend'
                        AND pid != pg_backend_pid()
                    )
                    SELECT 
                        pid,
                        datname,
                        usename,
                        application_name,
                        state,
                        query_duration_seconds,
                        xact_duration_seconds,
                        vacuum_impact,
                        recommended_action,
                        query_preview,
                        CASE 
                            WHEN vacuum_impact LIKE 'CRITICAL%' THEN 'YES - This transaction is likely causing table bloat and slow queries'
                            WHEN vacuum_impact LIKE 'WARNING%' THEN 'POSSIBLY - This transaction may contribute to performance issues'
                            ELSE 'NO - Transaction is not blocking vacuum'
                        END as slow_query_cause
                    FROM potential_vacuum_blockers
                    WHERE vacuum_impact != 'OK'
                    ORDER BY xact_duration_seconds DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check table bloat levels that cause slow query performance",
                "tool": "run_query",
                "action": "Identify tables with high bloat that are causing slow queries due to lack of vacuum",
                "query": """
                    SELECT 
                        schemaname,
                        relname as table_name,
                        n_live_tup,
                        n_dead_tup,
                        round((n_dead_tup::numeric/nullif(n_live_tup+n_dead_tup,0))* 100,2) AS dead_tuple_percent,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        last_vacuum,
                        last_autovacuum,
                        vacuum_count,
                        autovacuum_count,
                        CASE 
                            WHEN last_vacuum IS NULL AND last_autovacuum IS NULL THEN 'NEVER VACUUMED'
                            WHEN EXTRACT(EPOCH FROM (now() - COALESCE(last_autovacuum, last_vacuum)))/3600 > 48 THEN 'VACUUM OVERDUE (>48h)'
                            WHEN EXTRACT(EPOCH FROM (now() - COALESCE(last_autovacuum, last_vacuum)))/3600 > 24 THEN 'VACUUM OVERDUE (>24h)'
                            ELSE 'RECENTLY VACUUMED'
                        END as vacuum_status,
                        CASE 
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.3 THEN 'CRITICAL - Severe bloat causing very slow queries'
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.2 THEN 'HIGH - Significant bloat causing slow queries'
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.1 THEN 'MODERATE - Some bloat may affect performance'
                            WHEN seq_scan > idx_scan * 5 AND n_live_tup > 1000 THEN 'INDEX ISSUE - Too many sequential scans'
                            ELSE 'OK'
                        END as performance_impact,
                        CASE 
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.2 THEN 'URGENT VACUUM NEEDED'
                            WHEN seq_scan > idx_scan * 5 AND n_live_tup > 1000 THEN 'INDEX ANALYSIS NEEDED'
                            ELSE 'Monitor'
                        END as recommended_action
                    FROM pg_stat_user_tables 
                    WHERE n_live_tup > 1000  -- Focus on tables with significant data
                    AND (
                        n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.1 
                        OR seq_scan > idx_scan * 5
                        OR last_vacuum IS NULL 
                        OR last_autovacuum IS NULL
                    )
                    ORDER BY 
                        CASE 
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.3 THEN 1
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.2 THEN 2
                            WHEN seq_scan > idx_scan * 5 THEN 3
                            ELSE 4
                        END,
                        n_dead_tup DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Identify top SQL queries by execution time and resource consumption",
                "tool": "run_query", 
                "action": "Use pg_stat_statements to find slow queries and correlate with table access patterns",
                "query": """
                    SELECT
                        LEFT(query, 150) AS query_preview,
                        calls,
                        round(total_exec_time::NUMERIC, 2) AS total_time,
                        round((total_exec_time / calls)::NUMERIC, 2) AS avg_time_ms,
                        round(
                            (
                            (
                                100.0 * total_exec_time / sum(total_exec_time) OVER ()
                            )
                            )::NUMERIC,
                            2
                        ) AS percent_total_time,
                        rows,
                        round(rows::NUMERIC / calls, 2) AS avg_rows_per_call,
                        shared_blks_hit,
                        shared_blks_read,
                        shared_blks_dirtied,
                        shared_blks_written,
                        CASE
                            WHEN shared_blks_hit + shared_blks_read > 0 THEN round(
                            (
                                shared_blks_hit::NUMERIC / (shared_blks_hit + shared_blks_read)
                            ) * 100,
                            2
                            )
                            ELSE 0
                        END AS cache_hit_percent,
                        CASE
                            WHEN total_exec_time / calls > 5000 THEN 'VERY SLOW - Avg >5s per call'
                            WHEN total_exec_time / calls > 1000 THEN 'SLOW - Avg >1s per call'
                            WHEN shared_blks_read > shared_blks_hit THEN 'I/O INTENSIVE - Low cache hit ratio'
                            WHEN calls > 10000
                            AND total_exec_time / calls > 100 THEN 'HIGH FREQUENCY SLOW QUERY'
                            WHEN rows::NUMERIC / calls > 100000 THEN 'LARGE RESULT SET - May need optimization'
                            ELSE 'OK'
                        END AS performance_classification,
                        CASE
                            WHEN shared_blks_read > shared_blks_hit THEN 'Check for table bloat, missing indexes, or need for vacuum'
                            WHEN total_exec_time / calls > 1000 THEN 'Analyze query plan, check for locks, vacuum status'
                            WHEN rows::NUMERIC / calls > 100000 THEN 'Consider query optimization, indexing, or partitioning'
                            ELSE 'Monitor'
                        END AS optimization_suggestion
                        FROM pg_stat_statements
                        WHERE calls > 5
                        ORDER BY total_exec_time DESC
                        LIMIT 20;
                """,
                "DatabaseInstance": DatabaseInstance
            }
        ]

    @staticmethod
    def get_lock_analysis_diagnostic(DatabaseInstance: Optional[str] = None) -> List[Dict[str, str]]:
        """Returns diagnostic steps for lock contention analysis"""
        return [
            {
                "step": "Check current locks and blocking queries",
                "tool": "run_query",
                "action": "Identify current locks and which queries are blocking others",
                "query": """
                    SELECT 
                        blocked_locks.pid AS blocked_pid,
                        blocked_activity.usename AS blocked_user,
                        blocking_locks.pid AS blocking_pid,
                        blocking_activity.usename AS blocking_user,
                        blocked_activity.query AS blocked_statement,
                        blocking_activity.query AS current_statement_in_blocking_process,
                        blocked_activity.application_name AS blocked_application,
                        blocking_activity.application_name AS blocking_application
                    FROM pg_catalog.pg_locks blocked_locks
                    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                    JOIN pg_catalog.pg_locks blocking_locks 
                        ON blocking_locks.locktype = blocked_locks.locktype
                        AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                        AND blocking_locks.pid != blocked_locks.pid
                    JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                    WHERE NOT blocked_locks.granted;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check lock wait events and durations",
                "tool": "run_query",
                "action": "Analyze current lock wait events and their durations",
                "query": """
                    SELECT 
                        pid,
                        usename,
                        application_name,
                        state,
                        wait_event_type,
                        wait_event,
                        EXTRACT(EPOCH FROM (now() - query_start))::integer AS query_duration_seconds,
                        query
                    FROM pg_stat_activity 
                    WHERE wait_event_type = 'Lock' 
                    AND state = 'active'
                    ORDER BY query_duration_seconds DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            }
        ]

    @staticmethod
    def get_vacuum_analysis_diagnostic(DatabaseInstance: Optional[str] = None) -> List[Dict[str, str]]:
        """Returns comprehensive diagnostic steps for vacuum and bloat analysis"""
        return [
            {
                "step": "PRIORITY: Detect and terminate vacuum blockers immediately",
                "tool": "run_query",
                "action": "Find and provide termination commands for all vacuum blockers",
                "query": """
                    -- IMMEDIATE VACUUM BLOCKER DETECTION AND TERMINATION
                    WITH all_vacuum_blockers AS (
                        SELECT 
                            'IDLE_IN_TRANSACTION' as blocker_type,
                            pid,
                            datname,
                            usename,
                            application_name,
                            state,
                            EXTRACT(EPOCH FROM (now() - state_change))::integer AS idle_duration_seconds,
                            'TERMINATE_IMMEDIATELY' as recommended_action,
                            'CRITICAL - Idle in transaction blocking vacuum' as severity,
                            LEFT(query, 100) AS query_preview
                        FROM pg_stat_activity
                        WHERE state = 'idle in transaction'
                        AND backend_type = 'client backend'
                        AND pid != pg_backend_pid()
                        
                        UNION ALL
                        
                        SELECT 
                            'LONG_TRANSACTION' as blocker_type,
                            pid,
                            datname,
                            usename,
                            application_name,
                            state,
                            EXTRACT(EPOCH FROM (now() - xact_start))::integer AS idle_duration_seconds,
                            CASE 
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'TERMINATE_RECOMMENDED'
                                ELSE 'MONITOR_CLOSELY'
                            END as recommended_action,
                            CASE 
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'CRITICAL - Long transaction >1hr'
                                ELSE 'WARNING - Long transaction >5min'
                            END as severity,
                            LEFT(query, 100) AS query_preview
                        FROM pg_stat_activity
                        WHERE state != 'idle'
                        AND xact_start IS NOT NULL
                        AND EXTRACT(EPOCH FROM (now() - xact_start)) > 300
                        AND backend_type = 'client backend'
                        AND pid != pg_backend_pid()
                    )
                    SELECT 
                        blocker_type,
                        pid,
                        datname,
                        usename,
                        application_name,
                        state,
                        idle_duration_seconds,
                        severity,
                        recommended_action,
                        query_preview,
                        CASE 
                            WHEN blocker_type = 'IDLE_IN_TRANSACTION' THEN 'TERMINATE IMMEDIATELY - This is blocking vacuum'
                            WHEN idle_duration_seconds > 3600 THEN 'TERMINATE RECOMMENDED - Long running transaction'
                            ELSE 'MONITOR - May be legitimate long operation'
                        END as recommendation
                    FROM all_vacuum_blockers
                    ORDER BY 
                        CASE 
                            WHEN blocker_type = 'IDLE_IN_TRANSACTION' THEN 1
                            WHEN idle_duration_seconds > 3600 THEN 2
                            ELSE 3
                        END,
                        idle_duration_seconds DESC;
                """,
                "DatabaseInstance": DatabaseInstance,
                "next_action": "After terminating blockers, proceed to execute VACUUM VERBOSE"
            },
            {
                "step": "Check current vacuum progress",
                "tool": "run_query",
                "action": "Monitor current vacuum operations and their progress",
                "query": """
                    SELECT 
                        p.pid,
                        EXTRACT(EPOCH FROM (now() - a.xact_start))::integer AS duration_seconds,
                        p.datname AS database,
                        CASE 
                            WHEN p.relid IS NOT NULL THEN p.relid::regclass::text
                            ELSE 'N/A'
                        END AS table_name,
                        p.phase,
                        a.query,
                        round(100.0 * p.heap_blks_scanned / p.heap_blks_total, 1) AS scanned_pct,
                        round(100.0 * p.heap_blks_vacuumed / p.heap_blks_total, 1) AS vacuumed_pct
                    FROM pg_stat_progress_vacuum p 
                    JOIN pg_stat_activity a USING (pid)
                    ORDER BY duration_seconds DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check tables with high dead tuple ratio and vacuum status",
                "tool": "run_query",
                "action": "Identify tables with bloat and analyze vacuum patterns",
                "query": """
                    SELECT 
                        schemaname, 
                        relname, 
                        last_vacuum, 
                        last_autovacuum, 
                        n_live_tup, 
                        n_dead_tup, 
                        round((n_dead_tup::numeric/nullif(n_live_tup+n_dead_tup,0))* 100,2) AS dead_tuple_percent,
                        vacuum_count,
                        autovacuum_count,
                        CASE 
                            WHEN last_vacuum IS NULL AND last_autovacuum IS NULL THEN 'NEVER VACUUMED'
                            WHEN last_autovacuum IS NULL THEN 'NO AUTOVACUUM'
                            WHEN EXTRACT(EPOCH FROM (now() - COALESCE(last_autovacuum, last_vacuum)))/3600 > 24 THEN 'VACUUM OVERDUE'
                            ELSE 'OK'
                        END as vacuum_status
                    FROM pg_stat_user_tables 
                    WHERE n_dead_tup > 1000 OR n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.1
                    ORDER BY dead_tuple_percent DESC NULLS LAST, n_dead_tup DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check autovacuum settings and thresholds",
                "tool": "run_query",
                "action": "Analyze autovacuum configuration that might prevent vacuum execution",
                "query": """
                    SELECT 
                        name,
                        setting,
                        unit,
                        context,
                        short_desc
                    FROM pg_settings 
                    WHERE name LIKE '%autovacuum%' 
                       OR name LIKE '%vacuum%cost%'
                       OR name LIKE '%vacuum%delay%'
                       OR name = 'track_counts'
                    ORDER BY 
                        CASE 
                            WHEN name = 'autovacuum' THEN 1
                            WHEN name = 'track_counts' THEN 2
                            WHEN name LIKE '%threshold%' THEN 3
                            WHEN name LIKE '%scale%' THEN 4
                            ELSE 5
                        END, name;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Identify vacuum blockers - long running transactions",
                "tool": "run_query",
                "action": "Find long-running transactions that prevent vacuum from reclaiming space",
                "query": """
                    SELECT 
                        pid,
                        datname AS database_name,
                        usename AS username,
                        application_name,
                        state,
                        EXTRACT(EPOCH FROM (now() - xact_start))::integer AS transaction_duration_seconds,
                        EXTRACT(EPOCH FROM (now() - query_start))::integer AS query_duration_seconds,
                        xact_start AS transaction_start_time,
                        wait_event_type,
                        wait_event,
                        LEFT(query, 100) AS query_preview
                    FROM pg_stat_activity
                    WHERE state != 'idle'
                    AND xact_start IS NOT NULL
                    AND backend_type = 'client backend'
                    AND pid != pg_backend_pid()
                    ORDER BY transaction_duration_seconds DESC
                    LIMIT 15;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check replication slots blocking vacuum",
                "tool": "run_query",
                "action": "Identify inactive or lagging replication slots that may prevent vacuum from reclaiming space",
                "query": """
                    SELECT 
                        slot_name,
                        slot_type,
                        database,
                        active,
                        restart_lsn,
                        confirmed_flush_lsn,
                        CASE
                            WHEN NOT active THEN 'INACTIVE - Slot not in use, may block vacuum'
                            WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'LOGICAL_SLOT_NOT_CONSUMING - May block vacuum'
                            WHEN slot_type = 'physical' AND restart_lsn IS NULL THEN 'PHYSICAL_SLOT_ISSUE - Check replication status'
                            ELSE 'ACTIVE - Slot functioning normally'
                        END as status,
                        CASE
                            WHEN NOT active THEN 'CRITICAL - Inactive slot may prevent vacuum from reclaiming space'
                            WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'WARNING - Logical slot not consuming changes'
                            ELSE 'OK - Slot is healthy'
                        END as vacuum_impact,
                        CASE
                            WHEN NOT active THEN 'DROP_UNUSED_SLOT - Confirm slot is not needed before dropping'
                            WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'CHECK_LOGICAL_REPLICATION - Verify consumer is running'
                            ELSE 'MONITOR_SLOT - Continue monitoring'
                        END as recommended_action
                    FROM pg_replication_slots
                    ORDER BY active, slot_name;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check table-specific autovacuum settings",
                "tool": "run_query", 
                "action": "Identify tables with custom autovacuum settings that might affect vacuum behavior",
                "query": """
                    SELECT 
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation,
                        most_common_vals,
                        most_common_freqs,
                        histogram_bounds
                    FROM pg_stats 
                    WHERE schemaname NOT IN ('information_schema', 'pg_catalog', 'pg_toast')
                    AND tablename IN (
                        SELECT relname 
                        FROM pg_stat_user_tables 
                        WHERE n_dead_tup > 10000 
                        OR n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.2
                    )
                    ORDER BY schemaname, tablename, attname;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "EXECUTE: VACUUM VERBOSE after blocker removal",
                "tool": "run_query",
                "action": "Execute VACUUM VERBOSE on the most bloated table and capture the actual output",
                "query": "VACUUM (VERBOSE, ANALYZE) sales_data;",
                "note": "This should be replaced with the actual table name from bloat analysis",
                "output_capture": "The PostgreSQL MCP server should return the actual VACUUM VERBOSE output including INFO messages about pages removed, tuples cleaned, XID boundaries, etc.",
                "DatabaseInstance": DatabaseInstance,
                "analysis_focus": [
                    "Pages removed vs remaining",
                    "Dead tuples cleaned up",
                    "XID horizon advancement", 
                    "Buffer usage statistics",
                    "Any remaining blockers or warnings"
                ]
            },
            {
                "step": "POST-VACUUM: Analyze vacuum effectiveness",
                "tool": "run_query",
                "action": "Compare before/after statistics to measure vacuum effectiveness",
                "query": """
                    -- POST-VACUUM EFFECTIVENESS ANALYSIS
                    WITH vacuum_effectiveness AS (
                        SELECT 
                            schemaname,
                            relname,
                            n_live_tup,
                            n_dead_tup,
                            round((n_dead_tup::numeric/nullif(n_live_tup+n_dead_tup,0))* 100,2) AS current_dead_tuple_percent,
                            last_vacuum,
                            last_autovacuum,
                            vacuum_count,
                            autovacuum_count,
                            pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as current_table_size,
                            EXTRACT(EPOCH FROM (now() - COALESCE(last_vacuum, last_autovacuum)))::integer as seconds_since_last_vacuum
                        FROM pg_stat_user_tables 
                        WHERE n_live_tup > 1000
                    )
                    SELECT 
                        schemaname,
                        relname,
                        n_live_tup,
                        n_dead_tup,
                        current_dead_tuple_percent,
                        current_table_size,
                        seconds_since_last_vacuum,
                        CASE 
                            WHEN current_dead_tuple_percent = 0 THEN 'EXCELLENT - All dead tuples removed'
                            WHEN current_dead_tuple_percent < 2 THEN 'VERY GOOD - <2% dead tuples remaining'
                            WHEN current_dead_tuple_percent < 5 THEN 'GOOD - <5% dead tuples remaining'
                            WHEN current_dead_tuple_percent < 10 THEN 'ACCEPTABLE - <10% dead tuples remaining'
                            ELSE 'NEEDS ATTENTION - High dead tuple percentage remains'
                        END as vacuum_effectiveness,
                        CASE 
                            WHEN seconds_since_last_vacuum < 60 THEN 'JUST COMPLETED - Vacuum ran within last minute'
                            WHEN seconds_since_last_vacuum < 300 THEN 'RECENT - Vacuum completed within 5 minutes'
                            ELSE 'OLDER - Vacuum completed more than 5 minutes ago'
                        END as vacuum_recency,
                        CASE 
                            WHEN current_dead_tuple_percent > 10 THEN 'Consider running VACUUM again or check for remaining blockers'
                            WHEN current_dead_tuple_percent > 5 THEN 'Monitor table - may need more frequent vacuuming'
                            ELSE 'Table is in good condition'
                        END as recommendation
                    FROM vacuum_effectiveness
                    ORDER BY current_dead_tuple_percent DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            }
        ]

    @staticmethod
    def get_query_performance_diagnostic(DatabaseInstance: Optional[str] = None, table_name: Optional[str] = None) -> List[Dict[str, str]]:
        """Returns comprehensive diagnostic steps for query performance analysis including vacuum blockers and lock analysis"""
        table_filter = f"AND relname = '{table_name}'" if table_name else ""
        
        return [
            {
                "step": "Check current blocking queries and locks affecting performance",
                "tool": "run_query",
                "action": "Identify current locks and blocking queries that may cause slow performance",
                "query": """
                    SELECT 
                        blocked_locks.pid AS blocked_pid,
                        blocked_activity.usename AS blocked_user,
                        blocking_locks.pid AS blocking_pid,
                        blocking_activity.usename AS blocking_user,
                        blocked_activity.query AS blocked_statement,
                        blocking_activity.query AS blocking_statement,
                        blocked_activity.application_name AS blocked_application,
                        blocking_activity.application_name AS blocking_application,
                        EXTRACT(EPOCH FROM (now() - blocked_activity.query_start))::integer AS blocked_duration_seconds,
                        EXTRACT(EPOCH FROM (now() - blocking_activity.query_start))::integer AS blocking_duration_seconds,
                        CASE 
                            WHEN EXTRACT(EPOCH FROM (now() - blocking_activity.query_start)) > 300 THEN 'CRITICAL - Long blocking query (>5min)'
                            WHEN EXTRACT(EPOCH FROM (now() - blocking_activity.query_start)) > 60 THEN 'WARNING - Blocking query (>1min)'
                            ELSE 'ACTIVE'
                        END as blocking_severity
                    FROM pg_catalog.pg_locks blocked_locks
                    JOIN pg_catalog.pg_stat_activity blocked_activity ON blocked_activity.pid = blocked_locks.pid
                    JOIN pg_catalog.pg_locks blocking_locks 
                        ON blocking_locks.locktype = blocked_locks.locktype
                        AND blocking_locks.database IS NOT DISTINCT FROM blocked_locks.database
                        AND blocking_locks.relation IS NOT DISTINCT FROM blocked_locks.relation
                        AND blocking_locks.page IS NOT DISTINCT FROM blocked_locks.page
                        AND blocking_locks.tuple IS NOT DISTINCT FROM blocked_locks.tuple
                        AND blocking_locks.virtualxid IS NOT DISTINCT FROM blocked_locks.virtualxid
                        AND blocking_locks.transactionid IS NOT DISTINCT FROM blocked_locks.transactionid
                        AND blocking_locks.classid IS NOT DISTINCT FROM blocked_locks.classid
                        AND blocking_locks.objid IS NOT DISTINCT FROM blocked_locks.objid
                        AND blocking_locks.objsubid IS NOT DISTINCT FROM blocked_locks.objsubid
                        AND blocking_locks.pid != blocked_locks.pid
                    JOIN pg_catalog.pg_stat_activity blocking_activity ON blocking_activity.pid = blocking_locks.pid
                    WHERE NOT blocked_locks.granted
                    ORDER BY blocking_duration_seconds DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "CRITICAL: Identify vacuum blockers causing performance degradation",
                "tool": "run_query", 
                "action": "Find ALL transactions blocking vacuum including 'idle in transaction' sessions",
                "query": """
                    WITH comprehensive_vacuum_blockers AS (
                        -- ALL transactions that can block vacuum (including idle in transaction)
                        SELECT 
                            CASE 
                                WHEN state = 'idle in transaction' THEN 'IDLE IN TRANSACTION - VACUUM BLOCKER'
                                WHEN state = 'idle in transaction (aborted)' THEN 'IDLE IN TRANSACTION (ABORTED) - VACUUM BLOCKER'
                                WHEN state = 'active' AND EXTRACT(EPOCH FROM (now() - xact_start)) > 300 THEN 'Long Running Transaction'
                                WHEN state != 'idle' AND xact_start IS NOT NULL THEN 'Active Transaction'
                                ELSE 'Other'
                            END as blocker_type,
                            pid,
                            datname,
                            usename,
                            application_name,
                            client_addr,
                            state,
                            EXTRACT(EPOCH FROM (now() - xact_start))::integer AS xact_duration_seconds,
                            EXTRACT(EPOCH FROM (now() - query_start))::integer AS query_duration_seconds,
                            EXTRACT(EPOCH FROM (now() - state_change))::integer AS state_duration_seconds,
                            xact_start,
                            query_start,
                            state_change,
                            LEFT(query, 150) AS query_preview,
                            CASE
                                WHEN state = 'idle in transaction' AND EXTRACT(EPOCH FROM (now() - state_change)) > 300 THEN 'CRITICAL - IDLE IN TRANSACTION >5min (BLOCKING VACUUM)'
                                WHEN state = 'idle in transaction (aborted)' THEN 'CRITICAL - ABORTED TRANSACTION (BLOCKING VACUUM)'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'CRITICAL - Long transaction >1hr (BLOCKING VACUUM)'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 1800 THEN 'WARNING - Long transaction >30min (MAY BLOCK VACUUM)'
                                ELSE 'MONITOR'
                            END as vacuum_blocking_severity,
                            CASE 
                                WHEN state = 'idle in transaction' THEN 'TERMINATE_IMMEDIATELY'
                                WHEN state = 'idle in transaction (aborted)' THEN 'TERMINATE_IMMEDIATELY'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'CONSIDER_TERMINATING'
                                ELSE 'Monitor - No immediate action needed'
                            END as recommended_action
                        FROM pg_stat_activity
                        WHERE backend_type = 'client backend'
                        AND pid != pg_backend_pid()
                        AND (
                            -- Include idle in transaction (major vacuum blocker)
                            state = 'idle in transaction'
                            OR state = 'idle in transaction (aborted)'
                            -- Include long-running active transactions
                            OR (state != 'idle' AND xact_start IS NOT NULL AND EXTRACT(EPOCH FROM (now() - xact_start)) > 300)
                        )
                        
                        UNION ALL
                        
                        -- Prepared transactions (also block vacuum)
                        SELECT 
                            'PREPARED TRANSACTION - VACUUM BLOCKER' as blocker_type,
                            NULL as pid,
                            database as datname,
                            owner as usename,
                            'prepared_xact' as application_name,
                            NULL as client_addr,
                            'prepared' as state,
                            EXTRACT(EPOCH FROM (now() - prepared))::integer AS xact_duration_seconds,
                            NULL as query_duration_seconds,
                            EXTRACT(EPOCH FROM (now() - prepared))::integer AS state_duration_seconds,
                            prepared as xact_start,
                            NULL as query_start,
                            prepared as state_change,
                            'PREPARED TRANSACTION: ' || gid as query_preview,
                            CASE
                                WHEN EXTRACT(EPOCH FROM (now() - prepared)) > 3600 THEN 'CRITICAL - Prepared transaction >1hr (BLOCKING VACUUM)'
                                WHEN EXTRACT(EPOCH FROM (now() - prepared)) > 1800 THEN 'WARNING - Prepared transaction >30min (MAY BLOCK VACUUM)'
                                ELSE 'MONITOR'
                            END as vacuum_blocking_severity,
                            'COMMIT_OR_ROLLBACK_PREPARED - Use: COMMIT PREPARED ''' || gid || '''; or ROLLBACK PREPARED ''' || gid || ''';' as recommended_action
                        FROM pg_prepared_xacts
                    )
                    SELECT 
                        blocker_type,
                        pid,
                        datname,
                        usename,
                        application_name,
                        client_addr,
                        state,
                        xact_duration_seconds,
                        query_duration_seconds,
                        state_duration_seconds,
                        vacuum_blocking_severity,
                        recommended_action,
                        query_preview,
                        CASE 
                            WHEN vacuum_blocking_severity LIKE 'CRITICAL%' THEN 'YES - This is actively blocking vacuum and causing table bloat'
                            WHEN vacuum_blocking_severity LIKE 'WARNING%' THEN 'POSSIBLY - This may be contributing to vacuum delays'
                            ELSE 'NO - Not currently blocking vacuum'
                        END as is_blocking_vacuum
                    FROM comprehensive_vacuum_blockers
                    ORDER BY 
                        CASE 
                            WHEN vacuum_blocking_severity LIKE 'CRITICAL%' THEN 1
                            WHEN vacuum_blocking_severity LIKE 'WARNING%' THEN 2
                            ELSE 3
                        END,
                        xact_duration_seconds DESC NULLS LAST;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check replication slots blocking vacuum and causing bloat",
                "tool": "run_query",
                "action": "Identify replication slots that prevent vacuum from reclaiming space, causing performance issues",
                "query": """
                    SELECT 
                        slot_name,
                        slot_type,
                        database,
                        active,
                        restart_lsn,
                        confirmed_flush_lsn,
                        CASE
                            WHEN NOT active THEN 'INACTIVE - Slot not in use, may block vacuum'
                            WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'LOGICAL_SLOT_NOT_CONSUMING - May block vacuum'
                            WHEN slot_type = 'physical' AND restart_lsn IS NULL THEN 'PHYSICAL_SLOT_ISSUE - Check replication status'
                            ELSE 'ACTIVE - Slot functioning normally'
                        END as status,
                        CASE
                            WHEN NOT active THEN 'CRITICAL - Inactive slot may prevent vacuum from reclaiming space'
                            WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'WARNING - Logical slot not consuming changes'
                            ELSE 'OK - Slot is healthy'
                        END as vacuum_impact,
                        CASE
                            WHEN NOT active THEN 'DROP_UNUSED_SLOT - Confirm slot is not needed before dropping'
                            WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'CHECK_LOGICAL_REPLICATION - Verify consumer is running'
                            ELSE 'MONITOR_SLOT - Continue monitoring'
                        END as recommended_action
                    FROM pg_replication_slots
                    ORDER BY active, slot_name;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Analyze table bloat and vacuum status affecting query performance",
                "tool": "run_query",
                "action": f"Check table statistics, bloat, and vacuum status for performance impact{' on ' + table_name if table_name else ''}",
                "query": f"""
                    SELECT 
                        schemaname,
                        relname as table_name,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        n_tup_ins,
                        n_tup_upd,
                        n_tup_del,
                        n_live_tup,
                        n_dead_tup,
                        round((n_dead_tup::numeric/nullif(n_live_tup+n_dead_tup,0))* 100,2) AS dead_tuple_percent,
                        last_vacuum,
                        last_autovacuum,
                        last_analyze,
                        last_autoanalyze,
                        vacuum_count,
                        autovacuum_count,
                        analyze_count,
                        autoanalyze_count,
                        CASE 
                            WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN 'CRITICAL - NEVER ANALYZED (No query planner stats)'
                            WHEN EXTRACT(EPOCH FROM (now() - COALESCE(last_autoanalyze, last_analyze)))/3600 > 24 THEN 'WARNING - STATS OUTDATED (>24h, poor query plans)'
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.3 THEN 'CRITICAL - HIGH BLOAT (>30%, very slow queries)'
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.2 THEN 'WARNING - MODERATE BLOAT (>20%, slow queries)'
                            WHEN seq_scan > idx_scan * 10 AND n_live_tup > 1000 THEN 'WARNING - TOO MANY SEQ SCANS (index needed)'
                            ELSE 'OK'
                        END as performance_issue,
                        CASE 
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.2 THEN 'VACUUM NEEDED - Bloat causing slow queries'
                            WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN 'ANALYZE NEEDED - No statistics for query planner'
                            WHEN EXTRACT(EPOCH FROM (now() - COALESCE(last_autoanalyze, last_analyze)))/3600 > 24 THEN 'ANALYZE NEEDED - Outdated statistics'
                            ELSE 'Maintenance up to date'
                        END as recommended_action
                    FROM pg_stat_user_tables 
                    WHERE n_live_tup > 0 {table_filter}
                    ORDER BY 
                        CASE 
                            WHEN last_analyze IS NULL AND last_autoanalyze IS NULL THEN 1
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.3 THEN 2
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) > 0.2 THEN 3
                            WHEN seq_scan > idx_scan * 10 AND n_live_tup > 1000 THEN 4
                            ELSE 5
                        END,
                        n_live_tup DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check index usage and effectiveness",
                "tool": "run_query",
                "action": f"Analyze index usage patterns and identify missing or unused indexes{' for ' + table_name if table_name else ''}",
                "query": f"""
                    SELECT 
                        pui.schemaname,
                        pui.relname as tablename,
                        pui.indexrelname as indexname,
                        pui.idx_scan as index_scans,
                        pui.idx_tup_read as tuples_read,
                        pui.idx_tup_fetch as tuples_fetched,
                        CASE 
                            WHEN pui.idx_scan = 0 THEN 'UNUSED INDEX - Consider dropping'
                            WHEN pui.idx_scan < 10 AND pg_relation_size(pui.indexrelid) > 1024*1024 THEN 'RARELY USED LARGE INDEX'
                            WHEN pui.idx_tup_read > pui.idx_tup_fetch * 100 THEN 'INEFFICIENT INDEX - High read/fetch ratio'
                            ELSE 'OK'
                        END as index_status,
                        pg_size_pretty(pg_relation_size(pui.indexrelid)) as index_size
                    FROM pg_stat_user_indexes pui
                    JOIN pg_stat_user_tables put ON pui.relid = put.relid
                    WHERE put.n_live_tup > 0
                    ORDER BY 
                        CASE 
                            WHEN pui.idx_scan = 0 THEN 1
                            WHEN pui.idx_scan < 10 AND pg_relation_size(pui.indexrelid) > 1024*1024 THEN 2
                            ELSE 3
                        END,
                        pg_relation_size(pui.indexrelid) DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check for missing indexes on frequently queried columns",
                "tool": "run_query",
                "action": "Identify tables with high sequential scan ratios that might benefit from indexes",
                "query": f"""
                    WITH table_scans AS (
                        SELECT 
                            schemaname,
                            relname,
                            seq_scan,
                            seq_tup_read,
                            idx_scan,
                            idx_tup_fetch,
                            n_live_tup,
                            CASE 
                                WHEN seq_scan + idx_scan > 0 
                                THEN round((seq_scan::numeric / (seq_scan + idx_scan)) * 100, 2)
                                ELSE 0 
                            END as seq_scan_percent
                        FROM pg_stat_user_tables
                        WHERE n_live_tup > 1000 {table_filter}
                    )
                    SELECT 
                        schemaname,
                        relname as table_name,
                        seq_scan,
                        idx_scan,
                        seq_scan_percent,
                        n_live_tup,
                        CASE 
                            WHEN seq_scan_percent > 80 AND n_live_tup > 10000 THEN 'CRITICAL - Mostly sequential scans on large table'
                            WHEN seq_scan_percent > 50 AND n_live_tup > 1000 THEN 'WARNING - High sequential scan ratio'
                            WHEN seq_scan > 1000 AND idx_scan < 100 THEN 'WARNING - Many seq scans, few index scans'
                            ELSE 'OK'
                        END as recommendation
                    FROM table_scans
                    WHERE seq_scan_percent > 30 OR (seq_scan > 100 AND n_live_tup > 1000)
                    ORDER BY seq_scan_percent DESC, n_live_tup DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check current query performance from pg_stat_statements",
                "tool": "run_query",
                "action": "Analyze slow queries and execution patterns from pg_stat_statements",
                "query": """
                    SELECT 
                        LEFT(query, 100) as query_preview,
                        calls,
                        round(total_exec_time::numeric, 2) as total_time,
                        round((total_exec_time/calls)::numeric, 2) as avg_time_ms,
                        round(((100.0 * total_exec_time / sum(total_exec_time) OVER()))::numeric, 2) as percent_total_time,
                        rows,
                        round(rows::numeric/calls, 2) as avg_rows,
                        shared_blks_hit,
                        shared_blks_read,
                        CASE 
                            WHEN shared_blks_hit + shared_blks_read > 0 
                            THEN round((shared_blks_hit::numeric / (shared_blks_hit + shared_blks_read)) * 100, 2)
                            ELSE 0 
                        END as cache_hit_percent,
                        CASE 
                            WHEN total_exec_time/calls > 1000 THEN 'SLOW - Avg >1s per call'
                            WHEN shared_blks_read > shared_blks_hit THEN 'I/O INTENSIVE - Low cache hit ratio'
                            WHEN calls > 10000 AND total_exec_time/calls > 100 THEN 'HIGH FREQUENCY SLOW QUERY'
                            ELSE 'OK'
                        END as performance_issue
                    FROM pg_stat_statements 
                    WHERE calls > 10
                    ORDER BY total_exec_time DESC 
                    LIMIT 20;
                """,
                "DatabaseInstance": DatabaseInstance
            }
        ]

    @staticmethod
    def get_connection_analysis_diagnostic(DatabaseInstance: Optional[str] = None) -> List[Dict[str, str]]:
        """Returns diagnostic steps for connection and session analysis"""
        return [
            {
                "step": "Check active connections by state and application",
                "tool": "run_query",
                "action": "Analyze current database connections grouped by state and application",
                "query": """
                    SELECT 
                        state,
                        application_name,
                        count(*) as connection_count,
                        EXTRACT(EPOCH FROM max(now() - query_start))::integer as max_query_duration_seconds,
                        EXTRACT(EPOCH FROM max(now() - state_change))::integer as max_state_duration_seconds
                    FROM pg_stat_activity 
                    WHERE backend_type = 'client backend'
                    GROUP BY state, application_name 
                    ORDER BY connection_count DESC;
                """,
                "DatabaseInstance": DatabaseInstance
            },
            {
                "step": "Check long-running transactions",
                "tool": "run_query", 
                "action": "Identify long-running transactions that may be blocking autovacuum",
                "query": """
                    SELECT
                        pid,
                        datname AS database_name,
                        usename AS username,
                        application_name,
                        state,
                        EXTRACT(
                            EPOCH
                            FROM
                            (now() - xact_start)
                        )::INTEGER AS transaction_duration_seconds,
                        EXTRACT(
                            EPOCH
                            FROM
                            (now() - query_start)
                        )::INTEGER AS query_duration_seconds,
                        xact_start AS transaction_start_time,
                        wait_event_type,
                        wait_event,
                        LEFT(query, 100) AS query_preview
                        FROM pg_stat_activity
                        WHERE state != 'idle'
                        AND xact_start IS NOT NULL
                        AND backend_type = 'client backend'
                        AND pid != pg_backend_pid()
                        ORDER BY transaction_duration_seconds DESC
                        LIMIT 15;
                """,
                "DatabaseInstance": DatabaseInstance
            }
        ]

# Register runbook tools
@mcp.tool()
def slow_query_diagnostic(DatabaseInstance: str = "dev-cluster") -> dict:
    """Get diagnostic steps for slow query analysis with mandatory parallel enhancement"""
    
    # Core workflow steps  
    workflow_steps = PostgreSQLRunbooks.get_slow_query_diagnostic(DatabaseInstance)
    
    # Mandatory parallel enhancement steps
    parallel_enhancement = {
        "performance_insights_steps": [
            {
                "server": "performance_insights",
                "action": "get_top_sql",
                "purpose": "Get top slow SQL queries from Performance Insights",
                "parameters": {"metric_type": "db.SQL.Innodb.rows_read.avg", "group_by": "db.sql_tokenized.statement"}
            },
            {
                "server": "performance_insights",
                "action": "get_resource_metrics",
                "purpose": "Get CPU, I/O, and wait event metrics",
                "parameters": {"metric_type": "os.cpuUtilization.total.avg"}
            }
        ],
        "cloudwatch_steps": [
            {
                "server": "cloudwatch",
                "action": "get_log_events",
                "purpose": "Search for slow query logs",
                "parameters": {
                    "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
                    "filter_pattern": "duration.*ms|slow query",
                    "hours_back": 24,
                    "max_items": 100
                }
            },
            {
                "server": "cloudwatch",
                "action": "get_metric_statistics",
                "purpose": "Get CPU and I/O metrics during slow queries",
                "parameters": {
                    "namespace": "AWS/RDS",
                    "metric_name": "CPUUtilization",
                    "hours_back": 24,
                    "period": 300
                }
            }
        ],
        "aws_api_steps": [
            {
                "server": "aws_api",
                "action": "describe_db_clusters",
                "purpose": "Get RDS performance configuration",
                "parameters": {"cluster_identifier": DatabaseInstance}
            }
        ]
    }
    
    return {
        "workflow_type": "slow_query_diagnostic",
        "execution_mode": "parallel_enhanced",
        "core_workflow_steps": workflow_steps,
        "mandatory_parallel_enhancement": parallel_enhancement,
        "execution_instructions": {
            "phase_1": "Execute core slow query analysis",
            "phase_2": "SIMULTANEOUSLY get Performance Insights + CloudWatch slow query data",
            "phase_3": "Correlate database slow queries with infrastructure performance"
        },
        "total_steps": len(workflow_steps) + sum(len(steps) for steps in parallel_enhancement.values()),
        "comprehensive_coverage": [
            "Database slow query analysis",
            "Performance Insights top SQL correlation",
            "CloudWatch slow query log analysis",
            "Infrastructure performance impact"
        ]
    }

@mcp.tool()
def lock_analysis_diagnostic(DatabaseInstance: str = "dev-cluster") -> dict:
    """Get diagnostic steps for lock contention analysis with mandatory parallel enhancement"""
    
    # Core workflow steps
    workflow_steps = PostgreSQLRunbooks.get_lock_analysis_diagnostic(DatabaseInstance)
    
    # Mandatory parallel enhancement steps
    parallel_enhancement = {
        "performance_insights_steps": [
            {
                "server": "performance_insights",
                "action": "get_top_sql",
                "purpose": "Get top SQL queries that might be causing locks",
                "parameters": {"metric_type": "db.SQL.Innodb.rows_read.avg", "group_by": "db.sql_tokenized.statement"}
            },
            {
                "server": "performance_insights",
                "action": "get_resource_metrics",
                "purpose": "Get CPU and lock wait metrics",
                "parameters": {"metric_type": "db.locks.deadlocks.avg"}
            }
        ],
        "cloudwatch_steps": [
            {
                "server": "cloudwatch",
                "action": "get_log_events",
                "purpose": "Search for deadlock and lock timeout logs",
                "parameters": {
                    "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
                    "filter_pattern": "deadlock|lock timeout|could not obtain lock",
                    "hours_back": 24,
                    "max_items": 100
                }
            },
            {
                "server": "cloudwatch",
                "action": "get_metric_statistics",
                "purpose": "Get database connection and lock metrics",
                "parameters": {
                    "namespace": "AWS/RDS",
                    "metric_name": "DatabaseConnections",
                    "hours_back": 4,
                    "period": 300
                }
            }
        ],
        "aws_api_steps": [
            {
                "server": "aws_api",
                "action": "describe_db_clusters",
                "purpose": "Get RDS configuration affecting lock behavior",
                "parameters": {"cluster_identifier": DatabaseInstance}
            }
        ]
    }
    
    return {
        "workflow_type": "lock_analysis_diagnostic",
        "execution_mode": "parallel_enhanced",
        "core_workflow_steps": workflow_steps,
        "mandatory_parallel_enhancement": parallel_enhancement,
        "execution_instructions": {
            "phase_1": "Execute core lock analysis queries",
            "phase_2": "SIMULTANEOUSLY get Performance Insights lock metrics + CloudWatch logs",
            "phase_3": "Correlate database locks with infrastructure and application patterns"
        },
        "total_steps": len(workflow_steps) + sum(len(steps) for steps in parallel_enhancement.values()),
        "comprehensive_coverage": [
            "Database lock contention analysis",
            "Performance Insights lock wait correlation",
            "CloudWatch deadlock log analysis",
            "Infrastructure configuration review"
        ]
    }

@mcp.tool()
def vacuum_analysis_diagnostic(DatabaseInstance: str = "dev-cluster") -> dict:
    """Get comprehensive diagnostic steps for vacuum and bloat analysis with mandatory parallel enhancement"""
    
    # Core workflow steps
    workflow_steps = PostgreSQLRunbooks.get_vacuum_analysis_diagnostic(DatabaseInstance)
    
    # Mandatory parallel enhancement steps
    parallel_enhancement = {
        "performance_insights_steps": [
            {
                "server": "performance_insights",
                "action": "get_top_sql",
                "purpose": "Get top SQL queries that might be blocking vacuum",
                "parameters": {"metric_type": "db.SQL.Innodb.rows_read.avg", "group_by": "db.sql_tokenized.statement"}
            },
            {
                "server": "performance_insights", 
                "action": "get_resource_metrics",
                "purpose": "Get CPU/memory metrics during vacuum operations",
                "parameters": {"metric_type": "os.cpuUtilization.total.avg"}
            }
        ],
        "cloudwatch_steps": [
            {
                "server": "cloudwatch",
                "action": "get_log_events",
                "purpose": "Search for vacuum-related log entries",
                "parameters": {
                    "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
                    "filter_pattern": "removable cutoff",
                    "hours_back": 24,
                    "max_items": 100
                }
            },
            {
                "server": "cloudwatch",
                "action": "get_log_events", 
                "purpose": "Search for autovacuum launcher activity",
                "parameters": {
                    "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
                    "filter_pattern": "autovacuum launcher",
                    "hours_back": 24,
                    "max_items": 50
                }
            },
            {
                "server": "cloudwatch",
                "action": "get_metric_statistics",
                "purpose": "Get database connection metrics during vacuum",
                "parameters": {
                    "namespace": "AWS/RDS",
                    "metric_name": "DatabaseConnections",
                    "hours_back": 24,
                    "period": 300
                }
            }
        ],
        "aws_api_steps": [
            {
                "server": "aws_api",
                "action": "describe_db_clusters",
                "purpose": "Get RDS cluster configuration affecting vacuum",
                "parameters": {"cluster_identifier": DatabaseInstance}
            },
            {
                "server": "aws_api", 
                "action": "describe_db_instances",
                "purpose": "Get instance-level configuration and status",
                "parameters": {"db_instance_identifier": f"{DatabaseInstance}-instance-1"}
            }
        ]
    }
    
    return {
        "workflow_type": "vacuum_analysis_diagnostic",
        "execution_mode": "parallel_enhanced",
        "core_workflow_steps": workflow_steps,
        "mandatory_parallel_enhancement": parallel_enhancement,
        "execution_instructions": {
            "phase_1": "Execute core workflow steps (can be parallel within PostgreSQL)",
            "phase_2": "SIMULTANEOUSLY execute all enhancement steps across MCP servers", 
            "phase_3": "Synthesize results from all sources for comprehensive analysis"
        },
        "total_steps": len(workflow_steps) + sum(len(steps) for steps in parallel_enhancement.values()),
        "estimated_time_savings": "80-90% faster with optimized parallel execution (target: <30 seconds)",
        "performance_optimizations": [
            "Execute vacuum blocker detection first (most critical)",
            "Use LIMIT clauses on large result sets", 
            "Prioritize actionable queries over comprehensive analysis",
            "Cache configuration data across requests"
        ],
        "comprehensive_coverage": [
            "Database-level vacuum analysis",
            "Performance Insights metrics correlation", 
            "CloudWatch log pattern analysis",
            "AWS infrastructure configuration review"
        ]
    }

@mcp.tool()
def query_performance_diagnostic(DatabaseInstance: str = "dev-cluster", table_name: str = None) -> dict:
    """Get diagnostic steps for query performance analysis with mandatory parallel enhancement"""
    
    # Core workflow steps
    workflow_steps = PostgreSQLRunbooks.get_query_performance_diagnostic(DatabaseInstance, table_name)
    
    # Mandatory parallel enhancement steps
    parallel_enhancement = {
        "performance_insights_steps": [
            {
                "server": "performance_insights",
                "action": "get_top_sql",
                "purpose": "Get top SQL queries by execution time and resource consumption",
                "parameters": {"metric_type": "db.SQL.Innodb.rows_read.avg", "group_by": "db.sql_tokenized.statement"}
            },
            {
                "server": "performance_insights",
                "action": "get_resource_metrics", 
                "purpose": "Get detailed CPU, memory, and I/O metrics",
                "parameters": {"metric_type": "os.cpuUtilization.total.avg"}
            }
        ],
        "cloudwatch_steps": [
            {
                "server": "cloudwatch",
                "action": "get_log_events",
                "purpose": "Search for slow query logs and performance issues",
                "parameters": {
                    "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
                    "filter_pattern": "duration.*ms",
                    "start_time": "24h"
                }
            },
            {
                "server": "cloudwatch",
                "action": "get_metric_statistics",
                "purpose": "Get database performance metrics",
                "parameters": {
                    "namespace": "AWS/RDS", 
                    "metric_name": "CPUUtilization",
                    "start_time": "24h"
                }
            }
        ],
        "aws_api_steps": [
            {
                "server": "aws_api",
                "action": "describe_db_clusters",
                "purpose": "Get RDS performance configuration",
                "parameters": {"cluster_identifier": DatabaseInstance}
            }
        ]
    }
    
    return {
        "workflow_type": "query_performance_diagnostic",
        "execution_mode": "parallel_enhanced", 
        "core_workflow_steps": workflow_steps,
        "mandatory_parallel_enhancement": parallel_enhancement,
        "table_focus": table_name,
        "execution_instructions": {
            "phase_1": "Execute core performance queries",
            "phase_2": "SIMULTANEOUSLY get Performance Insights + CloudWatch data",
            "phase_3": "Correlate database queries with infrastructure metrics"
        },
        "total_steps": len(workflow_steps) + sum(len(steps) for steps in parallel_enhancement.values()),
        "comprehensive_coverage": [
            "Database query performance analysis",
            "Performance Insights top SQL correlation",
            "CloudWatch slow query log analysis", 
            "Infrastructure performance metrics"
        ]
    }

@mcp.tool()
def connection_analysis_diagnostic(DatabaseInstance: str = "dev-cluster") -> dict:
    """Get diagnostic steps for connection and session analysis with mandatory parallel enhancement"""
    
    # Core workflow steps
    workflow_steps = PostgreSQLRunbooks.get_connection_analysis_diagnostic(DatabaseInstance)
    
    # Mandatory parallel enhancement steps
    parallel_enhancement = {
        "performance_insights_steps": [
            {
                "server": "performance_insights",
                "action": "get_resource_metrics",
                "purpose": "Get connection and session metrics from Performance Insights",
                "parameters": {"metric_type": "db.connections.avg"}
            }
        ],
        "cloudwatch_steps": [
            {
                "server": "cloudwatch",
                "action": "get_log_events",
                "purpose": "Search for connection-related log entries",
                "parameters": {
                    "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
                    "filter_pattern": "connection|authentication|too many connections",
                    "hours_back": 24,
                    "max_items": 100
                }
            },
            {
                "server": "cloudwatch",
                "action": "get_metric_statistics",
                "purpose": "Get connection count metrics over time",
                "parameters": {
                    "namespace": "AWS/RDS",
                    "metric_name": "DatabaseConnections",
                    "hours_back": 24,
                    "period": 300
                }
            }
        ],
        "aws_api_steps": [
            {
                "server": "aws_api",
                "action": "describe_db_clusters",
                "purpose": "Get RDS connection limits and configuration",
                "parameters": {"cluster_identifier": DatabaseInstance}
            },
            {
                "server": "aws_api",
                "action": "describe_db_instances",
                "purpose": "Get instance-level connection configuration",
                "parameters": {"db_instance_identifier": f"{DatabaseInstance}-instance-1"}
            }
        ]
    }
    
    return {
        "workflow_type": "connection_analysis_diagnostic",
        "execution_mode": "parallel_enhanced",
        "core_workflow_steps": workflow_steps,
        "mandatory_parallel_enhancement": parallel_enhancement,
        "execution_instructions": {
            "phase_1": "Execute core connection analysis queries",
            "phase_2": "SIMULTANEOUSLY get Performance Insights + CloudWatch connection data",
            "phase_3": "Correlate database sessions with infrastructure limits and patterns"
        },
        "total_steps": len(workflow_steps) + sum(len(steps) for steps in parallel_enhancement.values()),
        "comprehensive_coverage": [
            "Database connection and session analysis",
            "Performance Insights connection metrics",
            "CloudWatch connection log analysis",
            "RDS connection limit configuration"
        ]
    }

@mcp.tool()
def get_vacuum_log_analysis_queries() -> List[Dict[str, str]]:
    """
    Get CloudWatch log analysis queries for vacuum operations
    
    Returns:
        List of log search patterns for vacuum analysis
    """
    return [
        {
            "tool": "get_log_events",
            "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql", 
            "search_pattern": "removable cutoff:",
            "description": "Find vacuum removable cutoff values in logs",
            "time_range_hours": 24
        },
        {
            "tool": "get_log_events", 
            "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
            "search_pattern": "automatic vacuum.*sales_data",
            "description": "Find autovacuum runs for sales_data table",
            "time_range_hours": 72
        },
        {
            "tool": "get_log_events",
            "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql", 
            "search_pattern": "autovacuum launcher",
            "description": "Check autovacuum launcher activity",
            "time_range_hours": 24
        },
        {
            "tool": "get_log_events",
            "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
            "search_pattern": "FATAL|ERROR.*vacuum",
            "description": "Find vacuum-related errors",
            "time_range_hours": 168
        }
    ]

@mcp.tool()
def get_performance_log_analysis_queries() -> List[Dict[str, str]]:
    """
    Get CloudWatch log analysis queries for performance issues
    
    Returns:
        List of log search patterns for performance analysis
    """
    return [
        {
            "tool": "get_log_events",
            "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
            "search_pattern": "duration.*ms.*SELECT.*sales_data",
            "description": "Find slow queries on sales_data table",
            "time_range_hours": 24
        },
        {
            "tool": "get_log_events",
            "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql", 
            "search_pattern": "checkpoint",
            "description": "Check checkpoint frequency and duration",
            "time_range_hours": 24
        },
        {
            "tool": "get_log_events",
            "log_group": f"/aws/rds/cluster/{DatabaseInstance}/postgresql",
            "search_pattern": "temporary file.*exceeds",
            "description": "Find queries creating large temporary files",
            "time_range_hours": 48
        }
    ]

@mcp.tool()
def propose_new_workflow(scenario_name: str, user_queries: list, diagnostic_steps: list) -> dict:
    """
    Propose a new workflow based on repeated unknown scenarios
    
    Args:
        scenario_name: Name for the new workflow scenario
        user_queries: List of similar user queries that triggered this
        diagnostic_steps: List of diagnostic steps that were effective
        
    Returns:
        Proposed workflow definition
    """
    
    # Generate workflow function name
    workflow_name = f"{scenario_name.lower().replace(' ', '_')}_diagnostic"
    
    # Categorize diagnostic steps
    query_steps = [step for step in diagnostic_steps if step.get('tool') == 'run_query']
    log_steps = [step for step in diagnostic_steps if step.get('tool') == 'get_log_events']
    
    return {
        "proposed_workflow_name": workflow_name,
        "scenario_description": f"Diagnostic workflow for {scenario_name} scenarios",
        "trigger_patterns": [
            # Extract keywords from user queries
            word for query in user_queries 
            for word in query.lower().split() 
            if len(word) > 3 and word not in ['the', 'and', 'for', 'with', 'this', 'that']
        ][:10],  # Top 10 keywords
        "diagnostic_steps": query_steps,
        "log_analysis_steps": log_steps,
        "estimated_complexity": len(diagnostic_steps),
        "implementation_priority": "high" if len(user_queries) > 2 else "medium",
        "workflow_template": f"""
@mcp.tool()
def {workflow_name}(DatabaseInstance: str = "dev-cluster") -> List[Dict[str, str]]:
    '''Get diagnostic steps for {scenario_name} analysis'''
    return {query_steps}
        """,
        "integration_notes": [
            f"Add '{scenario_name.lower()}' keyword to workflow_map",
            f"Set appropriate priority level in workflow_priority",
            f"Test with sample queries: {user_queries[:3]}"
        ]
    }

@mcp.tool()
def execute_vacuum_verbose_with_output_capture(table_name: str) -> dict:
    """
    Execute VACUUM VERBOSE and provide instructions for capturing the actual output
    
    Args:
        table_name: Name of the table to vacuum
        
    Returns:
        Instructions for executing VACUUM VERBOSE and capturing real output
    """
    
    return {
        "vacuum_command": f"VACUUM (VERBOSE, ANALYZE) {table_name};",
        "execution_priority": "HIGH - Execute immediately after removing vacuum blockers",
        "output_capture_instructions": {
            "capture_method": "PostgreSQL MCP server should return the complete VACUUM VERBOSE output",
            "expected_output_format": [
                "INFO: vacuuming \"public.{table_name}\"",
                "INFO: scanned X pages, removed Y tuples in Z pages", 
                "INFO: pages: X removed, Y remain, Z skipped due to pins",
                "INFO: tuples: X removed, Y remain, Z are dead but not yet removable",
                "INFO: buffer usage: X hit, Y miss, Z dirtied",
                "INFO: avg read rate: X MB/s, avg write rate: Y MB/s", 
                "INFO: system usage: CPU: user: Xs, system: Ys, elapsed: Zs",
                "INFO: XID cutoff: old=X new=Y (advanced by Z)",
                "INFO: MultiXact cutoff: old=X new=Y (advanced by Z)"
            ],
            "key_metrics_to_extract": [
                "Pages removed vs remaining",
                "Dead tuples removed vs remaining", 
                "XID horizon advancement (old → new)",
                "MultiXact advancement",
                "Buffer hit/miss ratio",
                "I/O rates and CPU usage",
                "Total execution time"
            ]
        },
        "analysis_instructions": {
            "success_indicators": [
                "Significant reduction in dead tuples",
                "XID cutoff advanced (indicates vacuum horizon moved forward)",
                "Pages successfully removed from table",
                "No errors or warnings in output"
            ],
            "warning_signs": [
                "Many tuples marked as 'dead but not yet removable'",
                "Pages 'skipped due to pins' (concurrent activity)",
                "XID cutoff did not advance significantly",
                "High buffer miss ratio indicating I/O pressure"
            ],
            "performance_assessment": [
                "Execution time relative to table size",
                "I/O rates compared to system capabilities", 
                "CPU usage efficiency",
                "Buffer cache effectiveness"
            ]
        },
        "post_vacuum_verification": [
            "Check pg_stat_user_tables for updated statistics",
            "Verify dead tuple count reduction",
            "Confirm last_vacuum timestamp updated",
            "Monitor query performance improvement"
        ]
    }

@mcp.tool()
def execute_vacuum_after_blocker_removal(table_name: str, blocker_pids: list = None) -> dict:
    """
    Execute VACUUM VERBOSE after removing vacuum blockers and analyze the results
    
    Args:
        table_name: Name of the table to vacuum
        blocker_pids: List of PIDs that were terminated (optional)
        
    Returns:
        VACUUM VERBOSE execution plan with analysis instructions
    """
    
    return {
        "execution_type": "post_blocker_vacuum_analysis",
        "priority": "HIGH - Execute immediately after terminating blockers",
        "table_target": table_name,
        "terminated_blockers": blocker_pids or [],
        "vacuum_sequence": [
            {
                "step": 1,
                "action": "pre_vacuum_stats",
                "query": f"""
                    -- PRE-VACUUM STATISTICS
                    SELECT 
                        'PRE-VACUUM STATS' as analysis_phase,
                        schemaname,
                        relname,
                        n_live_tup,
                        n_dead_tup,
                        round((n_dead_tup::numeric/nullif(n_live_tup+n_dead_tup,0))* 100,2) AS dead_tuple_percent_before,
                        last_vacuum,
                        last_autovacuum,
                        vacuum_count,
                        autovacuum_count,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as table_size_before
                    FROM pg_stat_user_tables 
                    WHERE relname = '{table_name}';
                """,
                "purpose": "Capture baseline statistics before vacuum"
            },
            {
                "step": 2,
                "action": "execute_vacuum_verbose",
                "query": f"VACUUM (VERBOSE, ANALYZE) {table_name};",
                "purpose": "Execute vacuum with verbose output for detailed analysis",
                "expected_output_analysis": [
                    "Pages removed/remaining counts",
                    "Tuple counts (removed/remain)",
                    "XID boundaries and horizon advancement",
                    "Index cleanup statistics",
                    "Buffer usage and I/O statistics"
                ]
            },
            {
                "step": 3,
                "action": "post_vacuum_stats",
                "query": f"""
                    -- POST-VACUUM STATISTICS COMPARISON
                    SELECT 
                        'POST-VACUUM STATS' as analysis_phase,
                        schemaname,
                        relname,
                        n_live_tup,
                        n_dead_tup,
                        round((n_dead_tup::numeric/nullif(n_live_tup+n_dead_tup,0))* 100,2) AS dead_tuple_percent_after,
                        last_vacuum,
                        last_autovacuum,
                        vacuum_count,
                        autovacuum_count,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as table_size_after,
                        CASE 
                            WHEN n_dead_tup = 0 THEN 'EXCELLENT - All dead tuples removed'
                            WHEN n_dead_tup < 1000 THEN 'GOOD - Minimal dead tuples remaining'
                            WHEN n_dead_tup::float/nullif(n_live_tup+n_dead_tup,0) < 0.05 THEN 'ACCEPTABLE - <5% dead tuples'
                            ELSE 'NEEDS ATTENTION - Significant dead tuples remain'
                        END as vacuum_effectiveness
                    FROM pg_stat_user_tables 
                    WHERE relname = '{table_name}';
                """,
                "purpose": "Compare before/after statistics to measure vacuum effectiveness"
            },
            {
                "step": 4,
                "action": "analyze_vacuum_progress",
                "query": """
                    -- CHECK IF VACUUM IS STILL RUNNING
                    SELECT 
                        'VACUUM PROGRESS CHECK' as analysis_phase,
                        CASE 
                            WHEN COUNT(*) > 0 THEN 'VACUUM STILL RUNNING'
                            ELSE 'VACUUM COMPLETED'
                        END as vacuum_status,
                        COALESCE(
                            string_agg(
                                'PID: ' || p.pid::text || 
                                ', Phase: ' || p.phase || 
                                ', Progress: ' || round(100.0 * p.heap_blks_scanned / p.heap_blks_total, 1)::text || '%'
                                , '; '
                            ), 
                            'No active vacuum operations'
                        ) as current_vacuum_info
                    FROM pg_stat_progress_vacuum p 
                    JOIN pg_stat_activity a USING (pid)
                    WHERE p.relid::regclass::text LIKE '%{table_name}%';
                """,
                "purpose": "Check if vacuum is still in progress or completed"
            }
        ],
        "vacuum_output_analysis_instructions": {
            "key_metrics_to_extract": [
                "Pages: X removed, Y remain",
                "Tuples: X removed, Y remain", 
                "Buffer usage: X hit, Y miss, Z dirtied",
                "XID cutoff: old=X new=Y",
                "MultiXact cutoff: old=X new=Y",
                "System usage: CPU X.XXs/X.XXu sec elapsed X.XX sec"
            ],
            "success_indicators": [
                "Significant reduction in dead tuples",
                "XID horizon advancement", 
                "Pages successfully removed",
                "No errors or warnings in output"
            ],
            "warning_signs": [
                "Many tuples could not be removed",
                "XID horizon did not advance significantly",
                "Warnings about concurrent activity",
                "High buffer miss ratio"
            ]
        },
        "interpretation_guide": {
            "excellent_vacuum": "Dead tuples reduced to <1%, XID horizon advanced significantly",
            "good_vacuum": "Dead tuples reduced by >80%, some XID advancement",
            "partial_vacuum": "Some cleanup occurred but blockers may still exist",
            "failed_vacuum": "Minimal cleanup, likely still blocked or concurrent activity"
        }
    }

@mcp.tool()
def detect_all_vacuum_blockers_immediately() -> dict:
    """
    CRITICAL: Comprehensive detection of ALL vacuum blockers for performance issues
    Includes: idle transactions, prepared statements, replication slots, long transactions
    
    Returns:
        Complete vacuum blocker analysis with specific remediation commands
    """
    
    return {
        "priority": "CRITICAL - Execute ALL queries FIRST",
        "purpose": "Detect ALL types of vacuum blockers: idle transactions, prepared statements, replication slots",
        "execution_order": 1,
        "queries": {
            "idle_and_long_transactions": """
                -- IMMEDIATE VACUUM BLOCKER DETECTION: Idle & Long Transactions
                        SELECT 
                            'TRANSACTION BLOCKER' as blocker_category,
                            CASE 
                                WHEN state = 'idle in transaction' THEN 'IDLE IN TRANSACTION'
                                WHEN state = 'idle in transaction (aborted)' THEN 'IDLE IN TRANSACTION (ABORTED)'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'LONG RUNNING TRANSACTION'
                                ELSE 'ACTIVE TRANSACTION'
                            END as blocker_type,
                            pid,
                            datname,
                            usename,
                            application_name,
                            client_addr,
                            state,
                            EXTRACT(EPOCH FROM (now() - xact_start))::integer AS xact_duration_seconds,
                            EXTRACT(EPOCH FROM (now() - state_change))::integer AS state_duration_seconds,
                            CASE
                                WHEN state = 'idle in transaction' THEN 'CRITICAL - BLOCKING VACUUM'
                                WHEN state = 'idle in transaction (aborted)' THEN 'CRITICAL - BLOCKING VACUUM'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'CRITICAL - LONG TRANSACTION'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 1800 THEN 'WARNING - MODERATE TRANSACTION'
                                ELSE 'ACTIVE'
                            END as severity,
                            CASE 
                                WHEN state = 'idle in transaction' THEN 'TERMINATE_IMMEDIATELY'
                                WHEN state = 'idle in transaction (aborted)' THEN 'TERMINATE_IMMEDIATELY'
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 'CONSIDER_TERMINATING'
                                ELSE 'MONITOR'
                            END as recommended_action,
                            LEFT(query, 100) AS query_preview
                        FROM pg_stat_activity
                        WHERE backend_type = 'client backend'
                        AND pid != pg_backend_pid()
                        AND (
                            state = 'idle in transaction'
                            OR state = 'idle in transaction (aborted)'
                            OR (xact_start IS NOT NULL AND EXTRACT(EPOCH FROM (now() - xact_start)) > 300)
                        )
                        ORDER BY 
                            CASE 
                                WHEN state = 'idle in transaction' THEN 1
                                WHEN state = 'idle in transaction (aborted)' THEN 2
                                WHEN EXTRACT(EPOCH FROM (now() - xact_start)) > 3600 THEN 3
                                ELSE 4
                            END,
                            xact_duration_seconds DESC;
            """,
            "prepared_transactions": """
                -- PREPARED TRANSACTION BLOCKERS
                    SELECT 
                        'PREPARED TRANSACTION BLOCKER' as blocker_category,
                        'PREPARED TRANSACTION' as blocker_type,
                        NULL as pid,
                        database as datname,
                        owner as usename,
                        'prepared_xact' as application_name,
                        NULL as client_addr,
                        'prepared' as state,
                        EXTRACT(EPOCH FROM (now() - prepared))::integer AS xact_duration_seconds,
                        EXTRACT(EPOCH FROM (now() - prepared))::integer AS state_duration_seconds,
                        CASE
                            WHEN EXTRACT(EPOCH FROM (now() - prepared)) > 3600 THEN 'CRITICAL - PREPARED >1hr'
                            WHEN EXTRACT(EPOCH FROM (now() - prepared)) > 1800 THEN 'WARNING - PREPARED >30min'
                            ELSE 'ACTIVE'
                        END as severity,
                        CASE 
                            WHEN EXTRACT(EPOCH FROM (now() - prepared)) > 3600 THEN 'COMMIT_OR_ROLLBACK_NEEDED'
                            ELSE 'MONITOR_PREPARED'
                        END as recommended_action,
                        gid as transaction_id,
                        'PREPARED TRANSACTION: ' || gid as query_preview
                    FROM pg_prepared_xacts
                    ORDER BY prepared;
            """,
            "replication_slot_blockers": """
                -- REPLICATION SLOT BLOCKERS
                SELECT 
                    'REPLICATION SLOT BLOCKER' as blocker_category,
                    CASE 
                        WHEN NOT active THEN 'INACTIVE REPLICATION SLOT'
                        WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'LOGICAL_SLOT_NOT_CONSUMING'
                        ELSE 'ACTIVE REPLICATION SLOT'
                    END as blocker_type,
                    NULL as pid,
                    database as datname,
                    NULL as usename,
                    slot_name as application_name,
                    NULL as client_addr,
                    CASE WHEN active THEN 'active' ELSE 'inactive' END as state,
                    NULL as xact_duration_seconds,
                    NULL as state_duration_seconds,
                    CASE
                        WHEN NOT active THEN 'CRITICAL - INACTIVE SLOT BLOCKING VACUUM'
                        WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'WARNING - LOGICAL SLOT NOT CONSUMING'
                        ELSE 'OK'
                    END as severity,
                    CASE 
                        WHEN NOT active THEN 'DROP_UNUSED_SLOT'
                        WHEN slot_type = 'logical' AND confirmed_flush_lsn IS NULL THEN 'CHECK_LOGICAL_REPLICATION'
                        ELSE 'MONITOR_SLOT'
                    END as recommended_action,
                    restart_lsn,
                    confirmed_flush_lsn,
                    'Slot: ' || slot_name || ', Type: ' || slot_type as query_preview
                FROM pg_replication_slots
                ORDER BY active, slot_name;
            """
        },
        "interpretation": {
            "idle_in_transaction": "CRITICAL - These sessions are holding locks and preventing vacuum from cleaning up dead tuples",
            "long_transactions": "WARNING - These may be preventing vacuum from advancing its cleanup horizon",
            "old_xmin": "CRITICAL - These are preventing vacuum from reclaiming space from old transactions"
        },
        "immediate_actions": [
            "Identify 'idle in transaction' sessions",
            "Terminate idle sessions immediately: SELECT pg_terminate_backend(PID);",
            "Check if vacuum can proceed after termination",
            "Monitor table bloat reduction"
        ]
    }

@mcp.tool()
def analyze_query_plan_degradation(query_text: str, table_name: str = None) -> dict:
    """
    Analyze how vacuum blockers and bloat affect query execution plans
    
    Args:
        query_text: The slow query to analyze
        table_name: Optional table name to focus analysis
        
    Returns:
        Query plan analysis with bloat impact explanation
    """
    
    return {
        "analysis_type": "query_plan_degradation_analysis",
        "purpose": "Understand how vacuum blockers → bloat → query plan changes → performance degradation",
        "queries": {
            "current_plan_analysis": f"""
                -- CURRENT QUERY PLAN WITH BLOAT IMPACT
                EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) 
                {query_text};
            """,
            "table_bloat_impact_on_plan": """
                -- HOW BLOAT AFFECTS QUERY PLANNER DECISIONS
                WITH table_bloat_stats AS (
                    SELECT 
                        schemaname,
                        relname,
                        n_live_tup,
                        n_dead_tup,
                        round((n_dead_tup::numeric/nullif(n_live_tup+n_dead_tup,0))* 100,2) AS dead_tuple_percent,
                        seq_scan,
                        seq_tup_read,
                        idx_scan,
                        idx_tup_fetch,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||relname)) as total_size,
                        pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) as table_size
                    FROM pg_stat_user_tables 
                    WHERE relname = COALESCE('{table_name}', relname)
                ),
                planner_impact AS (
                    SELECT 
                        *,
                        CASE 
                            WHEN dead_tuple_percent > 30 THEN 'SEVERE - Planner may choose seq scans over index scans'
                            WHEN dead_tuple_percent > 20 THEN 'HIGH - Index scans become less efficient, more buffer reads'
                            WHEN dead_tuple_percent > 10 THEN 'MODERATE - Slight increase in I/O, bitmap heap scans may be lossy'
                            ELSE 'LOW - Minimal impact on query planning'
                        END as planner_impact,
                        CASE 
                            WHEN dead_tuple_percent > 30 THEN 'Query planner sees inflated table size, may avoid nested loops'
                            WHEN dead_tuple_percent > 20 THEN 'Index scans read many dead tuples, causing excessive buffer usage'
                            WHEN dead_tuple_percent > 10 THEN 'Bitmap scans become lossy due to memory pressure from dead tuples'
                            ELSE 'Query plans should be optimal'
                        END as plan_degradation_reason,
                        CASE 
                            WHEN dead_tuple_percent > 30 THEN seq_tup_read / NULLIF(seq_scan, 0)
                            ELSE NULL
                        END as avg_tuples_per_seq_scan,
                        CASE 
                            WHEN dead_tuple_percent > 20 THEN idx_tup_fetch / NULLIF(idx_scan, 0)
                            ELSE NULL
                        END as avg_tuples_per_idx_scan
                    FROM table_bloat_stats
                )
                SELECT 
                    schemaname,
                    relname,
                    dead_tuple_percent,
                    total_size,
                    planner_impact,
                    plan_degradation_reason,
                    CASE 
                        WHEN dead_tuple_percent > 30 THEN 'CRITICAL - Immediate vacuum needed to restore query performance'
                        WHEN dead_tuple_percent > 20 THEN 'HIGH - Vacuum recommended to improve query plans'
                        WHEN dead_tuple_percent > 10 THEN 'MODERATE - Monitor and schedule vacuum'
                        ELSE 'OK - No immediate action needed'
                    END as recommended_action,
                    CASE 
                        WHEN dead_tuple_percent > 30 THEN 'After vacuum: Expect 60-80% performance improvement'
                        WHEN dead_tuple_percent > 20 THEN 'After vacuum: Expect 40-60% performance improvement'
                        WHEN dead_tuple_percent > 10 THEN 'After vacuum: Expect 20-40% performance improvement'
                        ELSE 'Performance should remain stable'
                    END as expected_improvement
                FROM planner_impact;
            """,
            "index_efficiency_with_bloat": """
                -- INDEX EFFICIENCY DEGRADATION DUE TO BLOAT
                SELECT 
                    pui.schemaname,
                    pui.relname as tablename,
                    pui.indexrelname as indexname,
                    pui.idx_scan,
                    pui.idx_tup_read,
                    pui.idx_tup_fetch,
                    CASE 
                        WHEN pui.idx_tup_read > 0 AND pui.idx_tup_fetch > 0 
                        THEN round((pui.idx_tup_fetch::numeric / pui.idx_tup_read) * 100, 2)
                        ELSE 0
                    END as index_selectivity_percent,
                    CASE 
                        WHEN pui.idx_tup_read > pui.idx_tup_fetch * 5 THEN 'HIGH BLOAT IMPACT - Index reading many dead tuples'
                        WHEN pui.idx_tup_read > pui.idx_tup_fetch * 2 THEN 'MODERATE BLOAT IMPACT - Some dead tuple reads'
                        ELSE 'LOW BLOAT IMPACT - Index efficiency good'
                    END as bloat_impact_on_index,
                    pg_size_pretty(pg_relation_size(pui.indexrelid)) as index_size
                FROM pg_stat_user_indexes pui
                JOIN pg_stat_user_tables put ON pui.relid = put.relid
                WHERE put.relname = COALESCE('{table_name}', put.relname)
                AND pui.idx_scan > 0
                ORDER BY pui.idx_scan DESC;
            """
        },
        "plan_comparison_explanation": {
            "healthy_table_plan": "With <5% bloat: Index scans are efficient, bitmap scans are exact (not lossy), minimal buffer reads",
            "bloated_table_plan": "With >20% bloat: Index scans read dead tuples, bitmap scans become lossy, excessive buffer usage",
            "severely_bloated_plan": "With >30% bloat: Planner may choose seq scans, nested loops avoided, query times 5-10x slower"
        },
        "typical_plan_changes": [
            "Bitmap Index Scan → Bitmap Heap Scan (lossy) due to memory pressure",
            "Index Scan → Sequential Scan when bloat makes index inefficient", 
            "Nested Loop → Hash Join when table size estimates are inflated",
            "Index-only Scan → Index Scan when visibility map is outdated"
        ]
    }

@mcp.tool()
def get_parallel_execution_plan(workflow_result: dict) -> dict:
    """
    Generate a parallel execution plan for workflow + enhancement steps
    
    Args:
        workflow_result: Result from a diagnostic workflow function
        
    Returns:
        Optimized parallel execution plan
    """
    
    if not isinstance(workflow_result, dict) or 'execution_mode' not in workflow_result:
        return {"error": "Invalid workflow result - expected parallel_enhanced workflow"}
    
    core_steps = workflow_result.get('core_workflow_steps', [])
    enhancement = workflow_result.get('mandatory_parallel_enhancement', {})
    
    # Create parallel execution batches
    execution_plan = {
        "execution_strategy": "parallel_batched",
        "total_estimated_time": "30-45 seconds (vs 90-120 seconds serial)",
        "parallel_batches": [
            {
                "batch_id": 1,
                "description": "Core Database Analysis (PostgreSQL MCP)",
                "execution_type": "sequential_within_server",
                "steps": core_steps,
                "estimated_time": "15-20 seconds",
                "server": "postgres"
            },
            {
                "batch_id": 2, 
                "description": "Performance Metrics Collection (Parallel)",
                "execution_type": "parallel_across_servers",
                "steps": enhancement.get('performance_insights_steps', []),
                "estimated_time": "10-15 seconds",
                "server": "performance_insights"
            },
            {
                "batch_id": 3,
                "description": "Log Analysis & Infrastructure Metrics (Parallel)", 
                "execution_type": "parallel_across_servers",
                "steps": enhancement.get('cloudwatch_steps', []) + enhancement.get('aws_api_steps', []),
                "estimated_time": "10-15 seconds", 
                "servers": ["cloudwatch", "aws_api"]
            }
        ],
        "synchronization_points": [
            {
                "after_batch": [1, 2, 3],
                "action": "synthesize_results",
                "description": "Combine all results for comprehensive analysis"
            }
        ],
        "optimization_notes": [
            "Batches 1, 2, and 3 can execute simultaneously",
            "PostgreSQL queries within batch 1 should be sequential to avoid connection limits",
            "Performance Insights and CloudWatch calls can be fully parallel",
            "AWS API calls are lightweight and can be parallel with other batches"
        ]
    }
    
    return execution_plan

@mcp.tool()
def execute_diagnostic_step(step_data: dict) -> dict:
    """
    Execute a diagnostic step by returning the query to be run by PostgreSQL MCP server
    
    Args:
        step_data: Dictionary containing step information with 'query' key
    
    Returns:
        Dictionary with query and execution instructions
    """
    if 'query' not in step_data:
        return {"error": "No query found in step data"}
    
    return {
        "tool_to_use": "run_query",
        "sql_query": step_data['query'],
        "step_description": step_data.get('action', 'Execute diagnostic query'),
        "instructions": f"Execute this query using the PostgreSQL MCP server's run_query tool: {step_data['query']}"
    }

@mcp.tool()
def get_index_statistics(index_names: List[str]) -> dict:
    """Get detailed statistics for specific indexes
    
    Args:
        index_names: List of index names to analyze (e.g., ["idx_customer_email", "idx_order_date"])
    
    Returns:
        Dictionary with query and description for execution by PostgreSQL MCP server
    """
    if not index_names or len(index_names) == 0:
        return {"error": "index_names parameter is required. Provide a list of index names to analyze."}
    
    # Build IN clause safely
    index_list = "', '".join(index_names)
    query = f"""
        SELECT 
            schemaname,
            relname as tablename,
            indexrelname as indexname,
            idx_scan,
            idx_tup_read,
            idx_tup_fetch,
            pg_size_pretty(pg_relation_size(indexrelid)) as index_size
        FROM pg_stat_user_indexes 
        WHERE indexrelname IN ('{index_list}')
        ORDER BY indexrelname;
    """
    
    return {
        "tool_to_use": "run_query",
        "sql_query": query,
        "step_description": f"Get statistics for indexes: {', '.join(index_names)}",
        "instructions": f"Execute this query using the PostgreSQL MCP server's run_query tool to get index statistics"
    }

@mcp.tool()
def get_table_statistics(table_name: str) -> dict:
    """Get detailed statistics for a specific table
    
    Args:
        table_name: Name of the table to analyze (e.g., "customer", "orders")
    
    Returns:
        Dictionary with query and description for execution by PostgreSQL MCP server
    """
    if not table_name or table_name.strip() == "":
        return {"error": "table_name parameter is required. Provide the name of the table to analyze."}
    
    # Remove any placeholder text
    if '<' in table_name or '>' in table_name or 'add' in table_name.lower():
        return {"error": f"Invalid table_name '{table_name}'. Please provide an actual table name, not a placeholder."}
    
    query = f"""
        SELECT 
            schemaname,
            relname as tablename,
            seq_scan,
            seq_tup_read,
            idx_scan,
            idx_tup_fetch,
            n_live_tup,
            n_dead_tup,
            pg_size_pretty(pg_relation_size(schemaname||'.'||relname)) as table_size
        FROM pg_stat_user_tables 
        WHERE relname = '{table_name}'
        ORDER BY relname;
    """
    
    return {
        "tool_to_use": "run_query",
        "sql_query": query,
        "step_description": f"Get statistics for table: {table_name}",
        "instructions": f"Execute this query using the PostgreSQL MCP server's run_query tool to get table statistics"
    }

if __name__ == "__main__":
    mcp.run()
