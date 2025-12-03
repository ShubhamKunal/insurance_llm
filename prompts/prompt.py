import json
MAX_CHARS_PER_SITE_FOR_AI = 10000

def truncate(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "\n\n[...TRUNCATED...]"

import json

def build_prompt(scraped: dict, am_best_ratings: dict) -> str:
    prepared = {
        domain: truncate(txt, MAX_CHARS_PER_SITE_FOR_AI)
        for domain, txt in scraped.items()
    }
    blob = json.dumps(prepared, indent=2)
    ratings_blob = json.dumps(am_best_ratings, indent=2)

    return f"""
You are an expert in US Commercial Truck Insurance and actuarial/AI-driven pricing optimization.

You will receive:
1) Scraped website text for multiple insurers (JSON: domain -> text).
2) A.M. Best Financial Strength Ratings for each domain (JSON: domain -> rating), extracted from downloaded HTML pages.

Using ONLY that information plus general industry knowledge, produce a **clean, readable, text-only report**
with EXACTLY these three level-3 headings in this exact order and wording:

### 1. Commercial Truck Insurance Coverages and Other Notes
### 2. Market Comparison Report and Pricing Transparency Analysis
### 3. AI-Driven Quote Proposal, Risk Assessment Model, and Key Metrics

---------------------------------------
GLOBAL FORMAT RULES (VERY IMPORTANT)
---------------------------------------
- Do NOT use markdown tables.
- Do NOT use "|" characters anywhere.
- Do NOT use bullets such as "*", "-", or "•".
- Use ONLY numbered lists (1., 2., 3.) and short paragraphs.
- You MAY use markdown **bold** for:
    - Company domain names
    - Key coverage types
  - Industry terms (e.g., **Primary Liability**, **Telematics**, **Predictive Analytics**)
- Keep paragraphs concise (1–4 sentences).
- The output MUST remain clean text, no code blocks.

===========================================================
### 1. Commercial Truck Insurance Coverages and Other Notes
===========================================================
For each insurer (domain), list:

1. **domain.com**
    Primary Liability: …
    Motor Truck Cargo: …
    Physical Damage: …
    Non-Trucking Liability: …
    Trailer Interchange: …
    Financial Strength / A.M. Best: …
    Claim Handling & Customer Satisfaction: …
    Pricing Transparency & Discounts: …
    Other Notes: …

Rules:
- Use the A.M. Best ratings JSON as your PRIMARY source for "Financial Strength / A.M. Best".
    - If a domain has a rating in the JSON, use that exact string.
    - If the rating is "Not Available", say: Not Available.
- For all other fields (coverages, claims, pricing, discounts), base your answers on the scraped website text.
- If scraped text does not provide explicit details, write: Not Specified.
- Any carrier-specific mentions (e.g., safety programs, telematics, fleet tools, specialty trucking focus) should appear in “Other Notes.”
- Each insurer must be a numbered item in order (1., 2., 3., …).
- Keep everything text-only, readable, and structured exactly as shown.

===========================================================
### 2. Market Comparison Report and Pricing Transparency Analysis
===========================================================
Write a **narrative comparison**, containing:

- 5–10 numbered points comparing the insurers on:
    - Coverage availability (Primary Liability, Cargo, Physical Damage, NTL, Trailer Interchange)
    - Financial Strength (A.M. Best ratings from the JSON)
    - Claim handling reputation & customer satisfaction (where text allows)
    - Transparency of pricing, discounts, and telematics/safe-driving programs
    - Market specialization (e.g., trucking-only carriers vs general commercial auto carriers)

- Each numbered point should be 2–4 sentences long.
- Domain names should be bold when referenced (e.g., **gwccnet.com**).
- Explicitly reference higher-rated vs lower/unknown-rated carriers where appropriate (e.g., carriers with strong A or A+ ratings vs "Not Available").

===========================================================
### 3. AI-Driven Quote Proposal, Risk Assessment Model, and Key Metrics
===========================================================
This section must output:

A. **High-level description of how to build an AI-driven rating model**
    - 5–10 numbered points explaining how AI can optimize:
        - Usage-based pricing
        - Risk segmentation
        - Predictive claim frequency/severity models
        - Real-time telematics scoring
        - Integration of HOS compliance, vehicle health, braking/speeding patterns, weather routing, etc.

B. **A detailed proposed competitive quote methodology**
    - Describe how a modern insurer could generate a competitive premium using:
        - Market benchmarks and coverage/strength differences identified in Section 2
        - A.M. Best ratings as a proxy for carrier reliability and capital strength
        - Telematics-driven behavioral risk scores
        - Historical loss data patterns
        - Vehicle type, operation radius, cargo class, fleet size, driver MVR history
        - Maintenance and safety program compliance

C. **Key metrics the AI model should output**
    Provide a numbered list of 10–15 key pricing metrics, such as:
   - **Telematics Safety Score**
   - **Predicted Annual Loss Cost**
   - **Driver Fatigue/HOS Risk Index**
   - **Vehicle Condition Score**
   - **Claim Severity Forecast**
   - **Probability of Large Loss**
   - **Fraud Likelihood Score**
   - **Route Risk Exposure Score**
   - **Weather/Geographic Risk Adjustment**
   - **Fleet Safety Compliance Index**

Rules for this section:
- Only numbered lists and paragraphs.
- No tables.
- Use bold keywords where appropriate (e.g., **Telematics Safety Score**).

---------------------------------------
INPUT JSON – SCRAPED WEBSITE TEXTS
(domain -> text)
---------------------------------------
{blob}

---------------------------------------
INPUT JSON – A.M. BEST RATINGS
(domain -> rating)
---------------------------------------
{ratings_blob}
"""
