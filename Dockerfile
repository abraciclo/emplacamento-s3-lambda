# Inside your Dockerfile
FROM lambci/lambda:build-python3.8
# Install Paramiko and other dependencies into /opt/python/
RUN pip install paramiko -t /opt/python/
WORKDIR /var/task
