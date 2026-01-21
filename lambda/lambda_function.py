"""
ECS Task Counter Lambda Function

Counts running tasks across all services in an ECS cluster and stores
the count in Supabase.

Environment Variables Required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_ANON_KEY: Your Supabase anon/public key
- CLUSTER_ARN: The ARN of the ECS cluster to monitor
- CLUSTER_NAME: A friendly name for the cluster
"""

import boto3
import json
import os
import urllib.request
import uuid
from datetime import datetime, timezone

# Configuration from environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')
CLUSTER_ARN = os.environ.get('CLUSTER_ARN')
CLUSTER_NAME = os.environ.get('CLUSTER_NAME')
REGION = os.environ.get('AWS_REGION', 'us-east-1')


def write_to_supabase(total_task_number, cluster_name):
    """Write task count to Supabase clusters table"""
    url = f"{SUPABASE_URL}/rest/v1/clusters"

    data = {
        "id": str(uuid.uuid4()),
        "total_task_number": total_task_number,
        "cluster_name": cluster_name,
        "created_at": datetime.now(timezone.utc).isoformat()
    }

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation"
    }

    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers=headers,
        method='POST'
    )

    with urllib.request.urlopen(req) as response:
        result = json.loads(response.read().decode('utf-8'))
        return result


def lambda_handler(event, context):
    ecs = boto3.client('ecs', region_name=REGION)

    # List all services in the cluster
    service_arns = []
    paginator = ecs.get_paginator('list_services')
    for page in paginator.paginate(cluster=CLUSTER_ARN):
        service_arns.extend(page['serviceArns'])

    total_running_tasks = 0
    services_detail = []

    if service_arns:
        # Describe services to get running task counts (batch of 10)
        for i in range(0, len(service_arns), 10):
            batch = service_arns[i:i+10]
            response = ecs.describe_services(cluster=CLUSTER_ARN, services=batch)

            for service in response['services']:
                running_count = service['runningCount']
                total_running_tasks += running_count
                services_detail.append({
                    'serviceName': service['serviceName'],
                    'runningCount': running_count,
                    'desiredCount': service['desiredCount']
                })

    # Write to Supabase
    supabase_result = write_to_supabase(total_running_tasks, CLUSTER_NAME)

    result = {
        'cluster': CLUSTER_ARN,
        'cluster_name': CLUSTER_NAME,
        'total_services': len(service_arns),
        'total_running_tasks': total_running_tasks,
        'services': services_detail,
        'supabase_insert': supabase_result
    }

    print(json.dumps(result, indent=2, default=str))

    return {
        'statusCode': 200,
        'body': json.dumps(result, default=str)
    }
