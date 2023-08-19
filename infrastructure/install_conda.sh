#!/bin/bash

cd ~
sudo apt install wget unzip -y
wget -q https://repo.anaconda.com/miniconda/Miniconda3-py310_23.5.2-0-Linux-x86_64.sh -O Miniconda3-py310_23.5.2-0-Linux-x86_64.sh
bash ~/Miniconda3-py310_23.5.2-0-Linux-x86_64.sh -b
~/miniconda3/bin/conda init $SHELL_NAME
rm Miniconda3-py310_23.5.2-0-Linux-x86_64.sh
