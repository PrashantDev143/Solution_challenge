# BiasX-Ray API Documentation

All endpoints are available at `http://localhost:8000` (or your deployed backend URL).

## Endpoints

### Upload Dataset

**POST** `/upload`

Upload a CSV file for bias analysis.

**Request:**
- Content-Type: `multipart/form-data`
- Body: CSV file

**Response:**
```json
{
  "temp_path": "backend/tmp/uploads/abc123_data.csv",
  "columns": ["age", "gender", "income", "approved"],
  "target_column": "approved",
  "row_count": 5000,
  "preview_rows": [
    {"age": "25", "gender": "M", "income": "50000", "approved": "1"}
  ]
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid CSV or file validation failed
- `413`: File exceeds 50MB limit
- `500`: Server error

---

### Run Bias Scan

**POST** `/scan`

Run a comprehensive bias scan on a dataset.

**Request:**
```json
{
  "dataset_path": "backend/tmp/uploads/abc123_data.csv",  // Optional
  "target_column": "approved"  // Optional
}
```

**Response:**
```json
{
  "dataset_path": "backend/tmp/uploads/abc123_data.csv",
  "total_rows": 5000,
  "groups_scanned": 24,
  "biased_groups_found": 5,
  "fairness_score": 78.5,
  "target_column": "approved",
  "top_biased_groups": [
    {
      "group": "gender=F + age_bucket=40-50",
      "count": 250,
      "approval_rate": 0.72,
      "baseline_rate": 0.85,
      "difference": -0.13,
      "disparate_impact": 0.85,
      "severity": "high",
      "ranking_reason": "Underprivileged group with large gap"
    }
  ]
}
```

**Status Codes:**
- `200`: Success
- `400`: Invalid dataset or target column
- `404`: Dataset not found
- `500`: Scan error

---

### Get Simulation Schema

**GET** `/simulate/schema`

Get available fields and options for what-if simulation.

**Query Parameters:**
- `dataset_path` (optional): Path to CSV file
- `target_column` (optional): Target column name

**Response:**
```json
{
  "dataset_path": "backend/tmp/uploads/abc123_data.csv",
  "target_column": "approved",
  "fields": [
    {
      "name": "age",
      "label": "Age",
      "type": "numeric"
    },
    {
      "name": "gender",
      "label": "Gender",
      "type": "categorical",
      "options": ["M", "F"]
    }
  ]
}
```

---

### Run Simulation

**POST** `/simulate`

Compare predictions for baseline vs scenario feature values.

**Request:**
```json
{
  "dataset_path": "backend/tmp/uploads/abc123_data.csv",
  "target_column": "approved",
  "baseline_features": {
    "age": 30,
    "gender": "F",
    "income": 50000
  },
  "scenario_features": {
    "age": 30,
    "gender": "M",
    "income": 50000
  }
}
```

**Response:**
```json
{
  "baseline": {
    "prediction": 1,
    "probability": 0.78
  },
  "scenario": {
    "prediction": 1,
    "probability": 0.85
  },
  "changed": false,
  "message": "Scenario shows higher approval probability (+0.07)"
}
```

---

### Generate Explanation

**POST** `/explain`

Get AI-powered explanation for a biased group using Gemini API.

**Request:**
```json
{
  "group": "Gender = Female + Age Bucket = 40-50",
  "count": 250,
  "approval_rate": 0.72,
  "baseline_rate": 0.85,
  "difference": -0.13,
  "severity": "high",
  "ranking_reason": "Underprivileged group with large gap"
}
```

**Response:**
```json
{
  "explanation": "This group shows significant bias. Women aged 40-50 have a 13% lower approval rate compared to the baseline...",
  "recommendations": [
    "Review underwriting criteria for age bias",
    "Increase oversight of approvals in this demographic",
    "Consider separate models for different age groups"
  ]
}
```

**Note:** If Gemini API is unavailable, returns a sensible local explanation.

---

### Get Latest Report

**GET** `/report`

Download the latest bias scan report as JSON.

**Response:**
- Returns the full scan report from the latest scan
- Content-Disposition header set for download as `biasxray-report.json`

---

### Health Check

**GET** `/health`

Check if the API is running.

**Response:**
```json
{
  "status": "ok",
  "app": "BiasX-Ray"
}
```

---

## Error Response Format

All errors follow this format:

```json
{
  "detail": "Human-readable error message"
}
```

Common error messages:
- `Invalid file type. Only .csv files are supported.`
- `File size exceeds 50MB limit.`
- `Could not parse CSV file.`
- `Dataset is empty.`
- `No scan report available. Please run a scan first.`

---

## Workflow Example

1. **Upload Dataset**
   ```
   POST /upload → Get temp_path and target_column
   ```

2. **Run Scan**
   ```
   POST /scan with temp_path → Get top_biased_groups
   ```

3. **Get Simulation Schema**
   ```
   GET /simulate/schema → Get available fields
   ```

4. **Run Simulation** (optional)
   ```
   POST /simulate → Compare baseline vs scenario
   ```

5. **Generate Explanation**
   ```
   POST /explain for a specific group → Get AI explanation
   ```

6. **Download Report**
   ```
   GET /report → Download JSON report
   ```

---

## Rate Limiting & Timeouts

- File uploads: 5 minute timeout
- Bias scans: 10 minute timeout
- Explanation generation: 2 minute timeout
- No rate limiting currently implemented

---

## Authentication

Currently, all endpoints are public. Authentication can be added by:
1. Adding API key validation middleware
2. Using JWT tokens
3. Implementing OAuth2 integration

---

## Data Retention

- Uploaded files are kept in `backend/tmp/uploads/`
- Reports are cached in memory and localStorage
- Files should be cleaned up periodically (>7 days old)

---

For more information, see:
- [README.md](./README.md) - Project overview
- [CONTRIBUTING.md](./CONTRIBUTING.md) - Development guidelines
- [frontend/AGENTS.md](./frontend/AGENTS.md) - AI agent architecture
