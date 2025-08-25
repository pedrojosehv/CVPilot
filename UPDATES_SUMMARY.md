# CVPilot Updates Summary

## ✅ Completed Tasks

### 1. Manual CSV Export Location
- **Created**: `D:\Work Work\Upwork\CVPilot\manual_exports\` folder
- **Purpose**: Temporary location for PowerBI CSV exports containing job IDs
- **Usage**: Export CSVs from PowerBI to this folder, CVPilot will automatically detect and load them

### 2. API Key Integration (DataPM Keys)
- **Updated**: `env.example` with DataPM Gemini API keys as default
- **Added**: Gemini support to CVPilot with API key rotation
- **Keys**: All 4 DataPM keys are now configured as default for CVPilot

### 3. Gemini LLM Support
- **Added**: `google-generativeai` to requirements.txt
- **Enhanced**: ContentGenerator to support Gemini with API key rotation
- **Features**: Automatic fallback to other keys when rate limited
- **Provider**: Set as default LLM provider in configuration

### 4. Manual Loader Module
- **Created**: `src/ingest/manual_loader.py` for PowerBI CSV processing
- **Features**: 
  - Flexible column name detection (job_id, id, jobid, etc.)
  - Automatic job ID generation if missing
  - Support for various CSV formats
  - Search functionality
  - Cache management

### 5. Updated Main Pipeline
- **Modified**: `src/main.py` to use manual loader first, then DataPM loader
- **Priority**: Manual exports take precedence over DataPM files
- **Fallback**: If job not found in manual exports, searches DataPM files

## 🔧 Configuration Changes

### Environment Variables (env.example)
```bash
# Primary LLM (Gemini with DataPM keys)
LLM_PROVIDER=gemini
LLM_MODEL=gemini-1.5-flash
GEMINI_API_KEYS=AIzaSyDZ8Nl4jlGt-odZOFVhBFwQnC-m35C7HZE,AIzaSyCU2RQKO9i0Cm8t6NhBCcCozVuH3lgeUfY,AIzaSyBKJViSNDfdbjAboGMzEBjhqcGMz4TeMAg,AIzaSyDNCigTvTv5ItL8ht48LbhDVVvY0inG_bg,AIzaSyBHsBZ6bnOH3DkCuc3Zyq8DanrCPjYRQdY

# Manual exports path
MANUAL_EXPORTS_PATH=manual_exports
```

### New Dependencies
- `google-generativeai>=0.3.0` - For Gemini API integration

## 📁 New File Structure
```
CVPilot/
├── manual_exports/          # ← NEW: PowerBI CSV exports
├── src/ingest/
│   ├── job_loader.py        # DataPM loader (existing)
│   └── manual_loader.py     # ← NEW: PowerBI loader
└── test_manual_loader.py    # ← NEW: Test script
```

## 🚀 Usage Instructions

### For Manual CSV Exports:
1. Export CSV from PowerBI to: `D:\Work Work\Upwork\CVPilot\manual_exports\`
2. Ensure CSV has columns like: `job_id`, `job_title`, `company`, `skills`, `software`
3. Run CVPilot with the job ID from your CSV

### Example CSV Format:
```csv
job_id,job_title,company,skills,software,seniority
JOB001,Product Manager,TechCorp,"Product Strategy, Agile, User Research","Jira, Figma, Analytics",Mid
```

### Testing:
```bash
cd "D:\Work Work\Upwork\CVPilot"
python test_manual_loader.py
```

## ⚠️ DataPM Processor Issue

The DataPM processor is hitting rate limits with all Gemini API keys. This is a separate issue from CVPilot and doesn't affect the manual CSV functionality.

**Status**: The processor ran but encountered rate limiting after processing a few records. The keys may need to be refreshed or have usage limits.

## 🎯 Next Steps

1. **Install Dependencies**: `pip install -r requirements.txt`
2. **Copy Environment**: `cp env.example .env`
3. **Test Manual Loader**: `python test_manual_loader.py`
4. **Export PowerBI CSV**: Place in `manual_exports/` folder
5. **Run CVPilot**: `python -m src.main --job-id YOUR_JOB_ID`

## 🔄 API Key Rotation

CVPilot now supports automatic API key rotation for Gemini:
- Uses all 4 DataPM keys
- Rotates automatically on rate limits
- Falls back to generic content if all keys fail
- Logs rotation events for monitoring
