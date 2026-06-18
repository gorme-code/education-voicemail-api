"""FastAPI entry point for the Education Voicemail Python API."""
from __future__ import annotations

from fastapi import FastAPI

from app.routers import cases, voicemail

app = FastAPI(
    title="Education Voicemail API",
    description=(
        "Creates Salesforce Cases from parsed voicemail data and attaches the .wav recording "
        "(MuleSoft -> Python -> Salesforce)."
    ),
    version="0.1.0",
)

app.include_router(voicemail.router)
app.include_router(cases.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}
