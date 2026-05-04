// HTTP API GATEWAY v2 (REST API is older, but this HTTP API is newer)
resource "aws_apigatewayv2_api" "lambda_apiGateway" {
  name          = "lambda-apiGateway"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_integration" "lambda_apiGateway_integration" {
  api_id                 = aws_apigatewayv2_api.lambda_apiGateway.id
  integration_type       = "AWS_PROXY"
  description            = "API Gateway proxy/forward EVERYTHING to FastAPI Lambda"
  integration_uri        = aws_lambda_function.fast_api_lambda.invoke_arn
  payload_format_version = "2.0"
}

resource "aws_apigatewayv2_route" "proxy_route" {
  api_id    = aws_apigatewayv2_api.lambda_apiGateway.id
  route_key = "ANY /{proxy+}"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_apiGateway_integration.id}"
}
resource "aws_apigatewayv2_route" "root_route" {
  api_id    = aws_apigatewayv2_api.lambda_apiGateway.id
  route_key = "ANY /"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_apiGateway_integration.id}"
}

resource "aws_apigatewayv2_stage" "example" {
  api_id      = aws_apigatewayv2_api.lambda_apiGateway.id
  name        = "$default"
  auto_deploy = true
}
