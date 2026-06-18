# Education Voicemail — Python API

FastAPI service that creates Salesforce Cases from parsed voicemail data and attaches the
`.wav` recording. Part of the Education Voicemail integration (MuleSoft → **Python API** → Salesforce).

- **Phase 1 (Salesforce data model):** complete — see `../Voicemail/PHASE2_HANDOFF.md`.
- **This project (Phase 2):** in progress. Built per the as-built Build Guide, Steps 8–9.

## Requirements
- Python 3.11

## Setup
```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then fill in real values (never commit .env)
```

## Run locally
```bash
uvicorn app.main:app --reload
```
- Health check: `GET http://127.0.0.1:8000/health`
- Interactive docs: `http://127.0.0.1:8000/docs`

## Test
```bash
pytest
```

## Project structure
```
app/
  main.py                 FastAPI entry point
  routers/
    voicemail.py          POST /api/voicemail, POST /api/voicemail/{case_id}/attachment
    cases.py              GET /api/cases, GET /api/cases/{id}
  services/
    salesforce.py         Settings + Salesforce connection (client credentials)
    auth.py               X-API-Key validation dependency
  models/
    voicemail_models.py   Pydantic request/response models
    case_models.py        Pydantic request/response models
tests/
  test_voicemail.py
  test_cases.py
  conftest.py
.env.example              placeholders only — copy to .env
```

## Build status (per Steps 8–9)
- [x] 8.1 Project scaffold
- [ ] 8.2 Dependencies installed
- [ ] 8.3 `.env` populated
- [ ] 8.4 Salesforce connection service
- [ ] 8.5 API key auth middleware
- [ ] 9.1 POST /api/voicemail
- [ ] 9.2 POST /api/voicemail/{case_id}/attachment
- [ ] 9.3 GET /api/cases
- [ ] 9.4 GET /api/cases/{id}

> Endpoint bodies in the routers are **Step 9 stubs** (`501 Not Implemented`). The auth
> dependency, settings, and Salesforce connection skeleton are wired so the app runs and the
> auth smoke tests pass today.

## Secrets
`SF_CLIENT_SECRET`, `API_KEY`, and the Connected App consumer secret live only in `.env`
(gitignored) or Azure app settings — **never** in source control.
