$env:PYTHONPATH = "src"
$env:INNGEST_DEV = "1"
.\.venv\Scripts\python.exe -m uvicorn research_copilot_server.main:app --reload --port 8000


docker run --rm -p 8288:8288 inngest/inngest inngest dev -u http://host.docker.internal:8000/api/inngest --no-discovery
