# Contributing to BiasX-Ray

Thank you for your interest in contributing to BiasX-Ray! This document provides guidelines and best practices for developing on this project.

## Getting Started

### Prerequisites
- Python 3.9+
- Node.js 18+
- Docker (optional, for containerized development)

### Backend Setup

```bash
cd backend
python -m venv .venv

# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate

pip install -r requirements.txt
```

Create `.env` from `.env.example`:
```bash
cp .env.example .env
# Fill in your API keys and configuration
```

Run the backend:
```bash
uvicorn app.main:app --reload
```

### Frontend Setup

```bash
cd frontend
npm install
npm run dev
```

The app will be available at `http://localhost:3000`.

## Development Guidelines

### Code Style

**Python (Backend)**
- Follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) style guide
- Use type hints for function signatures
- Include docstrings for functions and classes
- Use logging instead of print statements

**TypeScript (Frontend)**
- Use strict mode (`tsconfig.json`)
- Write components as function components with hooks
- Use proper TypeScript types (avoid `any`)
- Follow React best practices

### Logging

Use the logging module in Python:
```python
import logging
logger = logging.getLogger(__name__)
logger.info("User message")
logger.error("Error occurred", exc_info=True)
```

### Error Handling

- Always handle HTTPExceptions properly in routes
- Return meaningful error messages to the frontend
- Log exceptions with full context
- Provide user-friendly error messages

### Testing

Before submitting a PR:
1. Test your changes locally
2. Verify API endpoints work with your changes
3. Check frontend components render correctly
4. Test error scenarios and edge cases

## Project Structure

```
backend/
  app/
    routes/          # API endpoints
    services/        # Business logic
    schemas/         # Request/response models
    core/            # Configuration
ml-engine/           # Fairness computation logic
frontend/
  src/
    app/             # Next.js pages and layouts
    components/      # Reusable components
    lib/             # Utilities and API calls
```

## Common Tasks

### Adding a New API Endpoint

1. Create schema in `backend/app/schemas/`
2. Create service in `backend/app/services/`
3. Create route in `backend/app/routes/`
4. Include router in `backend/app/main.py`
5. Add types in `frontend/src/lib/types.ts`
6. Update frontend API client in `frontend/src/lib/api.ts`

### Debugging

**Backend:**
```bash
# Enable debug logging
LOG_LEVEL=DEBUG uvicorn app.main:app --reload

# Use Python debugger
import pdb; pdb.set_trace()
```

**Frontend:**
- Use browser DevTools
- Add `console.log()` statements
- Check network requests in Network tab

## Performance Considerations

- Large files (>50MB) should be rejected or chunked
- Cache bias scan results in localStorage
- Limit displayed groups to 8 for better performance
- Use React useMemo for expensive computations

## Security

- Never log sensitive data (API keys, passwords)
- Validate all user inputs
- Use environment variables for configuration
- Don't expose internal error details to users

## Submitting Changes

1. Create a new branch for your feature/fix
2. Make your changes with clear commit messages
3. Test thoroughly locally
4. Create a pull request with description

## Questions?

Feel free to open an issue or contact the maintainers!
