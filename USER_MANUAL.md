# ResearchCollision User Manual

**Version** 1.0 · For the `main` branch as currently implemented.

---

## What the application does

ResearchCollision is a **research-intersection discovery** tool. It helps researchers find
non-obvious connections between research areas by combining **researcher profiles** and
**scholarly literature**. For a chosen pair of researchers (or a researcher and a research
field), it runs an automated discovery pipeline that proposes:

- **Research intersections** — areas where two researchers' work could meaningfully meet.
- **Research gaps** — under-explored questions detected by cross-referencing literature.
- **Hypotheses** — testable research questions and proposed experiment designs.
- **Collaboration candidates** — ranked suggestions of why two people might collaborate.
- **A paper draft** — an AI-written draft of a proposed research paper, grounded in the
  evidence collected during the run.

Everything the application produces is a **candidate for a human to review**, not an
established scientific finding.

> **Grounded evidence, not invention.** Every claim in the system is linked to stored
> evidence with a verification status (`VERIFIED`, `INFERRED`, `SPECULATIVE`,
> `UNVERIFIED`, or `UNKNOWN`). The system never claims a result was measured when it was
> only proposed.

## Who it is for

- **Researchers and scientists** exploring cross-disciplinary ideas.
- **Students** preparing research directions or thesis proposals.
- **Research groups** looking for novel collaborations.
- **Anyone** who wants a structured, evidence-grounded starting point for an investigation.

No programming is required to use the application. A browser is all you need.

## What problem it solves

Researchers often work in isolated communities, and the connections between their results
can remain invisible. Manually scanning all literature for potential links between two
fields is slow and easy to miss. ResearchCollision automates that first-pass screening:
it collects literature, analyzes it, and surfaces *where* two research areas might collide —
then supports the human in turning those leads into testable hypotheses and drafts.

## High-level workflow

1. **Create an account** and a **workspace** (a private container for one research effort).
2. **Upload a CV** to build a research profile (the system extracts a "Research DNA").
3. **Find researchers** to pair (search the directory, or add them manually).
4. **Run a discovery job** (a 10-step automated pipeline).
5. **Review the results**: intersections, gaps, hypotheses, collaboration candidates, and
   evidence.
6. **Generate a paper draft** from a completed job.
7. **Export** the draft (Markdown or PDF) and/or the workspace (JSON).

Individual steps are described in detail below.

---

## Prerequisites

### Required software and services

| Item | Requirement |
|---|---|
| Python | 3.10 or newer (the project is verified on Python 3.10) |
| Node.js | 20 or newer, plus npm |
| Browser | Any modern browser (Chrome, Edge, Firefox, or Safari) |
| Internet | Needed the first time you install packages and any time real literature/LLM providers are used |

### Backend / frontend requirements

- **Backend**: a FastAPI application. It uses a single local SQLite database file (no
  separate database server is needed). By default it runs with **mock providers**, which
  work offline for exploring the interface.
- **Frontend**: a React application served by Vite (its own local web server).
- **Environment configuration**: copy `.env.example` to `.env` in the `backend/` folder if
  you want to configure providers (see [Provider/Model Status](#provider-model-status)).
  The application works out of the box without one.

### How to verify the application is running

- Open the web UI at **http://localhost:5173** — you should see the sign-in page.
- Backend health check: **http://localhost:8000/health** — the page should show JSON that
  begins with `{"status":"ok"`.
- Interactive API documentation: **http://localhost:8000/docs**.

---

## Starting the Application

Open a terminal in the project folder (`ResearchCollision`) and follow these steps.

### 1. Install the backend

```powershell
cd backend
python -m venv .venv
.venv\Scripts\activate
python -m pip install -r requirements.txt -r requirements-dev.txt
```

*On macOS/Linux, activate with `source .venv/bin/activate` and you can combine both
requirement files as shown above.*

### 2. Start the backend

```powershell
.venv\Scripts\activate        # if not already active
python -m uvicorn app.main:app --reload --port 8000
```

(Equivalently, run `make backend` or `make dev` from the project root.)

**Successful startup looks like:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [...]
INFO:     Application startup complete.
```

### 3. Install and start the frontend

In a **second terminal**:

```powershell
cd frontend
npm install
npm run dev
```

(Equivalently, run `make frontend` from the project root.)

**Successful startup looks like:**
```
VITE v5.x.x  ready in 2.x s

  Local:   http://localhost:5173/
```

### 4. Open the application

- **Web UI:** http://localhost:5173
- **API docs:** http://localhost:8000/docs (read-only reference of all backend endpoints)
- **Health check:** http://localhost:8000/health

### Optional: demo data

```powershell
cd backend
python ../scripts/seed.py      # or: make seed
```

This creates demo credentials you can use to explore the app quickly:
- Email: `demo@researchcollision.dev`
- Password: `demo1234`

Demo data is **clearly synthetic** (fictional researchers and papers) and is for local
exploration only.

---

## Getting Started

### Registration

1. Open http://localhost:5173 and click **Register**.
2. Fill in:
   - **Name** — your display name (required).
   - **Email** — your email address (required). It is stored in lowercase.
   - **Password** — at least **8 characters** (required).
3. Click **Create account**.

You are signed in immediately after registering — there is no separate "log in after
registration" step. If you register with an email that already has an account, you will see:
`An account with this email already exists`.

### Login

1. Click **Sign in** at the top of the page.
2. Enter your **Email** and **Password**.
3. Click **Sign in** (the button changes to **Signing in…** while it works).

You can click **Use demo credentials** to fill in the demo account details automatically
(you still press **Sign in**). Wrong credentials show `Invalid email or password`.

> A signed-in session expires after 12 hours. When a session expires, the application
> returns you to the sign-in page.

### Creating or selecting a workspace

A **workspace** is a private container that holds everything for one research effort:
profiles, researchers, jobs, and results. Each workspace belongs to you.

- **First time:** after login you will see the **Dashboard** with the message
  *"No workspace yet"*. Enter a name in the **Workspace name** field (for example
  `Climate × Health intersections`) and click **Create workspace**.
- **Later:** use the **workspace selector** in the top-right of the header (labeled
  "Active workspace") to switch between your workspaces.
- You can also create a workspace from **Settings → Workspaces** (see
  [Workspace Management](#workspace-management)).

**The only required field for a workspace is a name.** A description is optional and can
only be set when creating a workspace from **Settings**.

### Initial configuration

Once you have a workspace, you can optionally tune the **collaboration score weights**
from **Settings → Collaboration score weights** before you run discovery. These weights
decide how strongly each factor (research relevance, method complementarity, trajectory
alignment, gap relevance, evidence strength, feasibility) contributes to collaboration
rankings. See [Workspace Management](#workspace-management).

---

## Research Profile

The Research Profile page (sidebar → **Research Profile**) builds a **"Research DNA"**
from your CV: a structured summary of your domains, problems, methods, and interests.
The application uses this understanding internally when analyzing literature.

### Uploading a CV

1. On the **Research Profile** page, click **Upload CV**.
2. Choose a file. Supported formats: **.pdf, .docx, .txt**.
3. The button changes to **Extracting DNA…** — the system extracts your research profile
   in the background and then selects the new profile automatically.

The upload page explains: *"Upload CV (.pdf, .docx, .txt) — parsed locally, never
executed."* Files larger than 10 MB, empty files, or files whose content can't be read
are rejected.

### What the system extracts

The extracted **Research DNA** can include all of these fields, shown as tags on the
profile detail:

| Field | Example content |
|---|---|
| Domains | machine learning, epidemiology |
| Research Problems | early cancer detection |
| Methods | neural networks, ANOVA |
| Datasets | TCGA, imagenet |
| Tools | Python, R, pandas |
| Research Questions | "How do shifts affect outcomes?" |
| Publications | list of your cited works |
| Technical Skills | statistics, deep learning |
| Research Interests | precision medicine |
| Emerging Interests | federated learning |
| Experience | positions, roles |

If none could be extracted, the page shows *"No DNA fields extracted."*

### Reviewing the profile

- The profile list (left column) shows each profile's **name** and **source** (`cv` or
  `manual`), for example `Precision oncology — Your Name`.
- Click a profile to view its Research DNA (right column).
- A **Version history** panel lists each saved version with its date and time. This is
  **read-only** in the interface.

### Deleting an uploaded CV

Use the **Delete uploaded CV (privacy)** button to remove the CV document and its
extracted text from the workspace. **There is no confirmation prompt** — clicking the
button deletes immediately.

> **Note:** In the current interface, profiles can only be created by uploading a CV.
> There is no form for typing a profile by hand, and the DNA fields cannot be edited in
> the UI (an edit endpoint exists in the backend but is not exposed). An uploaded CV
> profile is **not** automatically linked to the researcher directory, so it will not
> appear when you search researchers.

---

## Researcher Discovery

The **Researchers** page (sidebar → **Researchers**) helps you find people to pair in a
discovery run.

### How researcher search works

1. Type into the search box (placeholder: `Search researchers…`) and click **Search**.
2. The system matches your words against researcher **names, affiliations, and aliases**
   (case-insensitive, partial match). Every workspace's own researchers **and** a
   shared/global set of researchers are searched.
3. Results are shown as cards with the researcher's **name**, a **synthetic** badge when
   the researcher is a demo/placeholder entry, their **affiliation**, and a short **bio**.

If nothing matches, you'll see: `No researchers found for "your query"`.

### Adding a researcher manually

Use the **Add researcher** panel on the right:

- **Name** — required.
- **Affiliation** — optional.

Click **Add researcher**. If a researcher with the same name already exists, the existing
record is reused rather than duplicated.

### How researchers relate to the workspace

- Researchers you add are stored in your workspace.
- Researchers from the shared/global directory are visible in every workspace.
- Results from a discovery run (intersections, collaborations) reference the researcher
  pair you chose.

There is **no** researcher detail page, and researchers cannot be edited or deleted from
the UI.

---

## Paper Discovery

The **Literature** page (sidebar → **Literature**) lets you search academic literature
across several providers with automatic fallback.

### Searching

1. Type a query (for example `low-resource machine translation`) and click **Search**.
2. The system queries literature providers in order — **OpenAlex → Semantic Scholar →
   Crossref → arXiv** — and falls back to the next one if a provider fails.

Each result card shows:

- **Title**, a **synthetic** badge (only for demo/placeholder papers), and the **provider**
  that returned it.
- The **abstract** (clipped to two lines).
- A metadata line: `venue · publication year · N citations`, plus `DOI` when present.

### Local papers vs discovered papers

While searching, the system **stores every result in your workspace's paper store
behind the scenes**. However, the current interface does **not** provide a "local papers"
browser — you always see the fresh search results. There is no "add to library" button.

> **Backend note:** a local-papers endpoint
> (`GET /api/v1/papers/local`) and a single-paper endpoint
> (`GET /api/v1/papers/{paper_id}`) exist in the API, but the web interface never calls
> them.

---

## Discovery Jobs

A **discovery job** is the core automated run. Sidebar → **Discovery**.

### How discovery jobs work

The page explains: *"Run the 10-step pipeline: literature → analysis → trajectories →
gaps → intersections → evidence verification → hypotheses → paper draft → ranking."*

A job takes a researcher pair, searches their literature, analyzes it, detects gaps,
finds intersections, verifies evidence, generates hypotheses, writes a paper draft, and
ranks collaboration opportunities — in that order.

### Starting a discovery job

In the **New discovery run** form:

| Control | Description |
|---|---|
| **Researcher A** | Required. Start typing to search; pick from the dropdown (shows name + affiliation). |
| **Researcher B (optional — auto-pair if empty)** | A second researcher. If left empty, you must provide a **Field query**. |
| **Field query (virtual researcher)** | A research field used instead of a second person (for example `climate science`). It is disabled automatically as soon as you pick a Researcher B. |
| **Discovery mode** | `Normal` or `Serendipity`. `Normal` is the default. |
| **Max papers per researcher** | A slider from 1 to 50 (default **12**) — how many papers to retrieve per researcher. |
| **Generate hypotheses** | Checkbox, on by default. Turn it off to skip hypothesis generation. |

Click **Start discovery** (**Starting…** while it submits). The form requires Researcher A,
and either a Researcher B or a Field query — otherwise you'll see messages such as
`Select researcher A first.` or `Pick researcher B or enter a field query.`

Each job runs in the background. You can leave the page and come back.

### Job status and progress

Each job card shows:

- A **status badge**: `PENDING`, `RUNNING`, `PAUSED`, `COMPLETED`, `FAILED`, or
  `CANCELLED` (the `RUNNING` badge pulses).
- **Attempt** number and the date/time it was created.
- A **progress bar** with a percentage.
- The **current step** while running (e.g. *Resolving inputs…*, *Searching literature…*,
  *Analyzing papers…*, *Analyzing trajectories…*, *Detecting gaps…*, *Discovering
  intersections…*, *Verifying evidence…*, *Generating hypotheses…*, *Writing paper
  draft…*, *Ranking collaborations…*).
- A red **error message** if the job failed.

While any job is running or pending, the page refreshes the job list every couple of
seconds automatically.

### Job event log

Click **Log** on a job card to open the **Job event log**. It shows time-stamped events,
one per line, such as step started/completed, literature found, a failed item analysis, or
the final completion message. Click **Hide log** or the **X** button to close it. The log
keeps updating while the job runs.

### Pause, resume, cancel, retry

| Button | Available when | Behavior |
|---|---|---|
| **Pause** | `RUNNING` | Requests a pause. Takes effect at the **next step boundary** (not mid-step). The job moves to `PAUSED`. |
| **Resume** | `PAUSED` | Requeues the job; it is picked up again. |
| **Cancel** | `PENDING`, `RUNNING`, `PAUSED` | Requests a cancellation. A running job is cancelled at the next step boundary; a pending/paused job is cancelled outright. |
| **Retry** | `FAILED`, `CANCELLED` | Requeues the job with its **original settings**. Progress resets to 0%. |

### Inspecting discovered papers

Papers collected by a job are analyzed and stored automatically. You do not "attach"
papers to a job — the pipeline fetches what it needs based on your settings. The results
of the analysis are what you review in the evidence/intersection/gap/hypothesis pages.

---

## Evidence and Research Analysis

All result pages below are **read-only**: every intersection, gap, hypothesis,
collaboration candidate, and evidence item is produced by discovery runs. There are no
"create/edit" buttons for them in the UI.

### Intersections

**Meaning:** a candidate area where two researchers' work could meet.

- **View:** sidebar → **Intersections** lists them as cards (status badge, discovery mode,
  title, short description, **novelty %** and **feasibility %**). Click a card for details.
- **Detail page** shows:
  - **Novelty** and **Feasibility** confidence bars.
  - **Researcher A** and **Researcher B** cards with each researcher's **name**,
    **affiliation**, and the **why_researcher_a** / **why_researcher_b** rationale.
  - Optional sections when present: **Shared problem**, **Complementary expertise**,
    **Underlying gap**.
  - **Hypotheses (n)** generated from this intersection, linking to each hypothesis.
  - **Supporting evidence (n)** for the intersection.

### Research Gaps

**Meaning:** underexplored questions detected by cross-referencing the researchers'
literature.

- **View:** sidebar → **Research Gaps**. Each gap is an expandable panel showing a
  **gap-type badge** (e.g. `explicit_limitation`, `future_work_opportunity`,
  `missing_evaluation`, `contradictory_findings`, `methodological_limitation`,
  `domain_transfer_opportunity`, `dataset_limitation`, `reproducibility_issue`), a
  **status** badge, the **description**, and a **Confidence** bar.
- Expand a gap to see its **Supporting evidence** (status + claim for each item).

### Hypotheses

**Meaning:** testable research questions built from a verified intersection, including a
proposed experiment design.

- **View:** sidebar → **Hypotheses** lists hypothesis cards (label, research question,
  confidence, date). Click a card for the full detail.
- **Detail page** shows:
  - **Research question** and **Hypothesis** statements.
  - Optional sections: **Motivation**, **Method**, **Dataset**, **Baseline**, **Metrics**,
    **Expected contribution**, **Risks**.
  - A **From intersection:** link back to the parent intersection's page.
  - An **Experiment design** card with **Proposed approach**, **Baseline**,
    **Dataset**, **Training setup**, **Evaluation setup**, **Metrics**, **Expected
    outcomes**, **Failure conditions**, and an **Ablations** list when present.
  - The **Evidence** supporting the hypothesis.

### Evidence

**Meaning:** the claims and sources gathered and verified during discovery.

- **View:** sidebar → **Evidence Explorer** shows every evidence record for the
  workspace. The subtitle: *"Every claim in this workspace with its verification status
  and source."*
- Filter with the chips at the top, each showing a live count: `ALL (n)`,
  `VERIFIED (n)`, `INFERRED (n)`, `SPECULATIVE (n)`, `UNVERIFIED (n)`, `UNKNOWN (n)`.
- Each item shows a **status badge**, **confidence %**, a clickable **source** link (opens
  the source URL in a new tab), the **claim**, a snippet of the **evidence text**, and the
  **source title**.

### Collaborations

**Meaning:** ranked reasons why two researchers might collaborate.

- **View:** sidebar → **Collaboration Candidates**. The page ranks candidates by a
  weighted score (*"tune weights in Settings"*).
- Each card shows a **rank** (#1, #2, …), a **category badge**, the **score**, a
  relative score bar, **component scores** (e.g. `research relevance: 85%`,
  `method complementarity: 70%`, …), and a short **rationale**.
- Categories are: **Exceptional** (90–100), **Strong** (80–89), **Promising** (70–79),
  **Exploratory** (60–69), and **Weak** (below 60).

---

## Reports and Paper Drafts

### The Paper Draft page

Sidebar → **Paper Draft** is the product's report screen. Its subtitle: *"AI-generated
research-paper draft for a discovery job — a proposal grounded in stored evidence, never
a report of measured results."*

**Generating a draft:**

1. Choose a **Discovery job** from the dropdown (options show `STATUS · date time`).
   The page auto-selects your most recent *completed* or *failed* job the first time.
2. Click **Generate / regenerate** (button reads **Generating…** while working).
3. The draft appears (or an empty-state message: *"No paper draft for this job yet"*).

> A draft requires at least one intersection from the job. If the job produced none, the
> backend reports that a draft cannot be written.

**The draft itself contains:**

- A title and the line `Generated date time · report <id>`.
- **Abstract**, then sections **1. Introduction**, **2. Related Work**, **3. Research
  Gap**, **4. Research Question & Hypothesis**, **5. Methodology**, **6. Experiment
  Design**, **7. Expected Results**, **8. Limitations**, **9. Conclusion**.
- **References (grounded in stored evidence)** — numbered citations, each with a status
  badge, built from the stored papers. Systematic labels are forced by the system:
  - The draft is labeled `AI-GENERATED RESEARCH-PAPER DRAFT — PROPOSED RESEARCH, NOT
    VALIDATED FINDINGS`.
  - The results section is labeled `EXPECTED / PROPOSED OUTCOMES — NOT EMPIRICALLY
    VALIDATED`.
- **Grounding Evidence** — the stored evidence items behind the draft's claims
  (status badge, evidence ID, claim, source title).

The draft is **not editable** in the interface. Clicking **Generate / regenerate** always
creates a fresh draft.

### Exporting the draft

Once a draft exists, two export buttons become enabled:

- **Markdown** — downloads the draft as a `.md` file.
- **PDF** — downloads a PDF version.

The filename is taken from the server response. **PDF export is best-effort:** if the
server cannot render a PDF (for example, the PDF library is unavailable), you will see an
error message. In that case, use the **Markdown** export instead.

> **Backend note:** there is also a general **Reports API**
> (`POST /api/v1/reports`, `GET /api/v1/workspaces/{id}/reports`,
> `GET /api/v1/reports/{report_id}`) that can generate markdown/json/csv/pdf workspace
> reports, but **no part of the web interface uses it**. For end users, the **Paper
> Draft** page is the report feature.

### Workspace JSON export

Settings → **Data export** has an **Export workspace JSON** button. See
[Workspace Management](#workspace-management).

---

## Workspace Management

Sidebar → **Settings**.

### Workspaces

- **Create:** enter a **New workspace name** (required) and a **Description (optional)**,
  then click **Create**. The new workspace becomes active.
- **Select:** click a workspace name to make it active.
- **Delete:** click the red trash button beside a workspace. You are asked to confirm:
  `Delete workspace "name" and all its data?`. Deleting removes the workspace and its
  data permanently.
- Workspaces can be **renamed**? No — the interface has no rename control.

### Collaboration score weights

Six sliders, each from 0 to 100% in 5% steps:

- **Research relevance**
- **Method complementarity**
- **Trajectory alignment**
- **Gap relevance**
- **Evidence strength**
- **Feasibility**

The helper text states the weights are *"Applied to the next discovery run"* in the
active workspace. Changes are saved to the server as you drag a slider.

### Data export

- **Export workspace JSON** downloads everything stored for your workspace as a JSON file
  (named like `my-workspace-export.json`). The text beside it: *"Download everything stored
  for this workspace as JSON (privacy / GDPR-style export)."*
- The export includes the workspace, intersections, gaps, hypotheses, collaboration
  candidates, evidence, and trajectories. It does **not** include jobs, research
  profiles, documents, reports, or experiments.

### Statistics

The **Dashboard** shows your workspace's statistics, including stat cards (**papers**,
**researchers**, **intersections**, **gaps**, **hypotheses**, **collaborations**, **avg
confidence**, **active jobs**) and charts (**Opportunity scores**, **Publications by
year**, **Top topics**, **Recent intersections**).

> **Implementation note:** some dashboard aggregates are computed **across the whole
> database**, not per-workspace (the papers count, top topics, methods, and the
> publications-by-year timeline). Treat those numbers as instance-wide overviews rather
> than workspace-specific totals.

---

## Provider/Model Status

The header (top-right of the screen) always shows which providers are active, in the
format:

```
LLM: <model provider> · Literature: <literature provider>
```

The sidebar shows an amber banner when the system is running in **mock mode**:
*"Mock mode — deterministic demo providers, no external API calls."*

### Mock mode vs real providers

- **Mock mode** means both the language model (LLM) **and** the embeddings are using
  built-in deterministic demo providers. The app works fully offline and returns clearly
  labeled synthetic data. This is the default when no provider credentials are configured.
- **Real mode** means an external model provider is configured (for example, an
  OpenAI-compatible or OpenRouter endpoint) and/or real literature providers are used.
  The banner only disappears when *both* the LLM and embeddings are real; literature
  providers are always live services (OpenAlex, Semantic Scholar, Crossref, arXiv).

The exact provider names shown come from the backend configuration (`.env`).

### When external providers are unavailable

- **Literature searches and discovery jobs may fail** if the external literature
  providers are unreachable. Job cards will show `FAILED` and an error message (e.g. a
  connection error or timeout), and the **Job event log** records it.
- **Check the header readout** to confirm which providers are configured.
- In pure **mock mode** the app does not depend on any external service, so everything
  works offline (with clearly synthetic demo data).
- To change providers, edit the backend `.env` file and restart the backend. See
  `backend/REPRODUCIBILITY.md` for environment guidance.

---

## Typical End-to-End Workflow

A complete walkthrough of what is actually implemented:

1. **Register** (Name, Email, Password ≥ 8 characters) or **Sign in**.
2. **Create a workspace** from the Dashboard onboarding card (enter a name, click
   **Create workspace**). Select it in the header if you have several.
3. **Build a research profile**: go to **Research Profile**, click **Upload CV**, choose a
   CV (.pdf/.docx/.txt).
4. **Find researchers**: go to **Researchers**, search the directory and/or **Add
   researcher** manually.
5. **(Optional) Tune weights**: go to **Settings → Collaboration score weights** and
   adjust the sliders for the next run.
6. **Run discovery**: go to **Discovery**, choose **Researcher A** (and a **Researcher B**
   or a **Field query**), set the **Discovery mode**, **Max papers per researcher**, and
   **Generate hypotheses**, then click **Start discovery**.
7. **Monitor the job**: watch the status badge, progress bar, and current step; open
   **Log** to see events; **Pause**/**Resume**/**Cancel** if needed.
8. **Review evidence**: open **Evidence** and filter by status (`VERIFIED`, `INFERRED`,
   `SPECULATIVE`, …).
9. **Identify gaps and intersections**: open **Research Gaps** to see detected gaps, and
   **Intersections** to review candidate connections (novelty/feasibility, paired
   researchers, supporting evidence).
10. **Formulate hypotheses**: open **Hypotheses** to read the generated research
    questions and experiment designs.
11. **Generate a paper draft**: go to **Paper Draft**, pick the job, click **Generate /
    regenerate**.
12. **Export**: click **Markdown** or **PDF** to download the draft; or use **Settings →
    Export workspace JSON** for a full data export.

---

## Troubleshooting

| Problem | What to check / do |
|---|---|
| **Frontend does not load** | Confirm `npm run dev` is running in `frontend/` and shows `Local: http://localhost:5173/`. Open http://localhost:5173. If the port is busy, change it in `frontend/vite.config.ts`. |
| **Backend unavailable** | Confirm uvicorn is running in `backend/`. Open http://localhost:8000/health — it should return `{"status":"ok",...}`. |
| **`/health` shows an error or nothing** | The backend process is probably not running or crashed mid-startup. Check the terminal output for a traceback, fix configuration errors, and restart. Look for a `500` message in the logs. |
| **Login fails with "Invalid email or password"** | Check the email spelling (addresses are stored lowercase), and that the password is correct. The demo credentials (`demo@researchcollision.dev` / `demo1234`) only exist if you ran `make seed` / `scripts/seed.py`. |
| **Registration fails** | Passwords must be **at least 8 characters**. A duplicate email shows `An account with this email already exists`. |
| **Discovery job fails** | Open the job's red **error message** and its **Log**. Common causes: external literature providers unreachable, a per-paper analysis failure, or the LLM/provider timing out. Fix provider configuration in `.env` and click **Retry** (or **Cancel** and start a new run). A job with only a **Field query** also requires a valid field; if a researcher B was selected, the field query is ignored. |
| **Provider/API errors** | Check the header provider readout. If providers are down, literature search and discovery will fail; the app does not silently invent data in real mode. In **mock mode** you can continue offline. |
| **Empty search results** | Literature search may return nothing if no provider matches. Try a different wording, or search **Researchers** by a name/affiliation/alias. If search works but returns nothing, the provider may be unreachable — check the error status. |
| **Export fails** | **Paper draft export:** make sure a draft exists for the selected job first (click **Generate / regenerate**). If **PDF** fails with a "PDF rendering is unavailable" error, use **Markdown** instead. **Workspace JSON export:** a workspace must be active. |
| **Stale/failed jobs** | Jobs that are `FAILED` or `CANCELLED` can be **Retried** (same settings, progress reset). Jobs that are stuck can be **Cancelled** and replaced with a new run. |
| **Signed out unexpectedly** | Sessions expire after **12 hours** and the UI returns you to the sign-in page when the token is invalid. Sign in again. |
| **Uploaded CV is rejected** | Only `.pdf`, `.docx`, `.txt` are supported; files must be under 10 MB, not empty, and must contain readable text (a minimum number of characters). |

---

## FAQ

**What is a "research intersection"?**
A candidate area where two researchers' work could meaningfully meet, proposed by the
system and shown on the Intersections page.

**Is everything the app says "true"?**
No. All outputs are **AI-generated candidates for human review**. Claims carry evidence
statuses (`VERIFIED`, `INFERRED`, `SPECULATIVE`, `UNVERIFIED`, `UNKNOWN`), and the paper
draft is explicitly labeled as *proposed research, not validated findings*.

**Does the app create an account automatically?**
No. You register once (name, email, password). Workspaces, profiles, and jobs are then
created by you as you go.

**Can I run a discovery with only one real person?**
Yes. Choose Researcher A, and enter a **Field query** as the virtual second researcher.
A Researcher B is optional if a field query is provided.

**What do the evidence statuses mean?**
`VERIFIED` = supporting source confirmed; `INFERRED` = derived with reasoning;
`SPECULATIVE` = plausible but not confirmed; `UNVERIFIED`/`UNKNOWN` = not yet verified.
Always check the linked source before relying on a claim.

**Can I edit or delete intersections, gaps, or hypotheses?**
No. These are generated results and are read-only in the interface.

**Why is my paper draft warning that results are "not validated"?**
Because the draft describes a *proposed* study. The system forces explicit labels so the
draft is never mistaken for measured results.

**Where do the papers come from?**
Live literature providers (OpenAlex, Semantic Scholar, Crossref, and arXiv), queried and
falling back in order. In mock mode, clearly labeled synthetic data is used instead.

**How long does a discovery job take?**
It depends on the settings (e.g. max papers) and on external provider/LLM response times.
You can monitor progress and steps in the Jobs list and leave the page while it runs.

**Can I download my data?**
Yes — export the workspace as JSON (Settings → Export workspace JSON) and/or export the
paper draft as Markdown or PDF.

---

## Data, Privacy, and Limitations

### What data you provide

- **Account:** name, email, and password (stored securely; passwords are hashed).
- **Workspaces:** workspace names and descriptions.
- **Research profiles:** uploaded CV files, the extracted text, and the structured
  "Research DNA" derived from them.
- **Search inputs and job settings:** literature queries, the researchers/field chosen,
  and pipeline options.
- If you add researchers manually, you provide their name and affiliation.

### Where it is stored

According to the implementation, all application data lives in a **local SQLite database**
at `backend/data/researchcollision.db`. Uploaded CV files are written under
`backend/data/uploads/`, and extracted CV text is stored in the database. The frontend
stores your session token and the active workspace selection in the browser's local
storage. No external database is used.

### External providers

- **Literature:** live requests go to OpenAlex, Semantic Scholar, Crossref, and arXiv.
- **Language model (LLM):** when configured (and not in mock mode), text prompts are sent
  to the configured LLM endpoint (for example, an OpenAI-compatible or OpenRouter
  service), as configured in the backend `.env` file.
- If no real credentials are configured, the system uses **mock providers** and makes no
  external API calls for the model; the app then works offline with clearly labeled
  synthetic demo data.

### Mock/development limitations

- In **mock mode**, researchers, papers, and model outputs are **synthetic demo data**,
  clearly labeled with "synthetic" badges where applicable — never real research evidence.
- Real-mode literature search depends on third-party availability and rate limits;
  providers may be unreachable at times.

### Limitations to understand

- Results are **candidate suggestions**, not established findings.
- The paper draft is a **proposed study outline**, explicitly labeled as not validated.
- Some dashboard statistics are **instance-wide** aggregates rather than workspace-only.
- The profile DNA, intersections, gaps, hypotheses, and collaboration rankings are
  machine-generated and were **not** scored by human experts.
- The application does **not** provide password reset, accounts management, or
  multi-user workspaces (each workspace belongs to one user).

---

## Quick Reference

| Main screen / function | Purpose | Typical user action |
|---|---|---|
| Sign in | Log in to the application | Enter email + password, click **Sign in** |
| Create account | Register a new account | Fill in Name / Email / Password (≥ 8 chars), click **Create account** |
| Dashboard | Workspace overview and first-run setup | Create a workspace; review stats/links |
| Research Profile | Build a "Research DNA" from a CV | Click **Upload CV** and pick a file |
| Researchers | Find or add people to pair | Search names/affiliations or use **Add researcher** |
| Literature | Search papers across providers | Enter a query, click **Search** |
| Discovery | Run and monitor the pipeline | Configure a run, click **Start discovery**; Pause/Resume/Cancel/Retry |
| Intersections | Candidate research connections | Open a card to see novelty/feasibility, researchers, evidence |
| Research Gaps | Underexplored questions | Expand a gap to view its evidence |
| Hypotheses | Proposed research questions | Open a card to see the full hypothesis + experiment design |
| Collaboration Candidates | Ranked collaboration reasons | Review ranks, scores, and rationale |
| Evidence Explorer | Claims + verification statuses | Filter by `ALL / VERIFIED / INFERRED / …` |
| Paper Draft | AI-written proposed paper | Pick a job, click **Generate / regenerate**, then **Markdown** or **PDF** |
| Settings — Workspaces | Create/select/delete workspaces | Fill in a name; click **Create** |
| Settings — Weights | Tune collaboration scoring | Drag the six sliders |
| Settings — Data export | Download workspace JSON | Click **Export workspace JSON** |

---

*End of manual. All features described were verified against the current `main` branch
implementation.*