<div align="center">

<img src=".assets/logo.png" width="100" alt="Claim Assistant Logo">

# Claim Assistant

AI-powered automation tool that streamlines insurance claim handling with LLM-based PDF processing, policy matching, and coverage analysis.

**[Live Demo](https://claim-assistant.symfa.ai/)** · **[GitHub](https://github.com/Symfa-Inc/claim-assistant)** · **[Confluence](https://symfa.atlassian.net/wiki/spaces/SYMFA/pages/5012094982)**

</div>

## Preview

<div align="center">
<img src=".assets/claim-assistant.png" width="800" alt="Claim Assistant Preview">
</div>

## Tech Stack

| Category | Technologies |
|----------|-------------|
| Backend | Python 3.13, FastAPI, Uvicorn |
| Frontend | TypeScript, Next.js, React, Tailwind CSS |
| AI/ML | OpenAI, Azure Document Intelligence |
| PDF | PyPDF2, FillPDF, ReportLab |
| Data | Pydantic, pandas |
| Package Management | uv (backend), pnpm (frontend) |
| Deployment | Docker, GitHub Actions, Google Artifact Registry |

## Getting Started

### Prerequisites

- Python 3.13+ / [uv](https://docs.astral.sh/uv/)
- Node.js 24+ / [pnpm](https://pnpm.io/)

### Installation & Running

```bash
# Backend
cd backend
cp .env.example src/claim_assistant/.env    # Add your API keys
uv sync
uv run uvicorn claim_assistant.web.main:app --reload

# Frontend (in a separate terminal)
cd frontend
pnpm install
pnpm dev
```

Open [http://localhost:3000](http://localhost:3000) (frontend) and [http://localhost:8000/docs](http://localhost:8000/docs) (API docs).

## License

[MIT](LICENSE)
