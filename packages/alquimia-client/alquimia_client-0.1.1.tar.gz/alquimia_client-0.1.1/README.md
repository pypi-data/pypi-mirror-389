# 🧪 Alquimia Python Client

`AlquimiaClient` is an asynchronous HTTP client for interacting with the **Alquimia Runtime API**, providing convenient methods for inferences, streaming responses, and uploading/downloading binary data (blobs), and extending tool capabilities on client side.
It uses **httpx** for async HTTP operations and **SSE (Server-Sent Events)** for event streaming.

---

## 🚀 Installation

```bash
# Create virtual environment and install dependencies
make venv

# Build the package
make build

# Format code with ruff
make format
```

---

## 🧠 Quick Start

```python
import asyncio
from alquimia_client import AlquimiaClient

API_URL = "https://api.alquimia.ai"
API_KEY = "your_api_key_here"


async def main():
    async with AlquimiaClient(base_url=API_URL, api_key=API_KEY) as client:
        # Run an inference
        result = await client.infer(
            assistant_id="assistant-123",
            session_id="session-xyz",
            query="Summarize this text",
        )
        print(result)

        # Stream live responses
        async for event in client.stream(stream_id="stream-123"):
            print("Received:", event)

asyncio.run(main())
```

---
