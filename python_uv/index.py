from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4
from mangum import Mangum
from datetime import datetime
import json
import requests
import boto3
from botocore.exceptions import ClientError
import os
from decimal import Decimal
from boto3.dynamodb.conditions import Key

app = FastAPI(title="My Serious API")
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('items')

# --- Fake DB (in-memory) ---
items_db = []

# --- Stats (simulate DynamoDB STATS item) ---
stats_db = {
    "total_items": 0,
    "total_price_sum": 0.0
}

# --- Models ---
class Item(BaseModel):
    name: str = Field(..., min_length=2, max_length=50)
    price: float = Field(..., gt=0)
    tags: Optional[List[str]] = []


class ItemResponse(Item):
    id: str
    created_at: str


# --- Routes ---

@app.get("/")
async def root():
    return {"status": "ok"}


@app.post("/items", response_model=ItemResponse)
async def create_item(item: Item):
    new_item = item.dict()
    new_item["id"] = str(uuid4())
    new_item["created_at"] = datetime.utcnow().isoformat()

    # REQUIRED for DynamoDB GSI:
    new_item["gsi_pk"] = "ITEM"
    new_item["price"] = Decimal(str(new_item["price"]))
    new_item["gsi_sk"] = new_item["price"]

    # Creating a new item:
    try:
        response = table.put_item(
            Item={
                "id": new_item["id"],
                "name": new_item["name"],
                "price": new_item["price"],
                "tags": new_item["tags"],
                "created_at": new_item["created_at"],
                "gsi_pk": new_item["gsi_pk"],
                "gsi_sk": new_item["gsi_sk"]
            }
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise HTTPException(status_code=500, detail=f"Message: {error_message} - Error: {error_code}")

    # updating attributes of the "stats" item in the table  (DynamoDB-style thinking):
    try:
        response = table.update_item(
            Key={"id": "STATS"},
            UpdateExpression="""
                SET total_items = if_not_exists(total_items, :zero) + :inc,
                    total_price_sum = if_not_exists(total_price_sum, :zero) + :price
            """,
            ExpressionAttributeValues={
                ":inc": 1,
                ":price": new_item["price"],
                ":zero": Decimal("0")
            }
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise HTTPException(status_code=500, detail=f"Message: {error_message} - Error: {error_code}")

    print(new_item)
    new_item["price"] = float(new_item["price"])
    return new_item


@app.get("/items", response_model=List[ItemResponse])
async def list_items(min_price: float = Query(0, ge=0), max_price: float = Query(999999, ge=0)):
    try:
        response = table.query(
            IndexName='price-index',
            KeyConditionExpression=(
                Key('gsi_pk').eq('ITEM') &
                Key('gsi_sk').between(
                    Decimal(str(min_price)),
                    Decimal(str(max_price))
                )
            )
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise HTTPException(status_code=500, detail=f"Message: {error_message} - Error: {error_code}")
    
    items = response.get("Items", [])
    for item in items:
        if "price" in item:
            item["price"] = float(item["price"])
        item.pop("gsi_pk", None)
        item.pop("gsi_sk", None)
    
    return items

@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    try:
        # 1. Get item by ID
        response = table.get_item(Key={"id": item_id})
        item = response.get("Item")

        if not item:
            raise HTTPException(status_code=404, detail="Item not found")

        price = item["price"]  # This is already Decimal

        # 2. Delete item
        table.delete_item(Key={"id": item_id})

        # 3. Update stats
        table.update_item(
            Key={"id": "STATS"},
            UpdateExpression="""
                SET total_items = if_not_exists(total_items, :zero) - :inc,
                    total_price_sum = if_not_exists(total_price_sum, :zero) - :price
            """,
            ExpressionAttributeValues={
                ":inc": 1,
                ":price": price,
                ":zero": Decimal("0")
            }
        )

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise HTTPException(status_code=500, detail=f"Message: {error_message} - Error: {error_code}")

    return {"deleted": True}


@app.get("/stats")
async def stats():
    try:
        response = table.get_item(
            Key={"id": "STATS"}
        )
    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']
        raise HTTPException(status_code=500, detail=f"Message: {error_message} - Error: {error_code}")

    item = response.get("Item")

    if not item:
        # No stats yet → return empty state
        return {
            "total_items": 0,
            "average_price": 0
        }

    total = item.get("total_items", 0)
    total_price_sum = item.get("total_price_sum", 0)

    avg_price = (
        float(total_price_sum) / total
        if total > 0 else 0
    )

    return {
        "total_items": total,
        "average_price": avg_price
    }


# FOR INITIAL CONNECTION TESTING:
# @app.get("/test-connection-dynamodb")
# async def test_dynamodb():
#     try:
#         # Test DynamoDB connection
#         table_info = {
#             'table_name': table.table_name,
#             'creation_time': str(table.creation_date_time),
#             'table_status': table.table_status
#         }
        
#         return {
#             'status': 'success',
#             'message': 'DynamoDB connection successful',
#             'table_info': table_info
#         }
        
#     except ClientError as e:
#         return {
#             'status': 'error',
#             'message': 'Failed to connect to DynamoDB',
#             'error': str(e)
#         }
#     except Exception as e:
#         return {
#             'status': 'error',
#             'message': 'Unexpected error occurred',
#             'error': str(e)
#         }


handler = Mangum(app, lifespan="off", api_gateway_base_path=None)