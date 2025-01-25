FROM python:3.12-alpine AS builder
RUN apk add --no-cache gcc musl-dev linux-headers
WORKDIR /app
COPY ./requirements.txt ./requirements.txt
RUN python3 -m venv venv
RUN ./venv/bin/pip install --no-cache -r ./requirements.txt

FROM python:3.12-alpine
WORKDIR /app
COPY --from=builder /app/venv /app/venv
COPY . .
ENV PYHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH=/app/venv/bin:$PATH
EXPOSE 8000
ENTRYPOINT [ "/app/docker-entrypoint.sh" ]