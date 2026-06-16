FROM python:3.9-slim

WORKDIR /code
COPY . /code

# Copy the certificate files to the appropriate location in the container
COPY certificates/cert.pem /etc/ssl/certs/cert.pem
COPY certificates/key.pem /etc/ssl/private/key.pem

RUN pip3 install -r requirements.txt

CMD ["sh", "-c", "uvicorn server:app --host 0.0.0.0  --ssl-keyfile /etc/ssl/private/key.pem --ssl-certfile /etc/ssl/certs/cert.pem --port ${AUTH_PORT}"]

