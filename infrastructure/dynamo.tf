resource "aws_dynamodb_table" "ticket_store" {
  name           = "NumberedTickets"
  billing_mode   = "PAY_PER_REQUEST"
  hash_key       = "seat_id"

  attribute {
    name = "seat_id"
    type = "S"
  }
}
