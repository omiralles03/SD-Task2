data "archive_file" "lambda_zip" {
  type        = "zip"
  source_file = "${path.module}/../worker/lambda_function.py"
  output_path = "${path.module}/worker.zip"
}

resource "aws_lambda_function" "ticket_worker_lambda" {
  filename         = data.archive_file.lambda_zip.output_path
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  function_name = "TicketWorkerLambda"
  runtime       = "python3.11"
  handler       = "lambda_function.lambda_handler"

  role = "arn:aws:iam::${data.aws_caller_identity.current.account_id}:role/LabRole"

  timeout     = 30
  memory_size = 128

  environment {
    variables = {
      DB_HOST     = "54.227.12.74"
      DB_NAME     = "ticket_system"
      DB_USER     = "user"
      DB_PASSWORD = "123"
      DB_PORT     = "5432"
    }
  }
}

data "aws_caller_identity" "current" {}
