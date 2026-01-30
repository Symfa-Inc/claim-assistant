<div align="center">

<img src=".assets/logo.png" width="100" alt="Claim Assistant Logo">

# Claim Assistant

[![Python 3.13](https://img.shields.io/badge/Python-3.13-blue.svg)](https://www.python.org/downloads/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.7-3178c6.svg)](https://www.typescriptlang.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.128-009688.svg)](https://fastapi.tiangolo.com/)
[![Next.js](https://img.shields.io/badge/Next.js-16-black.svg)](https://nextjs.org/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--5-10a37f.svg)](https://openai.com/)
[![Azure Doc Intelligence](https://img.shields.io/badge/Azure-Doc%20Intelligence-0078D4.svg)](https://azure.microsoft.com/en-us/products/ai-services/ai-document-intelligence)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://www.docker.com/)

**AI-powered automation tool that streamlines insurance claim handling by replacing repetitive adjuster tasks with intelligent LLM-based assistants.**

🔗 **Live Demo**: [claim-assistant-demo.d11.symfa.com](https://claim-assistant-demo.d11.symfa.com/)

</div>


## Overview

Claim Assistant automates claim processing for insurance companies through a modular pipeline architecture. The service converts filled insurance claim forms (PDFs) into structured data, matches claims against policy records, and produces analytical outputs that support insurance adjusters in evaluating claims.

### Key Features

- **Automated PDF Processing** – Extract key fields from filled claim forms using LLM-based pipelines
- **Policy Matching** – Map extracted claim data against policy records for validation
- **Confidence Scoring** – Account for OCR/LLM uncertainty with built-in confidence classification
- **Coverage Analysis** – Generate structured summaries with coverage status (covered / not covered)
- **Report Generation** – Produce adjuster-facing PDF reports with analysis results

### Target Audience

Claims managers, operations teams, and analysts who need to process insurance claims efficiently without technical expertise.

### Quick Demo

<p align="center">
  <video src="https://github.com/user-attachments/assets/6138161b-4e7c-4b7a-909f-4b05a2103051" width="80%"></video>
</p>

## Tech Stack

| Category | Technologies |
|----------|-------------|
| **Backend** | Python 3.13, FastAPI |
| **Frontend** | TypeScript, Next.js, Node.js |
| **AI/ML** | OpenAI API (GPT-4), Azure Document Intelligence |
| **PDF Processing** | PyPDF, FillPDF, ReportLab |
| **Data Validation** | Pydantic |
| **Package Management** | uv (backend), pnpm (frontend) |
| **Deployment** | Docker |

## Pipeline Architecture

The claim processing pipeline consists of five modular stages:

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  1. Data Prep   │ ──▶ │  2. Key         │ ──▶ │  3. Policy      │
│  (PDF → Text)   │     │  Extraction     │     │  Mapping        │
└─────────────────┘     └─────────────────┘     └─────────────────┘
                                                        │
                                                        │
                                                        ▼
                        ┌─────────────────┐     ┌─────────────────┐
                        │  5. Report      │ ◀── │  4. Analysis    │
                        │  Generation     │     │  Generation     │
                        └─────────────────┘     └─────────────────┘
```

| Stage | Purpose |
|-------|---------|
| **Data Preparation** | Handle scanned/image-based PDFs and prepare textual input |
| **Key Extraction** | Extract form fields using LLM-based structured extraction |
| **Policy Mapping** | Retrieve relevant policy data based on extracted identifiers |
| **Analysis Generation** | Evaluate coverage status with deterministic checks + LLM reasoning |
| **Report Generation** | Create adjuster-facing PDF reports with analysis results |

## Project Structure

```
claim-assistant/
├── src/claim_assistant/    # Backend source code (FastAPI)
├── frontend/               # Next.js frontend application
├── data/                   # Sample forms, policies, and processing runs
├── notebooks/              # Jupyter notebooks for experimentation
├── metrics/                # Evaluation metrics and benchmarks
├── Dockerfile              # Container configuration
└── pyproject.toml          # Backend dependencies and metadata
```

## Getting Started

### Prerequisites

- Python 3.13+
- Node.js 18+
- [uv](https://github.com/astral-sh/uv) package manager (backend)
- [pnpm](https://pnpm.io/) package manager (frontend)
- OpenAI API key
- Azure Document Intelligence credentials

### Installation

```bash
# Clone the repository
git clone https://github.com/Symfa-Inc/claim-assistant.git
cd claim-assistant

# Install backend dependencies
uv sync

# Install frontend dependencies
cd frontend
pnpm install
```

### Configuration

Provide your OpenAI API key using one of the following methods:

**Option 1: Environment Variable**
```bash
export OPENAI_API_KEY="your_api_key_here"
```

**Option 2: .env File** (recommended for local development)

Create `src/claim_assistant/.env` with:
```
OPENAI_API_KEY=your_api_key_here
```

### Running Locally

**Backend:**
```bash
uvicorn claim_assistant.web.main:app --port 8000 --reload
```

**Frontend:**
```bash
cd frontend
pnpm run dev
```

The backend API will be available at `http://localhost:8000` and the frontend at `http://localhost:3000`.

## Processing Demo Files

The repository includes sample claim forms for testing in the `data/` directory:

1. Launch the application
2. Select a prepared sample from the dropdown (grouped by state)
3. Click **Process Form** to start claim processing
4. Review the generated coverage analysis report

All processing artifacts are saved to `data/runs/` with timestamped folders containing:
- Input PDF
- Generated claim summary PDF
- Intermediate logs for debugging

## Demo

### 1. Select a Prepared Sample

The application displays available example claim forms grouped by state. Each example represents a pre-filled claim tied to a mock policy. Forms can be either **Digital** (typed fonts) or **Handwritten**.

![Select prepared sample](.assets/01_select_sample.png)

### 2. Upload a Custom Claim Form

Alternatively, upload your own filled PDF claim form and select the corresponding form type.

![Upload new sample](.assets/02_upload_sample.png)

### 3. Review Processing Results

Once processing is complete, view the original claim form alongside the generated claim summary report.

![Result view](.assets/03_results_view.png)

## License

This project is licensed under the Apache License 2.0 – see the [LICENSE](LICENSE) file for details.
