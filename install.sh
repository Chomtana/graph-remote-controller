#!/bin/bash

if ! docker compose --version; then
  # Run this two first

  sudo apt-get update
  sudo apt-get upgrade -y

  ### Docker and docker compose prerequisites
  sudo apt-get install -y curl
  sudo apt-get install -y gnupg
  sudo apt-get install -y ca-certificates
  sudo apt-get install -y lsb-release

  ### Download the docker gpg file to Ubuntu
  sudo mkdir -p /etc/apt/keyrings
  curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

  ### Add Docker and docker compose support to the Ubuntu's packages list
  echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

  sudo apt-get update
  
  ### Install docker and docker compose on Ubuntu
  sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
  
  ### Verify the Docker and docker compose install on Ubuntu
  sudo docker run hello-world

  ### Verify docker compose
  docker compose version
fi

curl https://bootstrap.pypa.io/get-pip.py | sudo python3

cd ~
if [ -d "graph-remote-controller" ]
then
  cd graph-remote-controller
  git pull
else
  git clone https://github.com/Chomtana/graph-remote-controller
fi

cd ~

python3 -m pip install quart

echo "[Unit]
Description=Graph Remote Allocation Controller
Wants=network-online.target
After=network-online.target
[Service]
User=root
Group=root
Type=simple
Restart=always
RestartSec=5
ExecStart=/usr/bin/python3 $HOME/graph-remote-controller/main.py
[Install]
WantedBy=multi-user.target" >> /etc/systemd/system/graph-remote-controller.service \

sudo systemctl daemon-reload
sudo systemctl restart graph-remote-controller
sudo systemctl enable graph-remote-controller

sudo ufw allow 1111
