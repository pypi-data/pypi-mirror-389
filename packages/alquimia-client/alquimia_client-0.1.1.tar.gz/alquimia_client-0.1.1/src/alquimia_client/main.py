import json
from typing import Any, AsyncGenerator, Dict, List, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel, Field

DEFAULT_AGENTSPACE = "_default"
API_VERSION = "v1"


class Blob(BaseModel):
    """
    Files related to a session context
    """

    filename: str
    content_type: str
    content_size: int
    checksum: Optional[str] = None
    uuid: Optional[str] = None
    data_base64: Optional[str] = None


class SessionContextMetadata(BaseModel):
    """
    Alquimia session context metadata.
    """

    session_id: str
    assistant_id: str
    agentspace_id: str


class SessionContext(BaseModel):
    """
    Alquimia session context.
    """

    blobs: list[Blob] = Field(default=[])
    messages: list[dict] = Field(default=[])


class AlquimiaClient:
    """
    Alquimia HTTP client with streaming support via httpx.
    """

    def __init__(
        self,
        base_url: str,
        api_key: str | None = None,
        event_stream_timeout: int | None = 300,
        request_timeout: int | None = 60,
        api_version: str = API_VERSION,
    ):
        self.base_url = urljoin(base_url, api_version)
        self.api_key = api_key
        self.event_stream_timeout = event_stream_timeout
        self.request_timeout = request_timeout
        self.client = None

    async def __aenter__(self):
        self.client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={"Authorization": f"Bearer {self.api_key}"},
            timeout=self.request_timeout,
        )
        return self

    async def __aexit__(self, exc_type, exc, tb):
        if self.client:
            await self.client.aclose()

    async def stream(
        self, stream_id: str, response_only: bool = True
    ) -> AsyncGenerator[dict, None]:
        """
        Stream events from the Alquimia API using Server-Sent Events (SSE) over httpx.
        """
        url = f"{self.base_url}/event/stream/{stream_id}"
        params = {"response_only": str(response_only).lower()}
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "text/event-stream",
        }

        async with self.client.stream(
            "GET",
            url,
            params=params,
            headers=headers,
            timeout=self.event_stream_timeout,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line or not line.startswith("data:"):
                    continue
                try:
                    data = json.loads(line[5:].strip())
                    yield data
                except json.JSONDecodeError:
                    continue

    async def tool_completion(self, stream_id: str, control_id: str, tool_output: dict):
        """
        Notify the server of a tool completion event.
        """
        response = await self.client.post(
            "/event/tool-completion",
            json={
                "stream_id": stream_id,
                "control_id": control_id,
                "result": tool_output,
            },
        )
        response.raise_for_status()
        return response.json()

    async def upload_attachment(
        self, session_id: str, stream_id: str, attachment_id: str, attachment: Blob
    ):
        response = await self.client.post(
            f"/event/attachment/{session_id}/{stream_id}/{attachment_id}",
            files={
                "file": (
                    attachment.filename,
                    attachment.data_base64,
                    attachment.content_type,
                )
            },
        )
        response.raise_for_status()
        return response.json()

    async def upload_context_blob(
        self,
        session_id: str,
        assistant_id: str,
        blob: Blob,
        agentspace=DEFAULT_AGENTSPACE,
    ) -> Blob:
        response = await self.client.post(
            f"/context/blob/upload/{assistant_id}/{session_id}",
            files={"file": (blob.filename, blob.data_base64, blob.content_type)},
            params={"agentspace": agentspace},
        )
        response.raise_for_status()
        return Blob(**response.json())

    async def download_context_blob(
        self,
        session_id: str,
        assistant_id: str,
        blob: Blob,
        keep=False,
        response_base64=True,
        agentspace=DEFAULT_AGENTSPACE,
    ) -> str:
        response = await self.client.get(
            f"/context/blob/download/{assistant_id}/{session_id}/{blob.uuid}",
            params={"agentspace": agentspace, "keep": keep, "response_base64": response_base64},
        )
        response.raise_for_status()
        return response.content

    async def session_context_retrieval(
        self,
        session_id: str,
        assistant_id: str,
        agentspace=DEFAULT_AGENTSPACE,
    ) -> SessionContext:
        response = await self.client.get(
            f"/context/retrieve/{assistant_id}/{session_id}",
            params={"agentspace_id": agentspace, "messages_only": False},
        )
        response.raise_for_status()
        body = response.json()
        return SessionContext(**body)

    async def infer(
        self,
        assistant_id: str,
        session_id: str,
        query: str,
        attachments: List[Blob] = [],
        chat_history=50,
        channel="chat",
        agentspace=DEFAULT_AGENTSPACE,
        **kwargs,
    ) -> Dict[str, Any]:
        payload = {
            "query": query,
            "session_id": session_id,
            "extra_data": kwargs,
            "attachments": [a.model_dump(exclude_none=True) for a in attachments],
        }
        response = await self.client.post(
            f"/event/infer/{channel}/{assistant_id}",
            json=payload,
            params={"chat_history": chat_history, "agentspace": agentspace},
        )
        response.raise_for_status()
        return response.json()
