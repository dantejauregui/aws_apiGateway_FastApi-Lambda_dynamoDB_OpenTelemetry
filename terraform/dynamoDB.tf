resource "aws_dynamodb_table" "item_table" {
  name           = "items"
  hash_key       = "id"
  billing_mode   = "PAY_PER_REQUEST"
  stream_enabled = false

  attribute {
    name = "id"
    type = "S"
  }
  attribute {
    name = "gsi_pk"
    type = "S"
  }
  attribute {
    name = "gsi_sk"
    type = "N"
  }

  global_secondary_index {
    name = "price-index"
    #For "ITEM":
    hash_key = "gsi_pk"
    #For price:
    range_key       = "gsi_sk"
    projection_type = "ALL"
  }

  tags = {
    Name        = "dynamodb-table-1"
    Environment = "dev"
  }
}
