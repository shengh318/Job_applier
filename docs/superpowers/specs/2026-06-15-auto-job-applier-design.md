# Auto Job Applier — Design Specification

## Overview

A semi-automated job application tool that searches Indeed, navigates to applications, fills forms on Indeed and external ATS platforms (Workday, Greenhouse, Lever, etc.), creates accounts when needed, and notifies the user. The user's involvement is limited to: logging into Indeed once, reviewing applied jobs, and occasionally answering questions the AI cannot determine.

## Tech Stack

- **Language:** Python
- **Browser:** Camoufox (anti-detect Firefox) via REST API (localhost:3000)
- **AI/LLM:** Configurable — Ollama (local, free), OpenAI, Anthropic, or any OpenAI-compatible API
- **Storage:** SQLite for accounts, JSONL for application logs
- **Notifications:** Desktop notifications (built-in)

## Architecture

```
┌───────────────────────────────────────────────────┐
│                User's Machine                      │
│                                                    │
│  ┌──────────────┐     ┌────────────────────────┐  │
│  │  Camoufox    │◄───►│  Python App            │  │
│  │  Browser     │     │                        │  │
│  │  :3000       │     │  ┌──────────────────┐  │  │
│  └──────────────┘     │  │ Job Search Engine │  │  │
│                       │  │ (Indeed + config) │  │  │
│                       │  └────────┬─────────┘  │  │
│                       │           │            │  │
│                       │  ┌────────▼─────────┐  │  │
│                       │  │ Application      │  │  │
│                       │  │ Engine (AI-first)│  │  │
│                       │  └────────┬─────────┘  │  │
│                       │           │            │  │
│                       │  ┌────────▼─────────┐  │  │
│                       │  │ Account Manager  │  │  │
│                       │  │ (creates logins, │  │  │
│                       │  │  stores creds)   │  │  │
│                       │  └────────┬─────────┘  │  │
│                       │           │            │  │
│                       │  ┌────────▼─────────┐  │  │
│                       │  │ Notification     │  │  │
│                       │  │ System           │  │  │
│                       │  └──────────────────┘  │  │
│                       └────────────────────────┘  │
│                                                    │
│  ┌──────────┐  ┌───────────┐  ┌────────────────┐  │
│  │ Profile  │  │ Resume    │  │ Accounts DB    │  │
│  │ .yaml    │  │ .pdf      │  │ (SQLite)       │  │
│  └──────────┘  └───────────┘  └────────────────┘  │
└───────────────────────────────────────────────────┘
```

## Components

### 1. Job Search Engine

Navigates Indeed based on config criteria. Scrapes job listings and returns structured data to the Application Engine.

**Config (search.yaml):**
```yaml
search:
  title: "Software Engineer"
  location: "San Francisco"
  remote_only: true
```

**Behavior:**
- Navigates to Indeed, enters search query + location + filters
- Extracts: title, company, location, salary, apply link, description
- LLM relevance scoring (optional): scores each job 0-100 against your profile
- Applies to ALL jobs, highest score first
- No hard filters — salary, job type, remote are soft preferences used for scoring only
- Exclude list is the only hard skip rule

**Anti-detection:**
- Random delays between pages (2-5s)
- Camoufox handles fingerprint spoofing
- Natural browsing behavior simulation

### 2. Application Engine (AI-First)

The core system. Uses an LLM to read page snapshots and fill forms.

**Flow for each job:**
```
1. Click into job listing
2. Click "Apply Now"
3. Take accessibility snapshot of current page
4. Send snapshot + profile + job description to LLM
5. LLM returns: { field_name: value } mapping + click action
6. Fill fields using Camoufox
7. If page changes (redirect/next page) → repeat from step 3
8. If account creation required → Account Manager handles it
9. If submit reached → log success
10. If stuck → prompt user (last resort)
```

**LLM Prompt Strategy:**
- Input: page accessibility snapshot (structured text, not HTML), profile YAML, resume text, job description
- Output: JSON with fields to fill, button to click, and status
- Example response:
```json
{
  "fields": [
    {"selector": "textbox 'First Name'", "value": "Your Name"},
    {"selector": "textbox 'Email'", "value": "your@email.com"},
    {"selector": "dropdown 'Experience'", "value": "5 years"},
    {"selector": "upload 'Resume'", "action": "upload_file", "path": "/path/to/resume.pdf"}
  ],
  "click": "button 'Next'",
  "status": "continue"
}
```

**Multi-page handling:**
- After each "Next" or "Continue" click, take fresh snapshot
- Claude evaluates new page and continues filling
- Handles: Indeed → Workday page 1 → Workday page 2 → Review → Submit

**Redirect detection:**
- After clicking "Apply," check if URL changed
- If redirected (Workday, Greenhouse, etc.), continue same AI-driven fill loop
- Transition is seamless — LLM doesn't care which site it's on

### 3. Account Manager

Creates accounts on external ATS sites when required.

**Flow:**
```
Redirect detected → Check Accounts DB
  → Account exists? Use stored credentials to log in
  → No account? Continue
  → Take snapshot
  → Send to LLM: "Create account using this profile"
  → LLM returns: { email: generated, password: generated }
  → Fill signup form, create account
  → Store credentials in Accounts DB
  → Send notification
```

**Credential generation:**
- Username: your email from profile (or variation like `name+sitename@gmail.com`)
- Password: random strong password
- Stored in plain text in SQLite (local machine only)

**Accounts DB:**
- SQLite database with table: accounts (domain, email, password, created_at)
- Reuses existing accounts if applying to same company again
- User sets master password once on first run

### 4. Notification System

Desktop notifications for applied jobs and created accounts.

**Notification content:**
- Job title + company
- Whether an account was created
- Login credentials if so
- Link to the application

**Also writes to:**
- `logs/applications.jsonl` — full application log (always)

### 5. Profile & Resume

**Profile (profile.yaml):**
```yaml
name: "Your Name"
email: "your@email.com"
phone: "+1-555-123-4567"
location: "San Francisco, CA"
linkedin: "linkedin.com/in/yourname"

work_history:
  - company: "Previous Company"
    title: "Software Engineer"
    duration: "2 years"
    description: "Built X, Y, Z"

education:
  - school: "University of California"
    degree: "BS Computer Science"
    year: "2020"

skills:
  - Python
  - JavaScript
  - React

screening_answers:
  years_experience: "5"
  visa_status: "US Citizen"
  willing_to_relocate: "Yes"
  salary_expectation: "120000"
```

**Resume:**
- PDF file referenced in config
- Uploaded to ATS forms when "upload resume" field is detected
- Also parsed for text to include in LLM context

## Configuration

**config.yaml:**
```yaml
llm:
  provider: ollama          # ollama, openai, anthropic
  model: llama3             # model name
  api_url: http://localhost:11434  # for Ollama
  api_key: ""               # for paid APIs

search:
  title: "Software Engineer"
  location: "San Francisco"
  remote_only: true

profile:
  file: ./profile.yaml
  resume: ./resume.pdf

notifications:
  desktop: true
  log_file: ./logs/applications.jsonl
```

## User Involvement

1. **Each session:** Log into Indeed manually (browser window opens, you log in, tool takes over)
2. **Ongoing:** Receive desktop notifications of applied jobs and created accounts
3. **Last resort:** Answer a question the AI truly cannot determine

## Anti-Detection Strategy

- Camoufox: C++ engine-level fingerprint spoofing (not JS injection)
- Random delays between actions (2-5s)
- Natural browsing behavior simulation
- No rapid-fire requests
- Per-session cookie management

## Error Handling

- **Bot detection triggered:** Pause, notify user, suggest manual intervention
- **Account creation fails:** Log error, skip to next job, notify user
- **LLM returns invalid JSON:** Retry once, then skip job
- **Page timeout:** Wait, retry, then skip if still stuck
- **Indeed login expires:** Prompt user to re-login

## Testing Strategy

- Unit tests for LLM prompt building and response parsing
- Integration tests for Camoufox REST API communication
- End-to-end test flow with mock Indeed pages
- Manual testing against real Indeed (with user's account)

## Future Considerations

- Support for other job boards (LinkedIn, Glassdoor)
- Application tracking dashboard
- Resume tailoring per job description
- Cover letter generation
- Interview scheduling integration
