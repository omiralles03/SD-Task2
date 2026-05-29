resource "aws_instance" "postgres_ec2" {
  ami           = "ami-091138d0f0d41ff90" # Ubuntu 26.04 LTS
  instance_type = "t3.medium"
  key_name      = "practica"

  vpc_security_group_ids = [aws_security_group.postgres_sg.id]

  root_block_device {
    volume_size = 20 # GB storage
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y docker.io
              systemctl enable --now docker
                
              docker run -d --name postgres -p 5432:5432 \
                -e POSTGRES_USER=user \
                -e POSTGRES_PASSWORD=123 \
                -e POSTGRES_DB=ticket_system \
                postgres:16-alpine
              EOF

  tags = {
    Name = "PosgreSQL"
  }
}
