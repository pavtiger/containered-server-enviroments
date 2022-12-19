FROM ubuntu:22.04
RUN apt update && apt install openssh-server wget curl vim git htop python3 python3-pip iproute2 zsh byobu sudo -y

RUN echo "PermitRootLogin no" >> /etc/ssh/sshd_config

# Start SSH service
RUN service ssh start

# Expose docker port 22
EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]
