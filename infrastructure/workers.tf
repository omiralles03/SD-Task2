resource "aws_instance" "workers_ec2" {
  ami           = "ami-091138d0f0d41ff90" # Ubuntu 26.04 LTS
  instance_type = "t3.medium"
  key_name      = "practica"

  vpc_security_group_ids = [aws_security_group.workers_sg.id]

  root_block_device {
    volume_size = 20 # GB storage
    volume_type = "gp3"
  }

  user_data = <<-EOF
              #!/bin/bash
              apt-get update
              apt-get install -y python3-pip python3-venv
              EOF

  tags = {
    Name = "Workers-Controller EC2"
  }
}
