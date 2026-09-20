$env:PYTHONPATH = "src"
$env:INNGEST_DEV = "1"
.\.venv\Scripts\python.exe -m uvicorn research_copilot_server.main:app --reload --port 8000
