from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from uuid import uuid4
from mangum import Mangum
from datetime import datetime
import json
import requests
import boto3
import os

app = FastAPI(title="My Serious API")

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

    # 👉 REQUIRED for DynamoDB GSI:
    # new_item["gsi_pk"] = "ITEM"
    # new_item["gsi_sk"] = new_item["price"]

    # store item
    items_db.append(new_item)

    # update stats (DynamoDB-style thinking)
    stats_db["total_items"] += 1
    stats_db["total_price_sum"] += new_item["price"]

    return new_item


@app.get("/items", response_model=List[ItemResponse])
async def list_items(
    min_price: float = Query(0, ge=0),
    max_price: float = Query(999999, ge=0)
):
    # still scan locally, but later this becomes a GSI query
    return [
        item for item in items_db
        if min_price <= item["price"] <= max_price
    ]


@app.get("/items/{item_id}", response_model=ItemResponse)
async def get_item(item_id: str):
    for item in items_db:
        if item["id"] == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")


@app.delete("/items/{item_id}")
async def delete_item(item_id: str):
    for i, item in enumerate(items_db):
        if item["id"] == item_id:
            removed = items_db.pop(i)

            # update stats (critical for DynamoDB design)
            stats_db["total_items"] -= 1
            stats_db["total_price_sum"] -= removed["price"]

            return {"deleted": True}

    raise HTTPException(status_code=404, detail="Item not found")


@app.get("/stats")
async def stats():
    total = stats_db["total_items"]

    avg_price = (
        stats_db["total_price_sum"] / total
        if total > 0 else 0
    )

    return {
        "total_items": total,
        "average_price": avg_price
    }


handler = Mangum(app, lifespan="off", api_gateway_base_path="/")