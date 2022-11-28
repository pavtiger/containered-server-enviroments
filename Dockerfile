FROM ubuntu:22.04
RUN apt update && apt install openssh-server vim git htop python3 python3-pip iproute2 zsh byobu sudo -y
# Create a user “sshuser” and group “sshgroup”
# RUN groupadd sshgroup && useradd -ms /bin/bash -g sshgroup sshuser
# Create sshuser directory in home
# RUN mkdir -p /home/sshuser/.ssh
# Copy the ssh public key in the authorized_keys file. The idkey.pub below is a public key file you get from ssh-keygen. They are under ~/.ssh directory by default.
# COPY id_rsa.pub /home/sshuser/.ssh/authorized_keys
# change ownership of the key file. 
# RUN chown sshuser:sshgroup /home/sshuser/.ssh/authorized_keys && chmod 600 /home/sshuser/.ssh/authorized_keys
# RUN useradd -m john && echo "john:john" | chpasswd && adduser john sudo

RUN git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
COPY .p10k.zsh /home/.p10k.zsh
COPY .zshrc /home/.zshrc
COPY .oh-my-zsh /home/.oh-my-zsh

RUN echo "PermitRootLogin no" >> /etc/ssh/sshd_config

# Start SSH service
RUN service ssh start

# Expose docker port 22
EXPOSE 22
CMD ["/usr/sbin/sshd","-D"]
