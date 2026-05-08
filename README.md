# AWS ApiGateway, FastApi python in Lambd, DynamoDB & OpenTelemetry enabled for Observability

## Python Part for Deploying a zip archive in AWS Lambda:
In the python module we generate the zip file for AWS Lambda that includes the needed pip packages and the latest python code.

For Zip file Lambda version:
first, install dependencies from requirements.txt inside your venv.
And Later, package all the dependencies and zip it:

```
uv export --frozen --no-dev --no-editable -o requirements.txt

uv pip install \
   --no-installer-metadata \
   --no-compile-bytecode \
   --python-platform x86_64-manylinux2014 \
   --python 3.12 \
   --target package_to_zip \
   -r requirements.txt

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


After the zip file is located inside the `Terraform folder`!



## Items & Attributes in DynamoDB "item" Table

DynamoDB does NOT enforce schema, but you should define "expected" attributes:

```
Item attributes (regular items)
id                (String)  → PK
name              (String)
price             (Number)
tags              (List of String)
created_at        (String, ISO format)

# GSI attributes
gsi_pk            (String)
gsi_sk            (Number)
Stats item attributes
id                (String) → "STATS" (PK)

total_items       (Number)
total_price_sum   (Number)
```



## Grafana Cloud & OpenTelemetry:

First, go to Grafana Cloud to start the openTelemetry setup: 
```
https://<YOUR-PROFILE>.grafana.net/a/grafana-setupguide-app/getting-started/otel/
```
and select the option: 
```
"OpenTelemetry SDK" > "Python" > Serverless (cause I am working with Lambda) > OpenTelemetry Collector > Create a new Token > Get the Base64 converted "clientID:Token structure"
```

That base64 you will need to add in this Lambda Env Variable 
```
OTEL_EXPORTER_OTLP_HEADERS="Authorization=Basic <clientID:Token Base64 Structure>"
```

**Do not use the `%20` that Grafana Cloud suggest as empty space, intead use a normal empty space as shown above.

