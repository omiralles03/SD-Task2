resource "aws_instance" "rabbitMQ" {
  ami           = "ami-091138d0f0d41ff90" # Ubuntu 26.04 LTS
  instance_type = "t3.medium"
  key_name      = "practica"

  vpc_security_group_ids = [aws_security_group.sd_task2_sg.id]

  root_block_device {
    volume_size = 20 # GB storage
    volume_type = "gp3"
  }

  tags = {
    Name = "RabbitMQ EC2"
  }
}
