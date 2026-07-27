# KIX

Central orchestrator for the gerivdb RLM runners.
Port: **8800**

## Endpoints

- `GET /health`
- `GET /metrics`
- `GET /vote`
- `GET /runners`
- `GET /runners/<name>/status`
- `POST /runners/<name>/start`
- `POST /runners/<name>/stop`

## Stack

- Python 3.12
- Flask
- SQLite
