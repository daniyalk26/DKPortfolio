# PawID – Dog Breed & Emotion Classifier 🐾

A full‑stack project that recognizes dog breeds and emotions from an image.  
**Backend:** FastAPI + TensorFlow.  
**Frontend:** React + Tailwind.

## Setup

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add API keys
uvicorn backend.main:app --reload
```

Front‑end:

```bash
cd frontend
npm install
npm run dev
```

## Tests

```bash
pytest
```

## Deployment

- Dockerfile included for containerised deployment.
- GitHub Actions workflow samples in `.github/workflows/`.

## License

MIT
