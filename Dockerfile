FROM rockylinux:9
RUN dnf install -y python3 python3-pip && dnf clean all
WORKDIR /opt/suture
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY . .
RUN chmod +x suture
ENV PYTHONPATH=/opt/suture
ENTRYPOINT ["python3", "/opt/suture/suture"]
CMD ["--help"]
