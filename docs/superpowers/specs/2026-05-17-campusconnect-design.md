# CampusConnect — Design Specification

| | |
| --- | --- |
| **Project** | CampusConnect |
| **Tagline** | AI WhatsApp agent that captures, qualifies, nurtures, and hands over admission leads to counsellors. |
| **Repository** | `git@github.com:ENZ048/CampusConnect.git` |
| **Author** | Pratik Yesare |
| **Date** | 2026-05-17 |
| **Status** | Approved design — implementation plan to follow |
| **Audience** | Hiring managers, senior engineers, the author future-self |

---

## Table of contents

1. [Executive summary](#1-executive-summary)
2. [Problem and product framing](#2-problem-and-product-framing)
3. [Goals and non-goals](#3-goals-and-non-goals)
4. [Personas and user stories](#4-personas-and-user-stories)
5. [System architecture](#5-system-architecture)
6. [Tech stack](#6-tech-stack)
7. [Multi-tenancy and isolation](#7-multi-tenancy-and-isolation)
8. [Domain model](#8-domain-model)
9. [Channel layer (WhatsApp first, channel-agnostic core)](#9-channel-layer)
10. [Agent design](#10-agent-design)
11. [RAG knowledge layer](#11-rag-knowledge-layer)
12. [Nurture engine](#12-nurture-engine)
13. [Counsellor dashboard](#13-counsellor-dashboard)
14. [Admin and onboarding](#14-admin-and-onboarding)
15. [Outbound campaigns](#15-outbound-campaigns)
16. [Analytics](#16-analytics)
17. [Resume-grade enhancements](#17-resume-grade-enhancements)
18. [Cross-cutting concerns](#18-cross-cutting-concerns)
19. [Phased delivery plan](#19-phased-delivery-plan)
20. [Risks and open questions](#20-risks-and-open-questions)
21. [Success metrics](#21-success-metrics)
22. [Appendix A — Agent tool catalogue](#appendix-a-agent-tool-catalogue)
23. [Appendix B — Prompt template structure](#appendix-b-prompt-template-structure)
24. [Appendix C — REST API surface (selected)](#appendix-c-rest-api-surface-selected)
25. [Appendix D — Glossary](#appendix-d-glossary)

---

## 1. Executive summary

CampusConnect is a multi-tenant SaaS that gives educational institutes an AI-powered WhatsApp admissions agent. The agent captures inbound leads (Click-to-WhatsApp ads, website buttons, QR codes), engages them in natural conversation, qualifies them against a five-field framework (name, course interest, eligibility, intent timeline, mode and city), answers questions using a retrieval-augmented knowledge base, nurtures silent leads through a scheduled follow-up sequence, and hands qualified leads to a human counsellor through a live-takeover dashboard. It also runs outbound campaigns from CSV uploads using Meta-approved templates, integrates with Google Calendar for callback bookings, fires outbound webhooks into the institute's CRM, and is delivered as a polished SaaS product with self-serve onboarding and Stripe billing.

The project is intentionally engineered to demonstrate the full surface of modern AI product work: production-grade backend (FastAPI, Celery, Postgres with pgvector, Row-Level Security), agent engineering (function-calling, model routing, prompt versioning with A/B testing, RAG with citations, evals in CI), realtime UX (WebSocket live takeover, message status callbacks), and SaaS plumbing (multi-tenant onboarding, Stripe, webhooks, runbooks, load tests).

---

## 2. Problem and product framing

### 2.1 The real business problem

Educational institutes — coaching centers, colleges, training schools — buy aggressive top-of-funnel lead flow from Meta Ads, Google Ads, Instagram, JustDial, Shiksha, CollegeDekho, and other education portals. They receive hundreds of leads per day across these sources. The fundamental operational problem is not "students ask questions" — it is that the admission team cannot:

1. Reply to every lead within minutes (the window when interest is highest)
2. Follow up consistently with leads who go silent
3. Qualify each lead before scheduling a counsellor call
4. Surface the right leads to the right counsellor with the right context

The result is a multi-million-rupee leak: ad budget produces leads, but conversion to enrolled students is bottlenecked by manual lead-ops capacity. Institutes either hire large admission teams (expensive, inconsistent) or accept the leak.

### 2.2 The product

CampusConnect replaces the first-line admissions team with a WhatsApp AI agent that does the unglamorous, high-volume work (instant reply, qualification, nurture, follow-up) and reserves human counsellor time for the leads that matter (qualified, ready to be persuaded). The product is sold to institutes as a SaaS subscription with usage-based plans.

### 2.3 Why WhatsApp

In the Indian education market — the primary target — WhatsApp is the channel students and parents actually use. SMS feels institutional. Email is ignored. Phone calls are intrusive. WhatsApp is intimate, asynchronous, and ubiquitous. Institutes already use it informally; CampusConnect formalises it.

---

## 3. Goals and non-goals

### 3.1 Goals (in scope for v1)

- Multi-tenant SaaS: any institute can self-sign-up, connect a WhatsApp Business number, and go live the same day.
- Inbound conversation handling: webhook ingestion, agent engagement, qualification, handover.
- Outbound campaigns: CSV upload, template message sending, rate-limited delivery.
- Scheduled nurture sequences with cancellation rules.
- Counsellor dashboard with live takeover.
- Per-institute RAG knowledge base for FAQ-style answers with citations.
- Channel abstraction with WhatsApp as the first adapter and Telegram as a second working adapter.
- Agent observability: trace viewer, Langfuse integration, prompt versioning with A/B testing.
- Voice-note transcription, multilingual handling (English / Hindi / Hinglish).
- Calendar-integrated callback booking via Google Calendar.
- Outbound webhooks for external CRM integration.
- Stripe billing with three plans and metered usage.
- DPDP / GDPR-compliant data export and deletion flows.
- Public marketing site, demo sandbox, API documentation, status page.
- Production runbook, end-to-end Playwright tests, k6 load tests.

### 3.2 Non-goals (deferred to v1.1+)

- Voice / phone-call agent (mentioned as a future channel, not built).
- Native mobile apps for counsellors (the web dashboard is mobile-responsive).
- Fine-tuned domain models (we rely on prompt engineering and RAG).
- Salesforce / HubSpot first-party connectors (covered by generic outbound webhooks).
- A no-code conversation-flow builder (qualification fields are configurable, but the conversation engine is LLM-driven, not visually authored).
- Custom analytics SQL editor in-app (we ship a fixed analytics page; advanced users export CSV).
- Programmatic billing of leads (we meter `leads_created`, not per-message).

### 3.3 Non-negotiables

- All conversations must respect WhatsApp's 24-hour customer service window. Outside it, only approved templates may be sent.
- No agent reply may contain a fee, date, or eligibility figure that did not come from a tool call result. This is enforced by an eval and reinforced by the system prompt.
- A counsellor's "Take over" click must silence the agent within the same WhatsApp turn (sub-second). Race conditions between agent and counsellor are unacceptable.
- All tenant data must be isolated at three layers: API middleware, ORM filter, and Postgres Row-Level Security.

---

## 4. Personas and user stories

### 4.1 Personas

**Priya — admissions head at a Pune coaching institute.** Manages four counsellors, drowning in WhatsApp messages from Meta ads. Wants instant first-touch and fewer "you never replied" complaints. Will be the buyer and primary admin in the dashboard.

**Vikram — counsellor on Priya's team.** Lives in the dashboard during work hours. Wants pre-qualified leads with full context, not raw inquiries. Wants to take over a conversation in one click when the agent has done its job.

**Rohan — 12th-pass student** who clicked a Meta ad. Doesn't want a form. Just wants to know fees, eligibility, and what comes next. Replies in Hinglish. Sometimes sends voice notes. Will ghost if not engaged within minutes.

**Anita — Rohan's mother.** Often the actual decision-maker. Asks about hostel, safety, scholarships, placements. May join the same WhatsApp thread later from Rohan's phone or her own.

### 4.2 Headline user stories

- As Priya, I sign up at campusconnect.dev, connect my WhatsApp Business number, upload my brochure, invite my counsellors, and see leads start landing within an hour.
- As Rohan, I tap "Chat on WhatsApp" on an ad, message "fees for B.Tech?", and get a real conversation in Hinglish that ends with a counsellor calling me back at a time I chose.
- As Vikram, I open the dashboard, see a qualified lead with a 3-line summary at the top, take over with one click, reply live in the same thread, and never have to ask the lead the questions the agent already asked.
- As Priya, I upload a CSV of 800 leads from a justdial export, pick the welcome template, dry-run on my own phone, launch, and watch sends rate-limit themselves to Meta's tier.
- As Anita, I message asking about hostel safety; the agent retrieves the right paragraph from the uploaded prospectus and quotes it with a citation, no hallucination.

---

## 5. System architecture

### 5.1 High-level diagram

```
                          ┌─────────────────────────────────────┐
                          │   Meta WhatsApp Cloud API           │
                          │   Telegram Bot API (channel #2)     │
                          └────────────────┬────────────────────┘
                                           │ inbound webhooks (signed)
                                           ▼
   ┌─────────────────────────┐   ┌─────────────────────────────────────────┐   ┌─────────────────────┐
   │  Next.js dashboard      │   │  FastAPI API service                    │   │ Postgres + pgvector │
   │  (Vercel)               │◄──┤  - /webhook/{channel}                   │◄──┤  (Neon)             │
   │  - NextAuth magic link  │   │  - /api/v1/*                            │   │  RLS enabled        │
   │  - Leads queue, inbox   │   │  - /ws/* (WebSocket)                    │   └─────────────────────┘
   │  - Lead detail + trace  │   │  - ChannelRouter                        │
   │  - Settings, billing    │   │  - JWT middleware + RLS context setter  │   ┌─────────────────────┐
   │  - Demo sandbox         │   │  - Stripe webhook handler               │◄──┤  Redis (Upstash)    │
   └────────────┬────────────┘   └──────────────────┬──────────────────────┘   │  - Celery broker    │
                │ REST + WS                          │ enqueue                  │  - WS pubsub        │
                │                                    ▼                          │  - Token buckets    │
                │                ┌──────────────────────────────────────────┐   └─────────────────────┘
                │                │  Celery workers (multiple queues)        │
                │                │   ├─ agent.run             (LLM turns)   │   ┌─────────────────────┐
                │                │   ├─ channel.send          (outbound)    │◄──┤  S3-compatible      │
                │                │   ├─ rag.ingest_doc        (embeddings)  │   │  storage (R2)       │
                │                │   ├─ nurture.tick          (beat)        │   │  brochures, audio   │
                │                │   ├─ outbound.campaign_send              │   └─────────────────────┘
                │                │   ├─ analytics.refresh     (beat)        │
                │                │   ├─ webhook.deliver       (out)         │   ┌─────────────────────┐
                │                │   └─ trace.write_to_langfuse             │◄──┤  OpenAI API         │
                │                └──────────────────────────────────────────┘   │  (chat + Whisper +  │
                │                                                                │   embeddings)       │
                │   Realtime via Redis pubsub                                    └─────────────────────┘
                ▼
   ┌─────────────────────────┐   ┌─────────────────────────┐   ┌─────────────────────┐
   │  Langfuse (self-hosted) │   │  Stripe                 │   │  Google Calendar    │
   │  - traces, datasets     │   │  - billing portal       │   │  - OAuth, free/busy │
   │  - evals, scoring       │   │  - subscriptions        │   │  - event creation   │
   └─────────────────────────┘   └─────────────────────────┘   └─────────────────────┘
```

### 5.2 Process boundaries

| Process | Responsibility | Why isolated |
| --- | --- | --- |
| `apps/api` (FastAPI) | Webhook ingest, REST, WebSocket fan-out, auth. Must ack inbound webhooks within 5 seconds. | Latency-critical; cannot block on LLM/network. |
| `apps/worker` (Celery) | Every slow thing: LLM calls, channel sends, RAG ingestion, nurture ticks, outbound campaigns, trace writes, webhook deliveries. | Independent scaling; retry semantics; survives external outages. |
| `apps/beat` (Celery Beat) | Periodic schedulers: nurture tick (every 60s), template sync (daily), analytics refresh (every 5 min), backup verification (daily). | Cron with persistence. |
| `apps/web` (Next.js) | Dashboard, marketing site, demo sandbox. Edge functions for auth. | Independent deploy cadence on Vercel. |
| `langfuse` | LLM observability. | Off-the-shelf; self-hosted so demo is dependency-free. |

### 5.3 Realtime fan-out

```
inbound message received in worker
  → INSERT messages row
  → Redis PUBLISH 'org:{org_id}:lead:{lead_id}' { event: 'message_new', message: {...} }
       ↓
  FastAPI WS hub subscribes to 'org:{org_id}:*' on connect (authed)
       ↓
  forwards JSON event to connected dashboard clients in that org
       ↓
  dashboard reconciles local state and renders
```

This pattern works for `message_new`, `message_status_updated`, `lead_updated`, `mode_changed`, `trace_ready`, `nurture_scheduled`, `campaign_progress`.

---

## 6. Tech stack

| Layer | Choice | Notes |
| --- | --- | --- |
| Language (backend) | Python 3.12 | Async FastAPI; typed code; matches LLM ecosystem |
| API framework | FastAPI | Async; Pydantic; OpenAPI for free |
| ORM | SQLAlchemy 2.x (async) | Mature; expressive |
| Migrations | Alembic | Standard with SQLAlchemy |
| DB | Postgres 16 | With `pgvector` and `pg_trgm` extensions |
| Vector index | `pgvector` ivfflat (HNSW later) | Avoids a second datastore |
| Cache + broker | Redis 7 | Celery broker, WS pubsub, rate-limit token buckets |
| Worker | Celery 5 | `prefork` for IO-bound LLM calls |
| Scheduler | Celery Beat with `django-celery-beat`-style persistence in Postgres | Survives restarts |
| LLM | OpenAI: `gpt-4o-mini` default, `gpt-4o` for escalations, `whisper-1` for voice | Abstracted behind `LLMProvider` interface; Anthropic adapter ships as a stub |
| Embeddings | OpenAI `text-embedding-3-small` (1536 dims) | Cheap, batchable |
| Observability (LLM) | Langfuse (self-hosted via docker-compose) | Traces, datasets, scoring |
| Observability (app) | Sentry + OpenTelemetry exporter | Errors + traces |
| Frontend | Next.js 15 App Router, TypeScript, Tailwind, shadcn/ui | Industry default |
| Frontend state | TanStack Query, Zustand for ephemeral UI state | Avoid Redux |
| Realtime client | Native WebSocket; reconnection wrapper | One file, no external dep |
| Auth | NextAuth (Auth.js) — email magic link primary, Google OAuth secondary | Custom JWT with `org_id`, `role` claims |
| Storage | Cloudflare R2 (S3-compatible) | Brochures, voice notes, exports |
| Email | Resend | Magic links, invites, daily digests |
| Billing | Stripe (Checkout + Customer Portal + metered usage) | Three plans |
| i18n | `next-intl` (web), `gettext`-style for Python templates | EN / HI / Hinglish |
| Testing — unit | `pytest`, `pytest-asyncio` | |
| Testing — agent evals | Custom runner over OpenAI replay snapshots; results pushed to Langfuse | |
| Testing — e2e | Playwright | Critical user journeys |
| Testing — load | k6 | Webhook hot path |
| Lint / format | `ruff` (Python), `eslint` + `prettier` (TS) | |
| Type checking | `mypy --strict` for `app/`, `tsc --noEmit` strict in web | |
| CI | GitHub Actions (matrix: lint, type, unit, evals, build) | Preview deploy on PR |
| Hosting | Fly.io for API + workers + Langfuse, Neon for Postgres, Upstash for Redis, Vercel for web, R2 for storage | All have generous free / hobby tiers |
| Status page | Static page at `status.campusconnect.dev` driven by GitHub Actions uptime job | Zero SaaS dependency |

### Why these choices, in three sentences

The stack picks the simplest production-grade option at every layer: Python because that's where the agent ecosystem lives; FastAPI + Celery because they are battle-tested and async; Postgres + pgvector because one datastore beats two; Next.js because it is the universal frontend assumption; OpenAI because it is the most recognisable function-calling LLM. Every choice is one a senior engineer would defend without flinching. Nothing exotic, nothing fashionable, nothing unjustified.

---

## 7. Multi-tenancy and isolation

Tenancy is enforced at three independent layers. Any one of them, alone, would mostly work. Together they make cross-tenant data exposure require the simultaneous failure of all three.

### 7.1 Layer 1 — API middleware (request gating)

Every authenticated request resolves an `org_id` from the JWT. A FastAPI dependency `current_org()` sets `request.state.org_id`. Routes that require an org call `Depends(current_org)`; the few that do not (webhook, public signup, demo provisioning) opt out explicitly.

The Postgres session for the request issues `SET LOCAL app.current_org_id = '...'` immediately after authentication. This activates Row-Level Security policies for the duration of the transaction.

### 7.2 Layer 2 — SQLAlchemy auto-filter

A global SQLAlchemy event listener inspects every `Select`, `Update`, and `Delete` against tenanted tables and injects `WHERE org_id = :current_org_id` if the binding context is set. Models that participate are tagged with the `TenantedMixin` mixin.

Bypass is explicit: code that legitimately needs cross-tenant access (the admin superuser console, the demo provisioner) calls `with bypass_tenant_filter():`. Any such bypass is logged to `audit_log`.

### 7.3 Layer 3 — Postgres Row-Level Security

Every tenanted table has an RLS policy:

```sql
CREATE POLICY tenant_isolation ON leads
  USING (org_id = current_setting('app.current_org_id')::uuid);
ALTER TABLE leads ENABLE ROW LEVEL SECURITY;
ALTER TABLE leads FORCE ROW LEVEL SECURITY;
```

`FORCE` ensures even the table owner is subject to the policy. A misconfigured ORM cannot read data it should not, and a SQL injection that bypasses the ORM still hits RLS.

### 7.4 Cross-tenant by design

A small set of tables is intentionally global: `organizations`, `plans`, `prompt_versions` (when shared as templates), `wa_templates` (when cached at platform level — but every org has its own copy too). They live in a `public` schema with `org_id NULL` semantics, and no RLS.

---

## 8. Domain model

This section enumerates the tables. Field types are simplified; the canonical schema lives in Alembic migrations.

### 8.1 Identity and tenancy

```
organizations
  id UUID PK
  name TEXT
  slug TEXT UNIQUE
  plan_id FK -> plans
  status ENUM('trial','active','past_due','suspended')
  created_at TIMESTAMPTZ
  default_language ENUM('en','hi','hinglish') DEFAULT 'hinglish'
  branding JSONB                         -- logo url, primary color
  data_residency ENUM('in','us','eu') DEFAULT 'in'

users
  id UUID PK
  org_id FK NULLABLE                     -- nullable for platform superusers
  email CITEXT UNIQUE
  name TEXT
  role ENUM('platform_admin','org_admin','counsellor')
  status ENUM('invited','active','disabled')
  google_calendar_token JSONB NULLABLE   -- encrypted OAuth tokens
  last_seen_at TIMESTAMPTZ
  created_at TIMESTAMPTZ

org_invites
  id UUID PK
  org_id FK
  email CITEXT
  role ENUM
  token_hash TEXT
  expires_at TIMESTAMPTZ
```

### 8.2 Channels and conversations

```
channel_accounts                         -- a connected channel for an org
  id UUID PK
  org_id FK
  type ENUM('whatsapp','telegram','sms','instagram')
  external_id TEXT                       -- e.g. wa_phone_number_id, telegram_bot_id
  display_name TEXT
  secrets JSONB                          -- encrypted access tokens, app secrets
  webhook_verify_token TEXT
  status ENUM('connecting','connected','error','disconnected')
  rate_limit_tier ENUM('1k','10k','100k','unlimited')  -- mirrors Meta tiers
  last_verified_at TIMESTAMPTZ

leads
  id UUID PK
  org_id FK
  channel_account_id FK -> channel_accounts
  external_id TEXT                       -- phone number for WA, chat_id for TG
  name TEXT
  email CITEXT NULLABLE
  course_interest_id FK -> courses NULLABLE
  eligibility TEXT
  intent_timeline TEXT
  mode_preference ENUM('online','offline','hybrid','unknown')
  city TEXT
  source ENUM('inbound','outbound','manual','demo')
  source_meta JSONB                      -- utm params, ad id, campaign id
  qualification_score INT                -- 0..100, computed
  status ENUM('new','engaging','qualified','handover','customer','cold','blocked')
  assigned_counsellor_id FK -> users NULLABLE
  language ENUM('en','hi','hinglish','unknown') DEFAULT 'unknown'
  sentiment_summary JSONB                -- rolling tags: angry, fee_objection, ...
  last_inbound_at TIMESTAMPTZ
  last_outbound_at TIMESTAMPTZ
  qualified_at TIMESTAMPTZ
  handover_at TIMESTAMPTZ
  created_at TIMESTAMPTZ
  UNIQUE (org_id, channel_account_id, external_id)

conversations
  id UUID PK
  org_id FK
  lead_id FK
  channel_account_id FK
  mode ENUM('agent','human') DEFAULT 'agent'
  current_state JSONB                    -- agent scratchpad
  current_prompt_version_id FK -> prompt_versions
  created_at TIMESTAMPTZ
  last_activity_at TIMESTAMPTZ
  last_inbound_at TIMESTAMPTZ            -- drives 24h-window check; updated on every inbound
  last_outbound_at TIMESTAMPTZ           -- last successful outbound

messages
  id UUID PK
  org_id FK
  conversation_id FK
  direction ENUM('inbound','outbound')
  sender ENUM('lead','agent','counsellor','system')
  sender_user_id FK -> users NULLABLE
  channel_message_id TEXT                -- wamid for WA, chat_message_id for TG
  content_type ENUM('text','template','image','document','interactive','audio','sticker')
  content_text TEXT
  content_meta JSONB                     -- media urls, template name/vars
  audio_transcript TEXT NULLABLE         -- for voice notes
  detected_language ENUM
  sentiment_tags TEXT[]                  -- e.g. {'fee_objection','urgent'}
  status ENUM('queued','sent','delivered','read','failed')
  error_code TEXT
  created_at TIMESTAMPTZ
  INDEX (conversation_id, created_at)
```

### 8.3 Courses and knowledge

```
courses
  id UUID PK
  org_id FK
  name TEXT
  code TEXT
  description TEXT
  mode ENUM('online','offline','hybrid')
  duration_months INT
  fees_inr INT
  eligibility TEXT
  seats_available INT
  brochure_url TEXT                      -- on R2
  is_active BOOL
  created_at TIMESTAMPTZ

knowledge_documents
  id UUID PK
  org_id FK
  title TEXT
  source_type ENUM('pdf','url','text')
  source_url TEXT
  raw_text TEXT
  page_count INT
  status ENUM('pending','embedding','embedded','failed')
  embedded_at TIMESTAMPTZ
  created_at TIMESTAMPTZ

knowledge_chunks
  id UUID PK
  org_id FK
  document_id FK
  chunk_index INT
  content TEXT
  token_count INT
  embedding VECTOR(1536)
  INDEX ivfflat (embedding vector_cosine_ops) WITH (lists = 100)
  INDEX (org_id, document_id)
```

### 8.4 Agent observability

```
prompt_versions
  id UUID PK
  org_id FK NULLABLE                     -- NULL = platform-default
  name TEXT                              -- e.g. "qualification.system.v3"
  body TEXT                              -- the Jinja template content
  variables JSONB                        -- declared input variables
  hash TEXT                              -- sha256 of normalized body
  is_active BOOL
  traffic_percent INT                    -- 0..100 for A/B
  created_by FK -> users
  created_at TIMESTAMPTZ
  UNIQUE (org_id, name, hash)

agent_traces
  id UUID PK
  org_id FK
  conversation_id FK
  message_id FK -> messages              -- the agent's reply this trace produced
  prompt_version_id FK -> prompt_versions
  model TEXT                             -- "gpt-4o-mini" / "gpt-4o" / ...
  router_decision JSONB                  -- {"reason":"complex_question","escalated":true}
  tokens_in INT
  tokens_out INT
  cost_usd NUMERIC(10,6)
  latency_ms INT
  steps JSONB                            -- ordered: tool_calls, rag_hits, model_outputs
  langfuse_trace_id TEXT
  created_at TIMESTAMPTZ
  INDEX (conversation_id, created_at)
```

### 8.5 Nurture and campaigns

```
nurture_sequences
  id UUID PK
  org_id FK
  name TEXT
  is_default BOOL
  steps JSONB                            -- [{after_hours, template_name, skip_if_qualified}, ...]
  created_at TIMESTAMPTZ

nurture_jobs
  id UUID PK
  org_id FK
  lead_id FK
  sequence_id FK
  next_step_index INT
  next_run_at TIMESTAMPTZ
  status ENUM('scheduled','running','done','cancelled','failed')
  reason TEXT NULLABLE                   -- why cancelled/failed
  INDEX (next_run_at) WHERE status = 'scheduled'

outbound_campaigns
  id UUID PK
  org_id FK
  name TEXT
  channel_account_id FK
  template_name TEXT
  csv_storage_key TEXT                   -- R2 key
  column_map JSONB                       -- {phone:"col_a", name:"col_b", "1":"col_c"}
  total_rows INT
  sent_count INT
  delivered_count INT
  failed_count INT
  status ENUM('draft','scheduled','running','paused','done','failed')
  created_by FK -> users
  created_at TIMESTAMPTZ
  scheduled_at TIMESTAMPTZ NULLABLE

outbound_campaign_recipients
  id UUID PK
  campaign_id FK
  org_id FK
  phone TEXT
  name TEXT
  variables JSONB
  status ENUM('pending','sent','delivered','failed','skipped_duplicate')
  message_id FK -> messages NULLABLE
  error_code TEXT
  INDEX (campaign_id, status)
```

### 8.6 Integrations and billing

```
wa_templates
  id UUID PK
  org_id FK
  name TEXT
  language TEXT
  category ENUM('marketing','utility','authentication')
  body TEXT
  status ENUM('pending','approved','rejected','paused')
  last_synced_at TIMESTAMPTZ
  UNIQUE (org_id, name, language)

webhook_subscriptions
  id UUID PK
  org_id FK
  url TEXT
  secret TEXT                            -- HMAC shared secret (encrypted)
  events TEXT[]                          -- e.g. {'lead.qualified','lead.handover'}
  is_active BOOL
  last_delivery_at TIMESTAMPTZ
  failure_count INT

webhook_deliveries
  id UUID PK
  subscription_id FK
  org_id FK
  event TEXT
  payload JSONB
  attempts INT
  status ENUM('pending','delivered','failed')
  response_code INT
  response_body TEXT
  created_at TIMESTAMPTZ

calendar_bookings
  id UUID PK
  org_id FK
  lead_id FK
  user_id FK -> users                    -- the counsellor
  start_at TIMESTAMPTZ
  end_at TIMESTAMPTZ
  google_event_id TEXT
  status ENUM('booked','cancelled','completed','no_show')

plans                                    -- platform-global
  id UUID PK
  code TEXT UNIQUE                       -- 'free','growth','enterprise'
  name TEXT
  monthly_inr INT
  monthly_lead_quota INT
  features JSONB

billing_subscriptions
  id UUID PK
  org_id FK UNIQUE
  stripe_customer_id TEXT
  stripe_subscription_id TEXT
  plan_id FK
  current_period_start TIMESTAMPTZ
  current_period_end TIMESTAMPTZ
  status ENUM('trialing','active','past_due','canceled')
  usage_leads_current_period INT

audit_log
  id UUID PK
  org_id FK
  actor_user_id FK NULLABLE
  action TEXT                            -- 'lead.qualify','conversation.takeover','prompt.publish',...
  target_type TEXT
  target_id UUID
  meta JSONB
  created_at TIMESTAMPTZ
```

---

## 9. Channel layer

### 9.1 The `ChannelAdapter` interface

```python
class ChannelAdapter(Protocol):
    type: ChannelType                     # 'whatsapp' | 'telegram' | ...
    def verify_webhook(self, request: Request) -> bool: ...
    def parse_inbound(self, payload: dict) -> list[InboundMessage]: ...
    def send_text(self, account: ChannelAccount, to: str, text: str) -> SendResult: ...
    def send_template(self, account, to, template, variables) -> SendResult: ...
    def send_media(self, account, to, media: MediaRef) -> SendResult: ...
    def send_interactive(self, account, to, payload: InteractivePayload) -> SendResult: ...
    def can_send_freeform(self, conversation: Conversation) -> bool: ...
    def supported_features(self) -> set[Feature]: ...
```

### 9.2 The two shipped adapters

**WhatsApp adapter** (`apps/api/channels/whatsapp.py`) — the primary, production target. Handles Meta Cloud API webhook payloads, signature verification (`X-Hub-Signature-256` against the app secret), template messages, media downloads (Meta returns a media id; we GET the media URL with the access token, stream the bytes to R2, store the R2 URL on the message), interactive list and button messages, and the 24-hour customer service window check.

**Telegram adapter** (`apps/api/channels/telegram.py`) — proves the abstraction is real. Handles Bot API webhooks (no signature; we verify by URL secret path), free-form messages without a 24h window, inline keyboards as the analogue of WhatsApp interactive messages. Useful for the demo sandbox because Telegram bots are trivial to spin up.

### 9.3 The 24-hour window enforcement

The single biggest source of WhatsApp-bot production bugs. We encode the rule once, in the WhatsApp adapter's `can_send_freeform`:

```python
def can_send_freeform(self, conversation: Conversation) -> bool:
    if conversation.last_inbound_at is None:
        return False
    return (now() - conversation.last_inbound_at) < timedelta(hours=24)
```

Every send path checks this. If freeform is not allowed, the send is rerouted to a template message (the agent's tool is told to use a template; the counsellor UI shows a "Template only" banner with a template picker).

### 9.4 Rate limiting

A per-`channel_account_id` Redis token bucket models Meta's tier limits. Outbound sends pull tokens before dispatching; if dry, the task self-reschedules with backoff. Campaigns pause gracefully and resume when the bucket refills.

---

## 10. Agent design

### 10.1 The conversation loop

```
on inbound message received and conversation.mode = 'agent':
  enqueue agent.run(conversation_id, message_id)

agent.run:
  with RLS context for conversation.org_id:
    1. Acquire advisory lock on conversation_id (prevents concurrent runs).
    2. Re-read conversation; if mode != 'agent', release lock and exit.
    3. Detect language on the inbound message if conversation.language is unknown.
    4. Run sentiment tagging on the inbound message; store tags on messages row.
    5. Build messages array:
         - system prompt (rendered from active prompt_version using lead + org context)
         - last 20 messages from conversation (compressed older history if >20)
    6. Pick model via Router (see 10.4).
    7. Call OpenAI chat.completions with tools=catalog(), tool_choice="auto".
    8. While response contains tool_calls:
         - for each tool_call: dispatch via ToolDispatcher; append result.
         - hard cap: 6 tool rounds. On 7th, force a final text generation.
    9. Capture full trace (model, prompt version, tool steps, RAG hits, tokens, latency).
    10. Persist trace to agent_traces and Langfuse.
    11. Insert outbound message row (status=queued) and enqueue channel.send.
    12. Re-check conversation.mode just before send (race: counsellor may have taken over).
         If mode = 'human', mark the message 'cancelled' and exit.
    13. Update conversation.current_state with collected fields and last topic.
    14. Publish 'message_sent' on Redis pubsub.
    15. Release lock.
```

### 10.2 Prompt composition

System prompts are Jinja templates stored in `prompt_versions`. Variables resolved at runtime:

- `org`: name, default_language, branding, custom guardrails
- `lead`: name, channel, language, collected fields, sentiment tags
- `state`: missing fields, last topic, conversation length
- `today`: current date in IST
- `policies`: hard guardrails (never invent fees, never promise admission, always offer human handover on request)

A platform default `qualification.system.v1` ships in seed data. Orgs may fork it; A/B testing splits traffic between active versions.

### 10.3 Tool catalogue (see Appendix A for full schemas)

`save_lead_field`, `lookup_course`, `lookup_kb`, `send_brochure`, `propose_callback_slots`, `book_callback`, `handover_to_human`, `mark_not_interested`, `set_language_preference`.

### 10.4 Model routing

```
default = "gpt-4o-mini"
escalate to "gpt-4o" if any of:
  - lookup_kb returned all hits with similarity < 0.55 (open-ended question)
  - inbound message has sentiment tag in {'angry','confused','fee_objection','comparing_competitor'}
  - conversation length > 8 turns without progress on qualification fields
  - explicit detected intent: 'talk_to_human' → skip model, force handover
all decisions persisted on agent_traces.router_decision for analytics
```

### 10.5 Evals

`tests/agent_evals/` holds scripted multi-turn scenarios with assertions. Examples:

- `eval_collects_all_fields_in_straight_conversation`
- `eval_handover_on_explicit_request`
- `eval_no_hallucinated_fees`
- `eval_rag_citation_correctness`
- `eval_hinglish_response_to_hinglish`
- `eval_voice_note_transcribed_and_responded`
- `eval_template_send_outside_24h_window`
- `eval_does_not_reply_after_takeover`

Evals run in CI on every PR touching `app/agent/` or `app/channels/` or any prompt template. Failures block merge. Results are pushed to Langfuse for trend tracking.

### 10.6 Guardrails

- Hard rule in the system prompt: never state a numeric fee, date, eligibility cutoff, or scholarship percentage that did not come from a `lookup_course` or `lookup_kb` result. A separate eval (`eval_no_hallucinated_fees`) replays a curated set of conversations and asserts no numbers appear without prior tool calls.
- Refusal patterns: if `lookup_kb` returns nothing useful, the agent says so honestly and offers handover. It never speculates.
- Prompt injection defence: tool results are wrapped in delimiters; the agent is instructed to treat their contents as data, not instructions. Inbound user messages are similarly framed.

---

## 11. RAG knowledge layer

### 11.1 Ingestion pipeline

```
upload received (PDF / URL / paste-text)
  → knowledge_documents row inserted (status='pending')
  → rag.ingest_doc(document_id) enqueued

rag.ingest_doc:
  1. Load source:
       PDF  → pdfplumber, page-by-page, store raw_text and page_count
       URL  → requests + readability-lxml, fetch HTML, strip nav/footer
       text → store as-is
  2. Normalize: collapse whitespace, drop repeated headers/footers across pages.
  3. Chunk: recursive character splitter, target 800 tokens, 100 overlap, prefer split on \n\n then \n then '. '.
  4. Embed: batch of 100 chunks per OpenAI call, with retry/backoff on rate limits.
  5. Upsert knowledge_chunks rows.
  6. Update knowledge_documents.status = 'embedded', set embedded_at.
  7. Publish 'kb_ready' on Redis pubsub so settings page can update.
```

### 11.2 Retrieval

The `lookup_kb` tool runs:

```sql
SELECT chunk_index, content, document_id,
       1 - (embedding <=> :q_emb) AS similarity
FROM knowledge_chunks
WHERE org_id = current_setting('app.current_org_id')::uuid
ORDER BY embedding <=> :q_emb
LIMIT :k;
```

`:q_emb` is the question embedded with the same model. Results are returned with the parent document title for citation. The tool's contract guarantees: if the top result's similarity < 0.55, return `{"hits": [], "advice": "no good match"}`.

### 11.3 Re-embedding

If an org changes embeddings model in the future, a `rag.reembed_all(org_id)` task re-vectorises everything with the new model. Versioning is tracked in `knowledge_chunks.embedding_model` (NULL = legacy). Out of scope for v1 implementation but designed-for.

### 11.4 Citations in the dashboard

When the agent's reply was produced from a tool result, the trace contains the `lookup_kb` step with the chunk content and document. The dashboard's chat view renders a small citation chip under the agent message: "from Prospectus.pdf, page 14". Clicking opens the chunk in a side panel. This is one of the small details that signal real-world readiness.

---

## 12. Nurture engine

### 12.1 Sequence definition

Per-org, JSON, edited via drag-drop UI:

```json
[
  { "after_hours": 24,  "template_name": "followup_24h_v1", "skip_if_qualified": true, "skip_if_cold": true },
  { "after_hours": 72,  "template_name": "followup_3d_v1",  "skip_if_qualified": true, "skip_if_cold": true },
  { "after_hours": 168, "template_name": "followup_7d_v1",  "skip_if_qualified": true, "skip_if_cold": true }
]
```

### 12.2 Scheduling

When a lead is created (inbound or outbound), a `nurture_jobs` row is created with `next_run_at = now() + steps[0].after_hours`. The default sequence is used unless the org has a custom one.

### 12.3 Beat tick

`nurture.tick` runs every 60 seconds:

```sql
SELECT * FROM nurture_jobs
WHERE status = 'scheduled' AND next_run_at <= now()
FOR UPDATE SKIP LOCKED
LIMIT 50;
```

For each job:

1. Reload the lead. If status in `('qualified','customer','cold','blocked')` → cancel job, log reason.
2. If the lead has replied since the job was last advanced → cancel job; create a fresh one starting from step 0 (re-engaged leads enter the funnel from the top).
3. Verify the WhatsApp 24-hour window: a template is always required for nurture follow-ups, so this is a sanity check on template approval.
4. Enqueue `channel.send` with the step's template and lead's stored variables.
5. Advance `next_step_index`. If past the last step, mark job `done`.
6. Bump `next_run_at` based on the next step's `after_hours`.

### 12.4 Cancellation rules (single source of truth)

| Trigger | Effect |
| --- | --- |
| Lead replies | Cancel + create fresh job starting step 0 |
| Lead becomes qualified | Cancel permanently |
| Lead becomes customer | Cancel permanently |
| Lead marked cold | Cancel permanently |
| Lead marked blocked | Cancel permanently |
| Template no longer approved | Cancel + alert org admin |
| Org subscription suspended | Cancel + alert |

---

## 13. Counsellor dashboard

### 13.1 Information architecture

```
/                                          public marketing site
/demo                                      sandbox auto-provisioner
/login                                     magic link
/signup                                    org creation
/app                                       authed shell (sidebar + topbar)
  /app/inbox                               all active conversations, filter rail
  /app/leads                               leads table (sort, filter, search, export)
  /app/leads/[id]                          lead detail (transcript + side panels)
    ?panel=profile                         default
    ?panel=trace&message=<id>              trace viewer
    ?panel=kb&document=<id>                cited document
  /app/campaigns                           list
  /app/campaigns/new                       wizard
  /app/campaigns/[id]                      progress
  /app/analytics                           funnel + agent quality + nurture cards
  /app/settings                            admin only
    /app/settings/organization
    /app/settings/whatsapp
    /app/settings/channels                 (Telegram, future SMS/IG)
    /app/settings/team
    /app/settings/courses
    /app/settings/knowledge
    /app/settings/nurture
    /app/settings/agent                    tone/personality, guardrails toggles
    /app/settings/prompts                  prompt versioning + A/B
    /app/settings/integrations             calendar, outbound webhooks
    /app/settings/billing                  Stripe portal
    /app/settings/api-keys                 (stub, post-v1)
    /app/settings/audit                    audit log viewer
    /app/settings/danger                   export all data, delete org
```

### 13.2 Lead detail page

The single most-used screen. Layout:

```
┌───────────────────────────────────────────────────────────────────────────┐
│ Rohan Sharma · +91 9XXX · WhatsApp · Hinglish                             │
│ Course: B.Tech CSE · Mode: offline-Pune · Timeline: this year · Score: 78 │
│ Status: qualified · Assigned: — · [Take over] [Assign to me] [Mark cold]  │
│ Handover summary (auto-generated):                                        │
│   "Rohan, 12th science, 78%, wants B.Tech CSE this year offline in Pune.  │
│    Hesitant about fees. Best time: weekday evenings."                     │
├───────────────────────┬───────────────────────────────────────────────────┤
│                       │                                                   │
│  TRANSCRIPT (live)    │  SIDE PANEL                                       │
│  ...                  │   Tabs: Profile · Trace · KB · Notes · Bookings   │
│  lead: voice [audio]  │                                                   │
│       transcribed:    │   Trace tab (when message selected):              │
│       "fees kya hai"  │     • Model: gpt-4o-mini (router: routine)        │
│  agent: "B.Tech CSE   │     • Prompt: qualification.system.v3 (75% split) │
│   is ₹2.4L/year [cite │     • Tools called:                               │
│   Prospectus p.14]"   │         lookup_course(query="b.tech")             │
│  🔔 handover_to_human │           → 1 match: B.Tech CSE                   │
│  ...                  │         save_lead_field(field="course_interest")  │
│                       │     • Tokens in/out: 824 / 162                    │
│                       │     • Latency: 1.21s · Cost: $0.0014              │
│                       │     • [Open in Langfuse]                          │
│                       │                                                   │
│  [textarea]           │                                                   │
│  ✅ Free reply OK     │                                                   │
│  [Send] [Template ▾]  │                                                   │
└───────────────────────┴───────────────────────────────────────────────────┘
```

The trace viewer is the show-stopper feature. Clicking any agent message expands the side panel into a stepper that walks through the model's reasoning. Each step is collapsible. Tool results are JSON-pretty-printed. RAG hits show the chunk text with similarity score.

### 13.3 Live takeover semantics

The "Take over" button does three things atomically (transaction):

1. `UPDATE conversations SET mode='human' WHERE id=$1`
2. `INSERT messages (sender='system', content_text='Counsellor has joined the conversation.')`
3. `audit_log INSERT`

A Redis pubsub event tells all connected dashboard clients to update the UI. Any in-flight agent run for that conversation re-reads `mode` before sending; if `human`, the planned reply is discarded.

To re-enable the agent, an admin clicks "Return to agent". A system message records the handback.

### 13.4 Realtime WebSocket protocol

```
client → server (on connect)
  { type: 'subscribe', auth_token: '<jwt>', topics: ['conversation:<id>'] }

server → client (events)
  { type: 'message_new',         conversation_id, message: {...} }
  { type: 'message_status',      message_id, status, channel_message_id }
  { type: 'lead_updated',        lead: {...} }
  { type: 'mode_changed',        conversation_id, mode }
  { type: 'trace_ready',         conversation_id, message_id, trace_id }
  { type: 'campaign_progress',   campaign_id, sent, delivered, failed }

client → server (counsellor typing)
  { type: 'typing', conversation_id, is_typing: true }
```

Heartbeats every 30s. Reconnect with exponential backoff. The dashboard maintains a local optimistic store and reconciles on each event.

---

## 14. Admin and onboarding

### 14.1 Self-serve signup wizard

```
Step 0  /signup            email + org name → magic link
Step 1  /onboarding/welcome  "Here's what we'll set up."
Step 2  /onboarding/channel
          Choose channel: WhatsApp (recommended) or Telegram (free for testing)
          WhatsApp: paste phone_number_id, WABA id, system user access token, app secret
          Server calls Meta GET /{phone_number_id} to validate.
          Server self-registers webhook URL with Meta.
Step 3  /onboarding/courses
          Quick-add table: name, fees, duration. Skip allowed.
Step 4  /onboarding/knowledge
          Drag-drop a brochure or paste FAQ. Skip allowed.
Step 5  /onboarding/team
          Invite counsellors by email. Skip allowed.
Step 6  /onboarding/test
          A "test message" form sends a fabricated webhook payload through the system.
          User watches the agent reply in real time.
          Confetti on success.
Step 7  /app                 → dashboard live.
```

Required steps: signup + channel connect. Everything else is skippable but flagged on the dashboard until completed.

### 14.2 Demo sandbox

Public visitors at `/demo` get a temporary org provisioned in 5 seconds: pre-seeded with two example courses (B.Tech CSE, MBA), one uploaded brochure, the default agent. They chat with the agent through a web-embedded WhatsApp simulator (same agent backend, different channel adapter: `web_demo`). The dashboard side-by-side shows their conversation appearing in real time, with the trace viewer enabled.

Sandbox orgs are tagged `is_demo = true` and hard-deleted by a daily job after 24 hours. They cannot connect a real WhatsApp number or upgrade to a paid plan.

This is the single highest-conversion thing in the project. It is also a demonstration of the multi-tenancy plumbing — anyone can be an org, instantly, isolated.

---

## 15. Outbound campaigns

### 15.1 Create flow

```
Step 1  Upload CSV (drag-drop, up to 10k rows)
          Required column: phone (E.164 or 10-digit, auto-normalised)
          Optional: name, course_hint, custom_<n>
Step 2  Server validates: parses with pandas, drops malformed rows, dedupes
        against leads where (org_id, channel_account_id, phone) already exists.
        Result: "9,810 valid, 138 duplicates skipped, 52 invalid (download list)".
Step 3  Pick template from wa_templates where status='approved'.
Step 4  Map CSV columns to template variables ({{1}}, {{2}}, ...).
Step 5  Live preview: rendered message for first 3 rows.
Step 6  Optional dry-run: send to admin's own phone only.
Step 7  Schedule:
          Send now  |  Send at <datetime>
          Rate cap: respects Meta tier; cannot be overridden upward.
Step 8  Launch → outbound_campaigns row created, recipients inserted in bulk.
```

### 15.2 Send execution

Worker `outbound.campaign_send` claims a batch of `outbound_campaign_recipients` rows, sends each through the channel adapter, updates row status, and emits a campaign_progress pubsub event every 50 sends. Pauses on rate-limit-exhausted; resumes on token-bucket refill. Marks the campaign `done` when no `pending` rows remain.

### 15.3 Reply handling

When a recipient replies, the normal inbound webhook flow takes over. The existing lead row (created at campaign launch) is updated with `last_inbound_at`, the agent engages, and the standard nurture sequence kicks in. Campaign attribution is preserved on `leads.source_meta.campaign_id`.

---

## 16. Analytics

### 16.1 The fixed analytics page

A single `/app/analytics` page presents three card groups, each computed from materialised views refreshed every 5 minutes by a Celery beat job.

**Funnel card** — leads created → engaged → qualified → handover → customer. Counts, percentages, sparkline for last 30 days, dropdown to switch window (7d / 30d / 90d).

**Agent quality card** — avg turns to qualify, avg cost per qualified lead, percent of conversations completed on `gpt-4o-mini` (routing wins), handover precision (counsellor-marked correct vs. incorrect), evals pass rate trend.

**Nurture card** — cold leads re-engaged by nurture (rolling), avg revival latency, drop-off by step (how many leads survive each step).

Breakdowns: by source (inbound vs outbound), by course (top 5 + Other), by language (EN / HI / Hinglish), by counsellor.

### 16.2 Export

Every leads list view has a CSV / XLSX export. The export respects current filters and runs as a background job, emailing the user a signed download link when ready (avoids long-running HTTP responses).

### 16.3 Shareable read-only links

Org admins can mint a read-only public link to the analytics page (e.g. for sharing weekly KPI snapshots with leadership). Links can be revoked. They carry a token that grants temporary access to a sanitised view of the analytics endpoint with no PII.

---

## 17. Resume-grade enhancements

Each of these is a separate, demonstrable feature that signals production-grade engineering. They are baked into the design, not bolted on.

### 17.1 Pluggable channel adapters

Already in §9. We ship WhatsApp + Telegram + the web demo adapter. SMS (Twilio) and Instagram DM are designed-for; the interfaces are stable. Adding a new channel is a single file in `apps/api/channels/` plus a settings UI tweak.

### 17.2 Conversation trace viewer

Already in §13.2. Per-message replay with model, prompt version, tool calls, RAG hits, tokens, latency, cost, and a deep link into Langfuse.

### 17.3 Langfuse observability

Self-hosted via docker-compose, included in the dev stack. Every agent turn writes a Langfuse trace with nested spans for LLM calls, tool calls, and RAG. The platform admin can browse production traces, build evaluation datasets from real conversations, and run offline scoring.

### 17.4 Prompt versioning and A/B testing

`prompt_versions` rows are immutable. Activating a new version means setting `is_active = true` and assigning a `traffic_percent`. The agent.run task chooses a version per conversation by hashing `(conversation_id, prompt_name)` and using the result modulo 100 against cumulative traffic percents — so a given conversation always gets the same version, but population-level splits are honored.

Conversion rate (`qualified / engaged`) per version is computed nightly. The settings UI shows side-by-side comparisons and a "Promote winner" button that flips traffic to 100% on the better version.

### 17.5 Multi-language with auto-detect

Per-message language detection uses a cheap LLM call on the first turn (`detect_language`) and is cached on the lead. The system prompt instructs the agent to mirror the lead's language. Hinglish is treated as a first-class language (not "broken English"), with examples in the prompt.

UI strings on the dashboard are i18n-ready via `next-intl`; we ship English UI and plan Hindi later (out of v1).

### 17.6 Voice notes via Whisper

WhatsApp voice notes arrive as media messages. The webhook handler streams the media to R2, then a `agent.transcribe_voice` Celery task downloads the audio (OGG/Opus), transcribes with OpenAI Whisper, stores `messages.audio_transcript`, and re-emits a synthetic text message into the agent loop. The dashboard's chat view shows both: an audio player and the transcript with a "transcribed by Whisper" badge.

### 17.7 Auto-generated handover summary

On `handover_to_human`, a second LLM call (always `gpt-4o`, max 150 output tokens) produces a 3-sentence summary capturing collected fields, the lead's mood, and the best-time-to-call signal. Stored on `leads.handover_summary`. Surfaced on the lead card header.

### 17.8 Calendar-integrated callback booking

Counsellors connect Google Calendar via OAuth in settings. Tokens stored encrypted on `users.google_calendar_token`. The agent's `propose_callback_slots` tool queries free/busy across assigned (or eligible) counsellors and returns three slots; the agent sends them as a WhatsApp interactive list message ("Pick a time"). On lead selection, `book_callback` creates a Google Calendar event with a Google Meet link, sends the lead a confirmation, and writes a `calendar_bookings` row. Counsellor receives a native calendar invite. Cancellations from the calendar fire back to the agent via webhook (Google push notifications) and update the booking row.

### 17.9 Outbound webhooks

`webhook_subscriptions` per org. Events: `lead.created`, `lead.qualified`, `lead.handover`, `lead.customer`, `lead.cold`, `conversation.takeover`, `booking.created`. Payloads include a `signature` header (HMAC-SHA256 with shared secret) and an event id for idempotency. Failed deliveries retry with exponential backoff for 24 hours (`webhook_deliveries` log each attempt). Admins can replay a delivery from the audit UI.

### 17.10 Sentiment and objection detection

A per-inbound-message classifier (cheap LLM call) tags the message with zero or more labels from a fixed taxonomy: `angry`, `confused`, `fee_objection`, `comparing_competitor`, `urgent`, `ready_to_buy`, `compliance_concern`. Tags appear inline in the dashboard chat view and feed:

- An "at-risk" filter on the leads list ("show me leads with any negative sentiment in the last 24h").
- The router (escalates to `gpt-4o` on negative sentiment).
- An optional Slack notification per org.

### 17.11 Demo sandbox on the public site

Already in §14.2. The single most important conversion feature on the marketing site.

### 17.12 Public marketing site, API docs, status page

- `/` Next.js marketing page with hero, demo embed, feature grid, pricing, testimonials (curated from real beta feedback or staged for v1).
- `/api-docs` Redoc rendering of the auto-generated OpenAPI spec from FastAPI.
- `status.campusconnect.dev` static page driven by a GitHub Action that probes `/healthz` from three regions every 5 minutes and writes results to a JSON file in a `gh-pages` branch. Zero SaaS dependency.

### 17.13 Stripe billing

Three plans (`Free`, `Growth`, `Enterprise`). Stripe Checkout for upgrades, Customer Portal for downgrade/cancel. Usage meter (`leads_created` in the current period) updated on every lead creation. Soft-block at 110% with an in-app upgrade nudge; hard-block at 200% with email + dashboard banner.

### 17.14 DPDP / GDPR data tools

- Lead can type "DELETE MY DATA" (English or Hindi variants); agent triggers a 30-day soft delete and acknowledges in the conversation. After 30 days, a cron hard-deletes.
- Org admin can export all org data as a zip from `/app/settings/danger`.
- Org admin can hard-delete the org (cascades to all tenanted tables).
- PII redaction filter applied to Sentry events and to application logs (phone numbers and emails are hashed in logs by default).

### 17.15 End-to-end + load testing

- Playwright suite covering: signup, channel connect (mocked Meta), course CRUD, brochure upload, inbound agent run, handover, counsellor reply, campaign upload + send (mocked channel), data export.
- k6 script in `tests/load/webhook.k6.js`: 100 RPS sustained against the webhook endpoint for 5 minutes, asserts p99 < 500ms ack and no dropped messages.
- Both run in CI as separate jobs; e2e on every PR, load weekly + on demand.

### 17.16 Production runbook and post-mortems

- `docs/runbook.md`: on-call playbooks ("Meta is rate-limiting → bump tier or pause outbound", "OpenAI 5xx surge → drain queue and switch to backup provider stub", "Agent looping → enable trace + inspect tool chain", "Postgres bloat → run vacuum analyze on `messages`").
- `docs/architecture.md`: the diagrams from this spec, kept in sync as the system evolves.
- `docs/post-mortems/2026-01-15-meta-token-expired.md`: a single illustrative post-mortem written in the style of a real incident report. Treats the project like a real product. Optional but high signal.

### 17.17 The README that sells the work

- One-paragraph hero with one screenshot of the trace viewer.
- 90-second Loom video, no edits, recorded end-to-end.
- Architecture diagram.
- "What I built and why" section, naming the hard parts:
  - Multi-tenant SaaS with three-layer isolation (API + ORM + Postgres RLS)
  - LLM agent with function-calling, model routing, and per-message trace replay
  - Prompt versioning + A/B testing infrastructure with conversion-rate analytics
  - Channel-agnostic core, demonstrated on WhatsApp and Telegram
  - RAG with citations, voice-note transcription, multilingual support
  - Live takeover with race-free agent-to-human handoff
  - Production-grade SaaS plumbing: Stripe billing, outbound webhooks, DPDP tooling, runbooks
- Live demo and sandbox links.
- Metrics from real demo runs ("X conversations, Y% qualification, $Z cost per qualified lead").
- "What I'd do next" — capacity planning, vector DB migration, multi-region, fine-tuning.

The README is the resume entry for this project. Most readers stop there. We write it like that's the only deliverable.

---

## 18. Cross-cutting concerns

### 18.1 Secrets

All secrets (Meta tokens, OpenAI key, Stripe keys, Google OAuth client secret, encrypted column keys) flow from environment variables in deploy targets. No secret is ever committed. Per-org channel access tokens live in `channel_accounts.secrets` encrypted with `pgcrypto` `pgp_sym_encrypt` using a key derived from a master env-var-supplied passphrase + per-org salt. Keys rotate via a documented runbook procedure.

### 18.2 Auth and authorization

- NextAuth issues a JWT containing `sub` (user id), `org_id`, `role`, and `email_verified`.
- FastAPI middleware verifies the JWT, sets request state, sets the Postgres session var.
- Authorization checks happen at the API layer via FastAPI dependencies: `require_role('org_admin')`, `require_lead_access(lead_id)`.
- UI hides controls the user cannot use, but never relies on UI hiding for security.

### 18.3 Rate limiting

- API-wide: 60 RPS per IP, 600 RPS per org (Redis token bucket).
- Webhook: no rate limit (we are receiving from Meta; they call the shots).
- Outbound to channels: per `channel_account_id` Meta-tier-matched bucket.
- OpenAI calls: per-org daily token budget (default 500k/day in production, 50k/day in dev).

### 18.4 Idempotency

- Webhook handlers dedupe on `channel_message_id` — Meta retries; we must accept gracefully.
- Outbound sends carry an idempotency key per recipient; replays do not double-send.
- Stripe webhooks idempotent on `event.id`.

### 18.5 Backups and disaster recovery

- Neon's point-in-time recovery for 7 days.
- Nightly logical dump to R2 with 30-day retention.
- Weekly backup verification (restore to a scratch DB, run smoke tests, alert on failure).
- Runbook entry: "lost the primary DB" — RTO 30 min, RPO 5 min.

### 18.6 Logging and tracing

- Structured logs (JSON) with `org_id`, `request_id`, `conversation_id`, `user_id` correlation fields.
- OpenTelemetry tracing for HTTP requests, Celery tasks, DB queries.
- Sentry for errors with PII scrubbing.
- Langfuse for LLM-specific traces.

### 18.7 Security hygiene

- All public traffic on HTTPS. HSTS preload.
- CSP, X-Frame-Options, X-Content-Type-Options headers via Next.js + FastAPI middleware.
- CSRF protection on cookie-auth routes (mainly Stripe webhook receiver).
- Dependabot enabled.
- `gitleaks` in pre-commit hook (project setting).
- Per-row `messages.error_code` and audit log entries for unauthorized attempts.

---

## 19. Phased delivery plan

The user has explicitly de-emphasised timeline. Phases below define **logical milestones**, not calendar weeks. Each phase ends with a tagged git release and a recorded demo video. Within a phase, work is broken into the implementation plan produced separately by the planning skill.

### Phase M0 — Foundations

Skeleton that proves the stack works end-to-end. No product features.

- Monorepo layout: `apps/api`, `apps/web`, `apps/worker`, `apps/beat`, `packages/shared`, `infra/`, `tests/`, `docs/`.
- Docker Compose stack: Postgres + pgvector, Redis, Langfuse, mailhog, S3 emulator.
- Alembic migrations: `organizations`, `users`, `audit_log`, `plans` (seed three plans).
- Postgres RLS policies + `TenantedMixin` ORM auto-filter.
- FastAPI `/healthz`, `/readyz`, `/metrics` (Prometheus format).
- Next.js shell with NextAuth magic-link login, protected `/app`.
- Celery worker, beat, and a `hello_world` task wired end-to-end.
- CI: lint, type-check, unit tests, build. Preview deploy on PR.
- Sentry + OpenTelemetry wired in both apps.
- `docs/architecture.md` skeleton.

Demoable end state: sign up with email, log in, see empty dashboard, view request trace in OTel.

### Phase M1 — Channel layer and inbound conversations

Lead messages an institute, the message appears live on the dashboard. No agent yet — a human counsellor replies.

- `channel_accounts`, `leads`, `conversations`, `messages` tables + RLS.
- `ChannelAdapter` interface and WhatsApp adapter.
- Webhook endpoint with signature verification and org resolution.
- `channel.send` Celery task with retry and 24h-window enforcement.
- Dashboard inbox view, lead list, lead detail with transcript.
- WebSocket fan-out for `message_new` and `message_status`.
- Manual reply textarea (counsellor types, message goes out).
- Settings UI to connect a WhatsApp Business number.
- Playwright test: connect channel, simulate inbound, see message, reply, verify outbound.
- `docs/runbook.md` first entries.

Demoable end state: real WhatsApp message → live dashboard → manual reply → received on phone.

### Phase M2 — Telegram adapter

Prove the channel abstraction by adding a second adapter.

- `apps/api/channels/telegram.py` implementation.
- Settings UI variant for connecting a Telegram bot.
- All existing flows work on Telegram with zero changes to higher layers.

Demoable end state: same dashboard handles a Telegram chat and a WhatsApp chat side-by-side.

### Phase M3 — The agent

LLM takes over.

- `courses` CRUD in settings, seed data.
- Agent loop in worker, with advisory lock per conversation.
- Tool dispatcher and core tools: `save_lead_field`, `lookup_course`, `handover_to_human`, `mark_not_interested`, `set_language_preference`.
- Model router (mini default, 4o escalation).
- `prompt_versions` table; seed `qualification.system.v1`.
- `agent_traces` table; trace viewer in dashboard (basic).
- Eval harness with starter scenarios; CI gate.
- Dashboard funnel widget (read-only).

Demoable end state: real lead converses with the agent, gets qualified, agent hands over, counsellor takes over.

### Phase M4 — RAG knowledge layer

Agent answers from uploaded docs with citations.

- `knowledge_documents`, `knowledge_chunks` tables.
- `/app/settings/knowledge` upload UI (PDF + URL + paste text).
- `rag.ingest_doc` task with pdfplumber + chunking + batched embeddings.
- `lookup_kb` tool with similarity threshold and `{"hits": [], "advice": ...}` fallback.
- Citation chips in the dashboard chat view.
- 3 new evals: RAG hit, RAG miss, citation correctness.

Demoable end state: upload brochure, lead asks about hostel fees, agent quotes the right number with a citation.

### Phase M5 — Voice notes, multilingual, sentiment

The agent stops feeling like a demo.

- Whisper-driven voice-note transcription pipeline.
- Language detection + Hinglish prompt examples.
- Sentiment tagger + dashboard tag rendering + router escalation hook.
- Auto-generated handover summary.

Demoable end state: lead sends a Hinglish voice note about fees, agent transcribes, answers in Hinglish with citation, sentiment tag flags hesitation, summary appears on the counsellor's lead card.

### Phase M6 — Nurture sequences

Re-engagement.

- `nurture_sequences`, `nurture_jobs` tables.
- Drag-drop sequence editor in settings.
- Celery Beat `nurture.tick`.
- Template message support (per-org `wa_templates` sync; daily job).
- Cancellation rules end-to-end.

Demoable end state: silent lead receives a 24h follow-up template; reply restarts the agent flow; qualified lead's nurture cancels.

### Phase M7 — Outbound campaigns

The other half of the funnel.

- `outbound_campaigns`, `outbound_campaign_recipients` tables.
- CSV upload wizard with dedup + template mapping + dry-run.
- Rate-limited send worker.
- Campaign progress UI.

Demoable end state: upload 800-row CSV, launch, watch sends rate-limit, recipient replies, enters agent flow.

### Phase M8 — Calendar bookings

Cross-system integration.

- Google Calendar OAuth in settings.
- `propose_callback_slots`, `book_callback` tools.
- WhatsApp interactive list message for slot selection.
- `calendar_bookings` table and Google Calendar push notifications listener.

Demoable end state: agent offers three slots, lead picks one in WhatsApp UI, calendar event created with Meet link, counsellor receives invite.

### Phase M9 — Prompt A/B testing and observability deepening

Make agent quality measurable.

- Prompt version traffic splits.
- Per-version conversion-rate computation (nightly job).
- Settings UI: side-by-side comparison and "Promote winner".
- Langfuse fully integrated; trace viewer deep-links into Langfuse.
- Datasets built from real conversations for offline scoring.

Demoable end state: two prompt versions in production at 50/50, side-by-side conversion rates, promote one with one click.

### Phase M10 — Outbound webhooks and CRM-integration

Real-world plumbing.

- `webhook_subscriptions`, `webhook_deliveries` tables.
- Settings UI for webhook configuration.
- HMAC-signed delivery with retry.
- Replay UI.

Demoable end state: receive webhook in a public Pipedream URL with a verified signature when a lead qualifies.

### Phase M11 — Billing, demo sandbox, marketing site, status page

The polish that makes the project look finished.

- Stripe Checkout + Customer Portal.
- Usage metering and soft/hard blocks.
- `/demo` sandbox auto-provisioner with `web_demo` channel adapter.
- Public marketing site at `/`.
- Status page at `status.campusconnect.dev`.
- `/api-docs` with Redoc.

Demoable end state: visitor lands on marketing site, clicks "Try the demo", chats with the agent, sees the dashboard live in another tab, then signs up and is on a Free plan.

### Phase M12 — Compliance, load tests, runbooks

Production-grade signal.

- Lead-initiated "DELETE MY DATA" flow.
- Org-level export + delete.
- PII redaction in logs.
- k6 load test against webhook hot path.
- Disaster recovery rehearsal.
- Final runbook + one fake post-mortem.

Demoable end state: load test passes, "delete my data" works, backups verified, runbook complete.

### Phase M13 — README, video, polish

The deliverable.

- 90-second Loom walkthrough.
- README with hero, screenshots, architecture diagram, "what I built and why", metrics, "what I'd do next".
- Tag `v1.0.0`.

Demoable end state: the GitHub repo is the resume entry.

---

## 20. Risks and open questions

### 20.1 Identified risks

| Risk | Likelihood | Mitigation |
| --- | --- | --- |
| Meta template approval is slow or opaque | High | Submit `welcome`, `followup_24h`, `followup_3d`, `followup_7d` templates as soon as M1 starts. Test outbound on the existing approved templates until then. |
| Agent hallucinates fees, dates, or scholarships | High without guardrails | Hard rule in system prompt + `eval_no_hallucinated_fees` blocks merge on regression. Use `lookup_course` / `lookup_kb` results verbatim. |
| Race between agent reply and counsellor takeover | Medium | Conversation advisory lock + re-read of `conversations.mode` immediately before send; drop the reply if mode flipped. |
| 24h-window violations send free-form outside window | High in production | Encoded once in adapter's `can_send_freeform`; every send path uses it. Dashboard banner makes state visible. |
| pgvector performance at scale | Low at portfolio scale | ivfflat with `lists=100` initially. Document migration path to HNSW. |
| OpenAI cost runaway | Medium | Per-org daily token budget enforced before calls. Dev default 50k/day. |
| Demo sandbox abused for spam | Medium | No real channel connection allowed in sandbox; rate limits; 24h hard delete; CAPTCHA on `/demo` if needed. |
| Whisper mis-transcribes Hinglish voice notes | Medium | Always store original audio; let counsellor verify on takeover. |
| Stripe webhook race conditions (subscription state) | Low | Idempotent on `event.id`; re-sync state from Stripe on every webhook. |
| Calendar OAuth tokens expire | Medium | Refresh-token flow; alert org admin on permanent failure. |

### 20.2 Open questions to validate during M0–M1

1. Does the user's existing WABA support the Cloud API directly, or is it on the older On-Premise API? (Answer determines exact webhook payload shape and template send endpoint.)
2. Which Meta tier does the user's WABA start at? (1k / 10k / 100k / unlimited — affects rate-limit testing.)
3. Where does the marketing-site domain (`campusconnect.dev`) get registered, and does the user want to use that name? (Trivial but commit-blocking when we wire DNS.)
4. Does the user have a Google Cloud project for Calendar OAuth? (Two-click setup; worth confirming before M8.)
5. Stripe account — exists, can the user create one in their name? (Required for M11.)

---

## 21. Success metrics

What we will measure to call v1 successful — both for the user's resume narrative and for any institute that runs the system.

### 21.1 Engineering quality

- Test coverage: backend ≥ 75% line, frontend ≥ 60% line.
- All evals in CI passing at every tagged release.
- p99 webhook ack < 500ms under 100 RPS load.
- p95 agent reply latency < 8s end-to-end.
- Zero critical Sentry errors in the 7 days before a release tag.
- Multi-tenant isolation: zero RLS escapes in pen-test (manual SQL injection attempts via API).

### 21.2 Product behaviour (target on the live demo with seed data)

- Qualification rate: of leads that reach 2+ inbound messages, ≥ 50% reach `qualified` status.
- Avg cost per qualified lead: ≤ $0.15 across 100 demo conversations.
- Hinglish conversation success: agent collects all 5 fields in ≥ 80% of Hinglish test conversations.
- Voice note transcription accuracy (manual sample of 20): ≥ 90% intent preservation.

### 21.3 Resume narrative

- README + Loom video together can be consumed in 3 minutes and leave a reader saying "this is real".
- A senior engineer skimming the repo can name three non-trivial engineering decisions without asking.
- The demo sandbox has been opened by recruiters and at least once led to a callback (the only metric that actually matters).

---

## Appendix A — Agent tool catalogue

Each tool is a Python function with a Pydantic args schema, registered with the dispatcher. The schemas are auto-converted to OpenAI's `tools` JSON schema — single source of truth.

| Tool | Args | Returns | Side effects |
| --- | --- | --- | --- |
| `save_lead_field` | `field: Literal['name','course_interest','eligibility','intent_timeline','mode_preference','city','email']`, `value: str` | `{ok: bool, normalized: str}` | UPDATE `leads`, INSERT `audit_log` |
| `lookup_course` | `query: str`, `top_k: int = 5` | `[{id, name, fees_inr, eligibility, mode, duration_months}]` | none |
| `lookup_kb` | `query: str`, `k: int = 4` | `{hits: [{content, document_title, similarity}], advice?: str}` | none |
| `send_brochure` | `course_id: UUID` | `{ok: bool, message_id: UUID}` | enqueue `channel.send` with document |
| `propose_callback_slots` | `preferred_window: Literal['morning','afternoon','evening']?` | `[{start: iso8601, end: iso8601, counsellor_id, counsellor_name}]` | reads Google Calendar free/busy |
| `book_callback` | `slot: {start, end, counsellor_id}` | `{ok: bool, booking_id: UUID, meet_link: str}` | creates calendar event, INSERT `calendar_bookings`, sends confirmation |
| `handover_to_human` | `reason: str`, `summary_hint: str?` | `{ok: bool}` | UPDATE `leads.status='qualified'`, `conversations.mode='human'`, triggers handover-summary job, fires `lead.handover` webhook |
| `mark_not_interested` | `reason: Literal['fee','distance','course_fit','timing','other']`, `note: str?` | `{ok: bool}` | UPDATE `leads.status='cold'`, cancel nurture jobs |
| `set_language_preference` | `lang: Literal['en','hi','hinglish']` | `{ok: bool}` | UPDATE `leads.language` and `conversations.current_state` |
| `request_data_deletion` | `confirm: Literal[true]` | `{ok: bool, deletion_at: iso8601}` | Initiates DPDP soft-delete (30-day window), cancels nurture, fires `lead.deletion_requested` webhook, sends confirmation message |

Each tool validates its args against the Pydantic schema before execution. Validation failures return `{error: ..., suggestion: ...}` to the model, which is taught (by examples in the system prompt) to handle them gracefully — e.g., re-prompt the lead for a clearer answer.

---

## Appendix B — Prompt template structure

The active platform-default system prompt at v1 launch (illustrative; final wording lives in `apps/api/agent/prompts/qualification.system.v1.j2`):

```jinja
You are CampusConnect, the admissions assistant for {{ org.name }}.
Today is {{ today.iso }} (IST). The lead is on {{ conversation.channel_type }}.

PERSONALITY
Warm, concise, professional. Match the lead's language: {{ lead.language | language_label }}.
For Hinglish: keep it natural ("Aap kis course me interested ho?"), not formal Hindi.

MISSION
Collect five fields about the lead, in any order that flows naturally:
  1. Name
  2. Course interest
  3. Current education / eligibility
  4. Intent timeline (when they want to join)
  5. Mode preference (online/offline) and city

Already collected: {{ state.collected_fields | json }}
Still missing: {{ state.missing_fields | json }}

WHEN THE LEAD ASKS A QUESTION
Use tools. Specifically:
  - For fee, duration, eligibility, or syllabus questions: call `lookup_course`.
  - For any other factual question about the institute (hostel, placements, scholarships,
    transport, holidays, refund policy, etc.): call `lookup_kb`.
  - Never state a number, date, or rule that did not come from a tool result.
  - If `lookup_kb` returns no good match, say so honestly and offer human handover.

WHEN TO HAND OVER
Call `handover_to_human` when:
  - All five fields are collected.
  - The lead explicitly asks for a counsellor.
  - The lead is angry, confused after two attempts, or comparing competitors.
  - You are about to lie or guess (refuse and hand over instead).

GUARDRAILS
  - Never promise admission, seat reservation, or discount.
  - Never share another lead's info or any internal data.
  - If the lead types "DELETE MY DATA" (or equivalent in Hindi/Hinglish), call `request_data_deletion`.
  - If the lead is a minor under 13 (mentions), pivot to ask for parent's WhatsApp.

OUTPUT
After tool calls, reply with one message, max 3 sentences. End with one clear question
that advances the conversation — unless you just handed over, in which case acknowledge
that a counsellor will reach out and stop.
```

The template is parsed once at startup, cached, and re-rendered per turn with current variables.

---

## Appendix C — REST API surface (selected)

Auto-generated from FastAPI; this is the public-facing slice.

```
Auth
  POST   /api/v1/auth/magic-link
  POST   /api/v1/auth/verify
  POST   /api/v1/auth/logout

Orgs and users
  POST   /api/v1/orgs                       (create org during signup)
  GET    /api/v1/orgs/current
  PATCH  /api/v1/orgs/current
  POST   /api/v1/orgs/current/invite
  GET    /api/v1/users
  PATCH  /api/v1/users/{user_id}

Channels
  POST   /api/v1/channels                   (connect a new channel)
  GET    /api/v1/channels
  DELETE /api/v1/channels/{id}
  POST   /webhook/{channel_type}/{channel_account_id}     (public; signature-verified)

Leads + conversations
  GET    /api/v1/leads?status=...&assigned_to=...&search=...
  GET    /api/v1/leads/{id}
  PATCH  /api/v1/leads/{id}                 (assign, mark cold, edit fields)
  GET    /api/v1/leads/{id}/messages
  POST   /api/v1/conversations/{id}/takeover
  POST   /api/v1/conversations/{id}/return-to-agent
  POST   /api/v1/conversations/{id}/messages
  GET    /api/v1/leads/{id}/trace?message_id=...
  GET    /api/v1/leads/export               (kicks off CSV/XLSX export)

Courses
  GET    /api/v1/courses
  POST   /api/v1/courses
  PATCH  /api/v1/courses/{id}
  DELETE /api/v1/courses/{id}

Knowledge
  GET    /api/v1/knowledge/documents
  POST   /api/v1/knowledge/documents
  DELETE /api/v1/knowledge/documents/{id}
  POST   /api/v1/knowledge/documents/{id}/reembed

Campaigns
  GET    /api/v1/campaigns
  POST   /api/v1/campaigns                  (create draft)
  POST   /api/v1/campaigns/{id}/dry-run
  POST   /api/v1/campaigns/{id}/launch
  POST   /api/v1/campaigns/{id}/pause
  GET    /api/v1/campaigns/{id}/recipients

Nurture
  GET    /api/v1/nurture/sequences
  PATCH  /api/v1/nurture/sequences/{id}

Prompts
  GET    /api/v1/prompts                    (versions for current org)
  POST   /api/v1/prompts/{name}/versions
  PATCH  /api/v1/prompts/{name}/versions/{id}    (set traffic_percent / activate)
  POST   /api/v1/prompts/{name}/promote-winner

Integrations
  GET    /api/v1/integrations/calendar/auth-url
  POST   /api/v1/integrations/calendar/callback
  GET    /api/v1/integrations/webhooks
  POST   /api/v1/integrations/webhooks
  POST   /api/v1/integrations/webhooks/{id}/replay/{delivery_id}

Billing
  POST   /api/v1/billing/checkout-session
  POST   /api/v1/billing/portal-session
  POST   /webhook/stripe                    (Stripe-signed)

Analytics
  GET    /api/v1/analytics/funnel?window=30d
  GET    /api/v1/analytics/agent-quality?window=30d
  GET    /api/v1/analytics/nurture?window=30d
  POST   /api/v1/analytics/share-link

Admin
  GET    /api/v1/audit-log
  POST   /api/v1/orgs/current/export        (kicks off DPDP export job)
  DELETE /api/v1/orgs/current               (DPDP delete)

WebSocket
  WS     /ws                                (authed; topic subscriptions)
```

---

## Appendix D — Glossary

| Term | Meaning |
| --- | --- |
| WABA | WhatsApp Business Account (Meta's parent object for a business's WhatsApp presence) |
| Cloud API | Meta-hosted WhatsApp Business API (vs. self-hosted On-Premise API) |
| 24h window | Meta's rule that free-form messages may only be sent within 24h of the customer's last inbound message |
| Template message | A Meta-pre-approved message format that can be sent outside the 24h window |
| wamid | A WhatsApp message id returned by the Cloud API |
| RLS | Postgres Row-Level Security |
| Function calling | An LLM feature where the model produces structured tool-invocation requests that the host program executes |
| RAG | Retrieval-Augmented Generation — the pattern of retrieving relevant context from a corpus and including it in the prompt |
| Eval | A scripted test that exercises an LLM's behaviour against assertions, run like a unit test |
| Tier | Meta's outbound messaging rate-limit class (1k/10k/100k/unlimited per 24h) |
| DPDP | India's Digital Personal Data Protection Act (2023) |
| Trace | A structured record of one agent turn: model, prompt, tools, RAG hits, tokens, latency |

---

*End of design specification.*
