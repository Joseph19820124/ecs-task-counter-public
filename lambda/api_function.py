"""
ECS Task Counter API Lambda Function

Provides a public API endpoint to fetch cluster data from Supabase.
This acts as a proxy to keep Supabase credentials secure.

Environment Variables Required:
- SUPABASE_URL: Your Supabase project URL
- SUPABASE_ANON_KEY: Your Supabase anon/public key
"""

import json
import os
import urllib.request

# Configuration from environment variables
SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_ANON_KEY = os.environ.get('SUPABASE_ANON_KEY')


def lambda_handler(event, context):
    """API endpoint to fetch clusters data from Supabase"""

    url = f"{SUPABASE_URL}/rest/v1/clusters?select=*&order=created_at.desc&limit=10"

    headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Authorization": f"Bearer {SUPABASE_ANON_KEY}",
        "Content-Type": "application/json"
    }

    req = urllib.request.Request(url, headers=headers, method='GET')

    try:
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode('utf-8'))

            # Note: CORS headers are handled by Lambda Function URL config
            # Do NOT add them here to avoid duplicate headers
            return {
                'statusCode': 200,
                'headers': {
                    'Content-Type': 'application/json'
                },
                'body': json.dumps(data)
            }
    except Exception as e:
        return {
            'statusCode': 500,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps({'error': str(e)})
        }
