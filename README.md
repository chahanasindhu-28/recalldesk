# RecallDesk

RecallDesk is a customer support application with a chat dashboard, long-term memory, and voice-ready architecture. The current working stage includes the chat dashboard, a customer memory model, and a verified local demo memory flow. This is a safe foundation before connecting the real Groq, Hindsight, and Twilio services.

## Architecture

```text
Browser / User
   |
   v
Streamlit Dashboard (app.py)
   |
   +--> Chat flow / customer ID validation
   +--> Memory panel
   +--> Local demo memory store for safe testing
   |
   v
Backend services
   |
   +--> LLM layer (Groq-ready, with fallback logic)
   +--> Memory layer (customer-specific retrieval + retention)
   +--> Voice API placeholder for Twilio integration
```

## Current stage status

Completed:
- Project scaffold and virtual environment setup
- Streamlit dashboard for chat
- Customer ID validation and memory isolation
- Demo memory retention and recall
- Test suite covering chat and memory behavior
- Runtime check confirming the dashboard starts locally

Not yet connected live:
- Groq API credentials and real LLM replies
- Hindsight Cloud live memory bank
- Twilio Programmable Voice + ConversationRelay

## Installation

1. Open PowerShell in the project folder.
2. Create the environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
3. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
4. Copy the example env file:
   ```powershell
   Copy-Item .env.example .env
   ```
5. Edit `.env` and add your keys only when you are ready for the external services.

## Run the app

```powershell
.\.venv\Scripts\streamlit run app.py --server.headless true --server.port 8501
```

Open the local URL shown in the terminal.

## Testing

```powershell
.\.venv\Scripts\python -m pytest -q
```

## Security notes

- Keep all secrets in `.env` and never commit them.
- Do not expose customer memory across customer IDs.
- Validate customer IDs before querying or storing memories.
- Do not print API keys to logs.

## Next services to connect

### Groq
- Add `GROQ_API_KEY` and `GROQ_MODEL` to `.env`.
- Use a supported current model from the official Groq docs.
- Confirm the model is available before deploying.

### Hindsight Cloud
- Add `HINDSIGHT_API_KEY`, `HINDSIGHT_BASE_URL`, and `HINDSIGHT_BANK_ID`.
- Keep a safe customer-to-bank mapping.
- Use a real memory bank only after the demo flow is validated.

### Twilio
- Add `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN`, and `TWILIO_PHONE_NUMBER`.
- Deploy the backend to a public HTTPS endpoint.
- Set the Twilio incoming call webhook to the deployed FastAPI route.
- Add ConversationRelay only after Twilio access is enabled and verified.

## Known limitations

- This local version uses a demo memory store when no Hindsight credentials are present.
- It does not make live payments or real external calls unless credentials are configured.
- Real voice calling requires Twilio account access, billing, and a public deployment.

## Recommended next stage

1. Add Groq live integration and verify a real response.
2. Connect Hindsight with live RETAIN and RECALL on a real bank.
3. Add Twilio voice webhook and ConversationRelay.
4. Validate cross-channel memory flow from phone to chat and chat to phone.

## Important

This is not a fake claim that the live integrations are active. The code is arranged so the real services can be connected safely once credentials and deployment are ready.
