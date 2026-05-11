resource "aws_lambda_function" "fast_api_lambda" {
  function_name    = "fast_api_function"
  filename         = "lambda.zip"
  source_code_hash = filebase64sha256("lambda.zip")
  role             = aws_iam_role.fast_api_lambda_role.arn
  # Due to is used in python code "handler = Mangum(app)", the handler is (index.py name and Mangum handler name):
  handler     = "index.handler"
  runtime     = "python3.12"
  memory_size = 256
  timeout     = 30

  environment {
    variables = {
      OTEL_EXPORTER_OTLP_TRACES_ENDPOINT  = "https://otlp-gateway-prod-eu-west-2.grafana.net/otlp/v1/traces",
      OTEL_EXPORTER_OTLP_METRICS_ENDPOINT = "https://otlp-gateway-prod-eu-west-2.grafana.net/otlp/v1/metrics",
      GRAFANA_CLOUD_OTEL_TOKEN            = var.grafanaCloud_otel_token
      OTEL_EXPORTER_OTLP_PROTOCOL         = "http/protobuf"
    }
  }

  layers = [
    var.lambda_insights_arn_x86_64
  ]
}

# Identity-based Trust-Policy for Lambda (WHO can use this role)
data "aws_iam_policy_document" "trust_policy" {
  statement {
    effect = "Allow"

    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }

    actions = ["sts:AssumeRole"]
  }
}
resource "aws_iam_role" "fast_api_lambda_role" {
  name               = "lambda_execution_role"
  assume_role_policy = data.aws_iam_policy_document.trust_policy.json
}
# Identity-based Permission-Policy for Lambda (WHAT this role can do):
data "aws_iam_policy_document" "permission_policy" {
  statement {
    effect = "Allow"

    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents",

      "dynamodb:DescribeTable",
      "dynamodb:PutItem",
      "dynamodb:GetItem",
      "dynamodb:DeleteItem",
      "dynamodb:UpdateItem",
      "dynamodb:Query",
      "dynamodb:TransactWriteItems",

      "cloudwatch:PutMetricData"
    ]

    resources = ["*"]
  }
}
resource "aws_iam_role_policy" "lambda_permission_list" {
  name   = "lambda_permission_list"
  role   = aws_iam_role.fast_api_lambda_role.id
  policy = data.aws_iam_policy_document.permission_policy.json
}

# Resource-based policy allowing granting permission to invoke Lambda function (WHO can access this resource):
resource "aws_lambda_permission" "fast_api_lambda" {
  statement_id  = "AllowAPIGatewayInvoke"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fast_api_lambda.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.lambda_apiGateway.execution_arn}/*/*/*"
}
