# AWS API Gateway + FastAPI (Python) + Lambda + DynamoDB + OpenTelemetry

Serverless FastAPI application running on AWS Lambda behind API Gateway, using DynamoDB as persistence layer and OpenTelemetry + Grafana Cloud for observability.

---

# Architecture

```text
Client
   ↓
API Gateway (HTTP API)
   ↓
AWS Lambda (FastAPI + Mangum)
   ↓
DynamoDB
   ↓
OpenTelemetry SDK
   ↓
Grafana Cloud (Tempo + Mimir)
```

---

# Tech Stack

- AWS Lambda
- API Gateway v2 (HTTP API)
- FastAPI
- Mangum
- DynamoDB
- Terraform
- OpenTelemetry
- Grafana Cloud
- uv (Python package manager)

---

# Packaging Python for AWS Lambda

The Lambda deployment uses a ZIP archive containing:

- Python source code
- Installed dependencies
- OpenTelemetry libraries
- FastAPI application

## Generate requirements.txt

```bash
uv export --frozen --no-dev --no-editable -o requirements.txt
```

## Install dependencies into deployment folder

```bash
uv pip install \
   --no-installer-metadata \
   --no-compile-bytecode \
   --python-platform x86_64-manylinux2014 \
   --python 3.12 \
   --target package_to_zip \
   -r requirements.txt
```

## Package Lambda ZIP

```bash
cp index.py package_to_zip/

cd package_to_zip

zip -r ../../terraform/lambda.zip . \
  -x "*__pycache__*" \
  -x "*.pyc" \
  -x "*.pyo" \
  -x "*.dist-info/RECORD" \
  -x "*.dist-info/WHEEL"

cd ..
```

The generated `lambda.zip` must be placed inside the Terraform directory.

---

# DynamoDB Table Design

## Table

```text
items
```

## Primary Key

| Attribute | Type |
|---|---|
| id | String |

---

# Expected Item Attributes

## Regular Items

| Attribute | Type | Description |
|---|---|---|
| id | String | Primary key |
| name | String | Item name |
| price | Number | Item price |
| tags | List[String] | Item tags |
| created_at | String | ISO datetime |
| gsi_pk | String | GSI partition key |
| gsi_sk | Number | GSI sort key |

---

## Stats Item

Single aggregated item used for lightweight statistics.

| Attribute | Type | Description |
|---|---|---|
| id | String | Fixed value: `STATS` |
| total_items | Number | Total items count |
| total_price_sum | Number | Running price total |

---

# Global Secondary Index (GSI)

## price-index

| Attribute | Type |
|---|---|
| gsi_pk | String |
| gsi_sk | Number |

Used for querying items by price range.

---

# OpenTelemetry + Grafana Cloud

## Grafana Cloud Setup

Open the Grafana Cloud OpenTelemetry setup page:

```text
https://<YOUR_GRAFANA_STACK>.grafana.net/a/grafana-setupguide-app/getting-started/otel/
```

Recommended setup path:

```text
OpenTelemetry SDK
→ Python
→ Serverless
→ OpenTelemetry Collector
```

Create a Grafana Cloud access token and generate the Base64 value:

```text
clientID:token
```

---

# Lambda Environment Variables

```text
OTEL_EXPORTER_OTLP_PROTOCOL=http/protobuf

OTEL_EXPORTER_OTLP_TRACES_ENDPOINT=https://<region>.grafana.net/otlp/v1/traces

OTEL_EXPORTER_OTLP_METRICS_ENDPOINT=https://<region>.grafana.net/otlp/v1/metrics

OTEL_EXPORTER_OTLP_HEADERS=Authorization=Basic <BASE64_CLIENTID_TOKEN>
```

Important:

Use a normal whitespace after `Basic`.

Correct:

```text
Authorization=Basic abc123
```

Incorrect:

```text
Authorization=Basic%20abc123
```

---

# Lambda Insights

Lambda Insights is enabled for:

- memory metrics
- cold start visibility
- CPU/runtime telemetry
- invocation analysis

Metrics are available in:

```text
AWS Console
→ Lambda
→ Monitor
→ Lambda Insights
```

---

# Grafana Dashboard

Dashboard JSON is located in:

```text
grafana_dashboard/
```

Import the dashboard manually in Grafana:

```text
Dashboards
→ Import
→ Upload JSON file
```

---

# Example PromQL Queries

## Total API requests (last hour)

```promql
increase(api_requests_total[1h])
```

## Items created (last hour)

```promql
increase(items_created_total[1h])
```

## Items deleted (last hour)

```promql
increase(items_deleted_total[1h])
```

## Delete/Create ratio

```promql
increase(items_deleted_total[1h])
/
increase(items_created_total[1h])
```

## HTTP 5xx errors

```promql
sum(rate(http_server_duration_milliseconds_count{http_status_code=~"5.."}[5m]))
```

---

# TraceQL Examples

## Recent traces

```traceql
{ resource.service.name = "fastapi-lambda" }
```

## Slow traces

```traceql
{ resource.service.name = "fastapi-lambda" && duration > 500ms }
```

## Error traces

```traceql
{ resource.service.name = "fastapi-lambda" && status = error }
```

---

# Local Development

Run FastAPI locally:

```bash
uvicorn index:app --reload
```

Swagger UI:

```text
http://127.0.0.1:8000/docs
```

---

# Terraform Components

Infrastructure managed with Terraform:

- Lambda Function
- API Gateway v2
- DynamoDB
- IAM Roles & Policies
- Lambda Permissions
- Lambda Insights Layer

---

# Notes

- DynamoDB uses `PAY_PER_REQUEST` billing mode.
- OpenTelemetry traces and metrics are exported directly from Lambda.
- FastAPI runs inside Lambda using Mangum ASGI adapter.
- Grafana Tempo is used for distributed traces.
- Grafana Mimir/Prometheus is used for metrics.
- CloudWatch stores Lambda runtime logs and Lambda Insights telemetry.