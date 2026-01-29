param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8000
)

python -m uvicorn app.api.main:app --reload --host $Host --port $Port
