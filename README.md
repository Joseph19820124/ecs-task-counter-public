# ECS Task Counter

AWS Lambda function that monitors ECS cluster tasks and stores the data in Supabase.

## Live Demo

https://joseph19820124.github.io/ecs-task-counter-public/

## Features

- Counts total running tasks across all services in an ECS cluster
- Stores task count history in Supabase
- Web dashboard to visualize the data
- Secure API proxy (credentials stored in Lambda environment variables)

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   GitHub Pages  │────▶│  Lambda API     │────▶│    Supabase     │
│   (Frontend)    │     │  (Proxy)        │     │   (Database)    │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                               │
                               ▼
                        ┌─────────────────┐
                        │  Lambda Counter │────▶ ECS Cluster
                        │  (Data Writer)  │
                        └─────────────────┘
```

## Lambda Functions

### 1. Counter Function (`lambda_function.py`)

Counts ECS tasks and writes to Supabase.

**Environment Variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anon key
- `CLUSTER_ARN` - ECS cluster ARN to monitor
- `CLUSTER_NAME` - Friendly name for the cluster

### 2. API Function (`api_function.py`)

Public API endpoint that proxies requests to Supabase.

**Environment Variables:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Your Supabase anon key

## Deployment

### 1. Create IAM Role

```bash
aws iam create-role \
  --role-name ecs-task-counter-lambda-role \
  --assume-role-policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Principal": {"Service": "lambda.amazonaws.com"},
      "Action": "sts:AssumeRole"
    }]
  }'
```

### 2. Attach Policies

```bash
aws iam put-role-policy \
  --role-name ecs-task-counter-lambda-role \
  --policy-name ecs-read-policy \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [
      {
        "Effect": "Allow",
        "Action": ["ecs:ListServices", "ecs:DescribeServices"],
        "Resource": "*"
      },
      {
        "Effect": "Allow",
        "Action": ["logs:CreateLogGroup", "logs:CreateLogStream", "logs:PutLogEvents"],
        "Resource": "arn:aws:logs:*:*:*"
      }
    ]
  }'
```

### 3. Deploy Lambda Functions

```bash
cd lambda
zip function.zip lambda_function.py

aws lambda create-function \
  --function-name ecs-task-counter \
  --runtime python3.12 \
  --handler lambda_function.lambda_handler \
  --zip-file fileb://function.zip \
  --role <your-role-arn> \
  --environment "Variables={SUPABASE_URL=<url>,SUPABASE_ANON_KEY=<key>,CLUSTER_ARN=<arn>,CLUSTER_NAME=<name>}"
```

### 4. Create API with Function URL

```bash
zip api_function.zip api_function.py

aws lambda create-function \
  --function-name ecs-task-counter-api \
  --runtime python3.12 \
  --handler api_function.lambda_handler \
  --zip-file fileb://api_function.zip \
  --role <your-role-arn> \
  --environment "Variables={SUPABASE_URL=<url>,SUPABASE_ANON_KEY=<key>}"

aws lambda create-function-url-config \
  --function-name ecs-task-counter-api \
  --auth-type NONE \
  --cors 'AllowOrigins=*,AllowMethods=GET,AllowHeaders=Content-Type'
```

## Supabase Table Schema

```sql
CREATE TABLE clusters (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  total_task_number INTEGER NOT NULL,
  cluster_name TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## License

MIT
