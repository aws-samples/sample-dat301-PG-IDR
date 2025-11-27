#!/usr/bin/env python3
import boto3
import json
from datetime import datetime, timedelta
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("PI-MCP-Server")

def get_pi_client():
    session = boto3.Session(region_name="us-west-2")
    return session.client('pi')

@mcp.tool()
def get_cluster_identifier(cluster_name: str = "dat301-ws-cluster"):
    """Get the RDS instance identifier from a cluster name
    
    This is a helper tool to get the correct instance identifier for Performance Insights.
    Call this FIRST before using other PI tools if you only have the cluster name.
    
    Args:
        cluster_name: The RDS cluster name (default: dat301-ws-cluster)
    
    Returns:
        Dictionary with instance_identifier and cluster_info
    """
    try:
        session = boto3.Session(region_name="us-west-2")
        rds_client = session.client('rds')
        
        response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster_name)
        if not response['DBClusters']:
            return {"error": f"No cluster found with name: {cluster_name}"}
        
        cluster = response['DBClusters'][0]
        if not cluster.get('DBClusterMembers'):
            return {"error": f"Cluster {cluster_name} has no instances"}
        
        # Get writer instance (preferred for Performance Insights)
        writer_instance = None
        all_instances = []
        
        for member in cluster['DBClusterMembers']:
            instance_id = member['DBInstanceIdentifier']
            all_instances.append({
                "instance_id": instance_id,
                "is_writer": member.get('IsClusterWriter', False)
            })
            if member.get('IsClusterWriter'):
                writer_instance = instance_id
        
        if not writer_instance:
            writer_instance = all_instances[0]['instance_id']
        
        return {
            "cluster_name": cluster_name,
            "writer_instance": writer_instance,
            "all_instances": all_instances,
            "message": f"Use this instance identifier for Performance Insights: {writer_instance}",
            "example": f'get_wait_events(cluster_identifier="{writer_instance}")'
        }
    
    except Exception as e:
        return {
            "error": str(e),
            "help": "Make sure the cluster name is correct. Default cluster is 'dat301-ws-cluster'"
        }

def get_rds_resource_id(cluster_identifier: str):
    """Get the correct RDS instance resource ID for Performance Insights
    
    Accepts either cluster name or instance name and auto-discovers the instance.
    """
    session = boto3.Session(region_name="us-west-2")
    rds_client = session.client('rds')
    
    # Try as instance identifier first
    try:
        response = rds_client.describe_db_instances(DBInstanceIdentifier=cluster_identifier)
        return response['DBInstances'][0]['DbiResourceId']
    except rds_client.exceptions.DBInstanceNotFoundFault:
        # Not an instance, try as cluster identifier
        pass
    except Exception as e:
        # If it's not a "not found" error, re-raise
        if "DBInstanceNotFound" not in str(e):
            raise
    
    # Try as cluster identifier - get first instance
    try:
        response = rds_client.describe_db_clusters(DBClusterIdentifier=cluster_identifier)
        if not response['DBClusters']:
            raise ValueError(f"No cluster found with identifier: {cluster_identifier}")
        
        cluster = response['DBClusters'][0]
        if not cluster.get('DBClusterMembers'):
            raise ValueError(f"Cluster {cluster_identifier} has no instances")
        
        # Get the first instance (writer preferred)
        instance_id = None
        for member in cluster['DBClusterMembers']:
            if member.get('IsClusterWriter'):
                instance_id = member['DBInstanceIdentifier']
                break
        
        if not instance_id:
            # No writer found, use first instance
            instance_id = cluster['DBClusterMembers'][0]['DBInstanceIdentifier']
        
        # Now get the resource ID for this instance
        response = rds_client.describe_db_instances(DBInstanceIdentifier=instance_id)
        return response['DBInstances'][0]['DbiResourceId']
    
    except Exception as e:
        raise ValueError(f"Could not find instance or cluster with identifier '{cluster_identifier}': {str(e)}")

@mcp.tool()
def get_performance_insights_metrics(cluster_identifier: str, metric_queries: list = None, start_time: str = None, end_time: str = None):
    """Get Performance Insights metrics for RDS instance
    
    Args:
        cluster_identifier: RDS instance identifier (REQUIRED) - Use get_cluster_identifier() first if you only have cluster name
        metric_queries: List of metric queries
        start_time: Start time in ISO format
        end_time: End time in ISO format
    """
    try:
        if not cluster_identifier:
            return {
                "error": "cluster_identifier parameter is REQUIRED",
                "help": "Call get_cluster_identifier() first to get the instance identifier",
                "example": 'Step 1: result = get_cluster_identifier(cluster_name="dat301-ws-cluster")\nStep 2: get_performance_insights_metrics(cluster_identifier=result["writer_instance"])'
            }
        
        pi_client = get_pi_client()
        resource_id = get_rds_resource_id(cluster_identifier)
        
        if not start_time:
            start_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        if not end_time:
            end_time = datetime.utcnow().isoformat()
        
        if not metric_queries:
            # Default metrics for lock analysis
            metric_queries = [
                #{"Metric": "db.SQL.Innodb_rows_read.avg"},
                #{"Metric": "db.wait_event.Lock/transactionid.avg"},
                #{"Metric": "db.wait_event.Lock/tuple.avg"}
                {"Metric": "db.load.avg"},
                {"Metric": "db.SQL.total_query_time.avg"},
                {"Metric": "db.SQL.total_rows_returned.avg"}
            ]
        
        response = pi_client.get_resource_metrics(
            ServiceType='RDS',
            Identifier=resource_id,
            MetricQueries=metric_queries,
            StartTime=start_time,
            EndTime=end_time,
            PeriodInSeconds=300
        )
        
        return response
    except ValueError as e:
        return {
            "error": str(e),
            "help": "Call get_cluster_identifier() first to get the correct instance identifier",
            "example": 'get_cluster_identifier(cluster_name="dat301-ws-cluster")'
        }
    except Exception as e:
        return {
            "error": f"Performance Insights API error: {str(e)}",
            "help": "Make sure Performance Insights is enabled for this instance"
        }

@mcp.tool()
def get_top_sql_statements(cluster_identifier: str, limit: int = 10):
    """Get top SQL statements from Performance Insights
    
    Args:
        cluster_identifier: RDS instance identifier (REQUIRED) - Use get_cluster_identifier() first if you only have cluster name
        limit: Maximum number of results to return
    """
    try:
        if not cluster_identifier:
            return {
                "error": "cluster_identifier parameter is REQUIRED",
                "help": "Call get_cluster_identifier() first to get the instance identifier",
                "example": 'Step 1: result = get_cluster_identifier(cluster_name="dat301-ws-cluster")\nStep 2: get_top_sql_statements(cluster_identifier=result["writer_instance"])'
            }
        
        pi_client = get_pi_client()
        resource_id = get_rds_resource_id(cluster_identifier)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        response = pi_client.describe_dimension_keys(
            ServiceType='RDS',
            Identifier=resource_id,
            Metric='db.load.avg', #changed by chirag
            #GroupBy={'Group': 'db.sql_tokenized'},
            GroupBy={'Group': 'db.sql'},
            StartTime=start_time.isoformat(),
            EndTime=end_time.isoformat(),
            MaxResults=limit
        )
        
        return response
    except ValueError as e:
        return {
            "error": str(e),
            "help": "Call get_cluster_identifier() first to get the correct instance identifier",
            "example": 'get_cluster_identifier(cluster_name="dat301-ws-cluster")'
        }
    except Exception as e:
        return {
            "error": f"Performance Insights API error: {str(e)}",
            "help": "Make sure Performance Insights is enabled for this instance"
        }

@mcp.tool()
def get_wait_events(cluster_identifier: str, limit: int = 10):
    """Get top wait events from Performance Insights for lock analysis
    
    Args:
        cluster_identifier: RDS instance identifier (REQUIRED) - Use get_cluster_identifier() first if you only have cluster name
        limit: Maximum number of results to return
    """
    try:
        if not cluster_identifier:
            return {
                "error": "cluster_identifier parameter is REQUIRED",
                "help": "Call get_cluster_identifier() first to get the instance identifier",
                "example": 'Step 1: result = get_cluster_identifier(cluster_name="dat301-ws-cluster")\nStep 2: get_wait_events(cluster_identifier=result["writer_instance"])'
            }
        
        pi_client = get_pi_client()
        resource_id = get_rds_resource_id(cluster_identifier)
        
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=1)
        
        response = pi_client.describe_dimension_keys(
            ServiceType='RDS',
            Identifier=resource_id,
            Metric='db.load.avg', #chirag changed this
            GroupBy={'Group': 'db.wait_event'},
            StartTime=start_time.isoformat(),
            EndTime=end_time.isoformat(),
            MaxResults=limit
        )
        
        return response
    except ValueError as e:
        return {
            "error": str(e),
            "help": "Call get_cluster_identifier() first to get the correct instance identifier",
            "example": 'get_cluster_identifier(cluster_name="dat301-ws-cluster")'
        }
    except Exception as e:
        return {
            "error": f"Performance Insights API error: {str(e)}",
            "help": "Make sure Performance Insights is enabled for this instance"
        }

if __name__ == "__main__":
    mcp.run()