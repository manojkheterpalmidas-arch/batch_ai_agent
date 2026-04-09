import streamlit as st
from openai import OpenAI
import requests
import json
import re
import time
import pandas as pd
from datetime import datetime, timezone, timedelta
from urllib.parse import urlparse

def now_gmt2():
    return datetime.now(timezone.utc) + timedelta(hours=2)

# ── PAGE CONFIG ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="MIDAS Batch Lead Scorer", layout="wide", page_icon="📊")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important; background: #ffffff !important; color: #1a1a1a !important; }
.stApp { background: #ffffff !important; }
.stMarkdown, .stMarkdown * { color: #1a1a1a !important; }
[data-testid="stMetricValue"] { color: #1a1a1a !important; }
[data-testid="stMetricLabel"] { color: #6b7280 !important; }
a { color: #2563eb !important; }
a:hover { color: #1d4ed8 !important; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding: 2rem 2.5rem 4rem !important; max-width: 1400px !important; }

/* Buttons — white text */
.stButton > button {
    background: #1a1a1a !important; color: white !important; border: none !important;
    border-radius: 8px !important; font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 13px !important; padding: 10px 24px !important;
    transition: all 0.15s ease !important;
}
.stButton > button:hover { background: #374151 !important; }
.stButton > button > div,
.stButton > button > div > p,
.stButton > button span,
.stButton > button * { color: white !important; }

/* Download buttons */
.stDownloadButton > button {
    background: transparent !important; color: #1a1a1a !important;
    border: 1px solid #e5e7eb !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-weight: 600 !important; font-size: 12px !important;
}
.stDownloadButton > button:hover { background: #f9fafb !important; }
.stDownloadButton > button > div,
.stDownloadButton > button > div > p,
.stDownloadButton > button span,
.stDownloadButton > button * { color: #1a1a1a !important; }

/* Inputs */
.stTextInput > div > div > input, .stTextArea > div > div > textarea {
    background: #ffffff !important; color: #1a1a1a !important;
    border: 1px solid #e5e7eb !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important; padding: 11px 14px !important;
    caret-color: #1a1a1a !important;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
    border-color: #2563eb !important; box-shadow: 0 0 0 3px rgba(37,99,235,0.1) !important;
}
.stTextInput > div > div > input::placeholder, .stTextArea > div > div > textarea::placeholder {
    color: #9ca3af !important;
}

/* Expander — light background so text is visible */
.streamlit-expanderHeader {
    background: #f9fafb !important; border: 1px solid #f3f4f6 !important; border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important; font-size: 14px !important; font-weight: 600 !important;
    color: #1a1a1a !important;
}
.streamlit-expanderHeader p, .streamlit-expanderHeader span,
.streamlit-expanderHeader * { color: #1a1a1a !important; }
[data-testid="stExpander"] details summary { color: #1a1a1a !important; }
[data-testid="stExpander"] details summary * { color: #1a1a1a !important; }

/* Metrics */
[data-testid="metric-container"] {
    background: #ffffff !important; border: 1px solid #f3f4f6 !important;
    border-radius: 10px !important; padding: 16px 20px !important;
}
[data-testid="stMetricValue"] { font-family: 'Inter', sans-serif !important; font-size: 28px !important; font-weight: 700 !important; }
[data-testid="stMetricLabel"] { font-family: 'Inter', sans-serif !important; font-size: 11px !important; letter-spacing: 0.05em !important; text-transform: uppercase !important; }

/* Tabs */
.stTabs [data-baseweb="tab-list"] { background: transparent !important; border-bottom: 1px solid #f3f4f6 !important; }
.stTabs [data-baseweb="tab"] {
    font-family: 'Inter', sans-serif !important; font-size: 13px !important; font-weight: 500 !important;
    color: #9ca3af !important; padding: 10px 20px !important; background: transparent !important;
    border: none !important; border-bottom: 2px solid transparent !important; margin-bottom: -1px !important;
}
.stTabs [aria-selected="true"] { color: #1a1a1a !important; border-bottom-color: #1a1a1a !important; }

/* Progress */
.stProgress > div > div > div { background: #1a1a1a !important; border-radius: 2px !important; }
.stProgress > div > div { background: #f3f4f6 !important; border-radius: 2px !important; }

/* Score badges */
.score-hot  { background: #fef2f2; color: #dc2626; border: 1px solid #fecaca; }
.score-warm { background: #fffbeb; color: #d97706; border: 1px solid #fde68a; }
.score-cold { background: #f9fafb; color: #6b7280; border: 1px solid #e5e7eb; }
.score-badge {
    display: inline-block; font-family: 'Inter', sans-serif; font-weight: 600;
    font-size: 12px; padding: 4px 12px; border-radius: 20px;
}

/* Lead cards */
.lead-card {
    background: #ffffff; border: 1px solid #f3f4f6; border-radius: 10px;
    padding: 20px 24px; margin-bottom: 12px; transition: all 0.15s ease;
}
.lead-card:hover { border-color: #e5e7eb; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }

::-webkit-scrollbar { width: 4px; }
::-webkit-scrollbar-thumb { background: #e5e7eb; border-radius: 2px; }

/* Form submit buttons */
.stApp [data-testid="stFormSubmitButton"] button,
.stApp [data-testid="stFormSubmitButton"] button * { color: white !important; font-family: 'Inter', sans-serif !important; font-weight: 600 !important; }
[data-testid="stFormSubmitButton"] button {
    background: #1a1a1a !important; color: white !important; border: none !important;
    border-radius: 8px !important; font-family: 'Inter', sans-serif !important;
    font-weight: 600 !important; font-size: 13px !important; padding: 10px 24px !important;
}
[data-testid="stFormSubmitButton"] button:hover { background: #374151 !important; }

/* Radio buttons */
.stRadio label { color: #1a1a1a !important; }
.stRadio label span { color: #1a1a1a !important; }
.stRadio label p { color: #1a1a1a !important; }
.stRadio div[role="radiogroup"] label { color: #1a1a1a !important; }
.stRadio div[role="radiogroup"] label * { color: #1a1a1a !important; }

/* Input labels */
.stTextInput label, .stTextInput label * { color: #1a1a1a !important; }
.stTextArea label, .stTextArea label * { color: #1a1a1a !important; }
.stSelectbox label, .stSelectbox label * { color: #1a1a1a !important; }
.stFileUploader label, .stFileUploader label * { color: #1a1a1a !important; }

/* Expander */
[data-testid="stExpander"] { border: 1px solid #f3f4f6 !important; border-radius: 8px !important; }
[data-testid="stExpander"] summary,
[data-testid="stExpander"] summary *,
[data-testid="stExpander"] details > summary > span,
[data-testid="stExpander"] details > summary > span * { color: #1a1a1a !important; background: transparent !important; }
[data-testid="stExpander"] [data-testid="stExpanderDetails"] { background: #ffffff !important; }

/* Force all label/paragraph text visible */
p, span, label, div { color: inherit; }
.stApp p, .stApp label, .stApp span { color: #1a1a1a; }
</style>
""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# CORE FUNCTIONS
# ══════════════════════════════════════════════════════════════════════════════

def extract_domain(url):
    return urlparse(url).netloc.replace("www.", "")

def safe_json(text):
    try:
        cleaned = re.sub(r"```json|```", "", text).strip()
        return json.loads(cleaned)
    except:
        try:
            match = re.search(r'\{.*\}', text, re.DOTALL)
            if match:
                return json.loads(match.group())
        except:
            pass
        return {}

def score_cls(s):
    return {"Hot": "score-hot", "Warm": "score-warm", "Cold": "score-cold"}.get(s, "score-cold")

def score_emoji(s):
    return {"Hot": "🔥", "Warm": "⚡", "Cold": "❄️"}.get(s, "")


# ── SERPAPI SEARCH ────────────────────────────────────────────────────────────
def serp_search(query, api_key, num=10):
    """Single Google search via SerpAPI. Returns list of {title, snippet, link}."""
    try:
        resp = requests.get(
            "https://serpapi.com/search",
            params={"q": query, "api_key": api_key, "num": num, "engine": "google"},
            timeout=15
        )
        data = resp.json()
        results = []
        for r in data.get("organic_results", []):
            results.append({
                "title": r.get("title", ""),
                "snippet": r.get("snippet", ""),
                "link": r.get("link", ""),
            })
        return results
    except:
        return []

def serp_to_text(results):
    """Convert SerpAPI results to a text block for corpus."""
    return "\n".join([f"{r['title']}\n{r['snippet']}\n{r['link']}" for r in results])


# ── FIRECRAWL ─────────────────────────────────────────────────────────────────
def firecrawl_crawl(url, api_key, max_pages=30):
    """Crawl a website with Firecrawl. Returns list of {url, markdown}."""
    try:
        # Try scrape with cookie accept action first
        action_resp = requests.post(
            "https://api.firecrawl.dev/v1/scrape",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "url": url, "formats": ["markdown"],
                "actions": [
                    {"type": "wait", "milliseconds": 2000},
                    {"type": "click", "selector": "button[class*='accept'], button[id*='accept'], button[class*='agree'], button[class*='consent'], .cookie-accept, #cookie-accept, .accept-cookies"},
                    {"type": "wait", "milliseconds": 1000}
                ]
            }, timeout=30
        )
        homepage_md = action_resp.json().get("data", {}).get("markdown", "")

        if homepage_md and len(homepage_md) > 500:
            results = [{"url": url, "markdown": homepage_md}]
            # Now crawl subpages
            try:
                resp = requests.post(
                    "https://api.firecrawl.dev/v1/crawl",
                    headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
                    json={"url": url, "limit": max_pages, "scrapeOptions": {"formats": ["markdown"]}},
                    timeout=30
                )
                job_id = resp.json().get("id")
                if job_id:
                    for _ in range(30):
                        time.sleep(3)
                        poll = requests.get(
                            f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                            headers={"Authorization": f"Bearer {api_key}"}, timeout=15
                        ).json()
                        status = poll.get("status")
                        pages = poll.get("data", [])
                        if status == "completed" or (status == "scraping" and len(pages) >= max_pages - 2):
                            for p in pages:
                                md = p.get("markdown", "")
                                if md.strip() and len(md) > 500:
                                    results.append({"url": p.get("metadata", {}).get("sourceURL", url), "markdown": md})
                            break
                        if status == "failed":
                            break
            except:
                pass
            return results

        # Fallback: normal crawl
        resp = requests.post(
            "https://api.firecrawl.dev/v1/crawl",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"url": url, "limit": max_pages, "scrapeOptions": {"formats": ["markdown"]}},
            timeout=30
        )
        job_id = resp.json().get("id")
        if not job_id:
            return []

        for _ in range(30):
            time.sleep(4)
            poll = requests.get(
                f"https://api.firecrawl.dev/v1/crawl/{job_id}",
                headers={"Authorization": f"Bearer {api_key}"}, timeout=15
            ).json()
            status = poll.get("status")
            pages = poll.get("data", [])
            if status == "completed" or (status == "scraping" and len(pages) >= max_pages - 2):
                return [
                    {"url": p.get("metadata", {}).get("sourceURL", url), "markdown": p.get("markdown", "")}
                    for p in pages if p.get("markdown", "").strip() and len(p.get("markdown", "")) > 500
                ]
            if status == "failed":
                break

        return []
    except:
        return []


def direct_fetch(url, max_subpages=10):
    """Fallback: direct HTTP fetch with priority subpage discovery."""
    try:
        from bs4 import BeautifulSoup
        from urllib.parse import urljoin
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Cookie": "cookielawinfo-checkbox-necessary=yes; cookie_consent=accepted; gdpr=1; euconsent=1"
        }
        resp = requests.get(url, headers=headers, timeout=15)
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript", "iframe"]):
            tag.decompose()
        text = soup.get_text(separator="\n", strip=True)

        results = [{"url": url, "markdown": text}] if len(text) > 500 else []

        domain = urlparse(url).netloc
        visited = {url}
        priority_kw = ["people","team","about","projects","services","careers","expertise","sectors","what-we-do"]
        all_links = []
        for a in soup.find_all("a", href=True):
            full = urljoin(url, a["href"].strip())
            parsed = urlparse(full)
            if parsed.netloc == domain and "#" not in full and full not in visited and not any(full.endswith(e) for e in [".pdf",".jpg",".png",".zip"]):
                all_links.append(full)
                visited.add(full)

        def prio(link):
            lower = link.lower()
            for i, kw in enumerate(priority_kw):
                if kw in lower: return i
            return 999

        for link in sorted(set(all_links), key=prio)[:max_subpages]:
            try:
                sub = requests.get(link, headers=headers, timeout=10)
                sub_soup = BeautifulSoup(sub.text, "html.parser")
                for tag in sub_soup(["script","style","noscript","iframe"]): tag.decompose()
                sub_text = sub_soup.get_text(separator="\n", strip=True)
                if len(sub_text) > 300:
                    results.append({"url": link, "markdown": sub_text})
            except:
                pass
        return results
    except:
        return []


# ── CORPUS BUILDER ────────────────────────────────────────────────────────────
def build_corpus(pages):
    chunks = []
    for p in pages:
        md = p.get("markdown", "").strip()
        if not md: continue
        md = re.sub(r'!\[.*?\]\(.*?\)', '', md)
        md = re.sub(r'\n{3,}', '\n\n', md)
        chunks.append(f"[PAGE: {p.get('url','')}]\n{md[:15000]}")
    return "\n\n---\n\n".join(chunks)[:40000]


# ── SERPAPI ENRICHMENT FUNCTIONS ──────────────────────────────────────────────
def serp_linkedin(company_name, api_key):
    """Search LinkedIn for company info and employee count."""
    results = serp_search(f'site:linkedin.com/company "{company_name}" employees', api_key, num=5)
    text = serp_to_text(results)

    employee_signal = ""
    # Range patterns like "51-200 employees"
    range_matches = re.findall(r'(\d[\d,]*\s*-\s*\d[\d,]*)\s*employees', text.lower())
    if range_matches:
        employee_signal = range_matches[0].replace(" ", "")
    else:
        matches = re.findall(r'(\d[\d,]*)\s*\+?\s*employees', text.lower())
        for m in matches:
            try:
                num = int(m.replace(",", ""))
                if 2 <= num <= 500000:
                    employee_signal = m.replace(",", "")
                    break
            except:
                continue

    return text, employee_signal


def serp_glassdoor(company_name, api_key):
    """Search Glassdoor and Indeed for employer reviews."""
    all_text = ""
    review_count = 0

    r1 = serp_search(f'glassdoor "{company_name}" reviews engineers software employees', api_key, num=5)
    all_text += serp_to_text(r1)
    review_count += len(r1)

    r2 = serp_search(f'"{company_name}" employees size headquarters glassdoor OR linkedin OR indeed', api_key, num=5)
    all_text += "\n" + serp_to_text(r2)

    return all_text[:5000], review_count


def serp_people(company_name, domain, api_key):
    """Search for key people at the company."""
    all_text = ""

    r1 = serp_search(f'site:{domain} team OR engineers OR directors OR people OR staff', api_key, num=10)
    all_text += serp_to_text(r1)

    r2 = serp_search(f'site:linkedin.com/in "{company_name}" engineer OR director OR structural OR bridge OR geotechnical OR FEA', api_key, num=10)
    all_text += "\n" + serp_to_text(r2)

    return all_text[:8000]


def serp_planning(company_name, api_key):
    """Search for planning applications and public projects."""
    results = serp_search(f'"{company_name}" planning application structural engineer', api_key, num=5)
    text = serp_to_text(results)
    return text[:3000], text.lower().count("planning")


def lookup_companies_house(company_name, ch_api_key, locations=None):
    """Companies House API lookup — uses the provided API key directly."""
    try:
        all_text = ""
        director_count = 0

        search_resp = requests.get(
            f"https://api.company-information.service.gov.uk/search/companies?q={company_name.replace(' ', '+')}",
            auth=(ch_api_key, ""),
            timeout=10
        )
        results = search_resp.json().get("items", [])
        if results:
            company_number = results[0].get("company_number", "")
            officers_resp = requests.get(
                f"https://api.company-information.service.gov.uk/company/{company_number}/officers",
                auth=(ch_api_key, ""),
                timeout=10
            )
            officers = officers_resp.json().get("items", [])
            officer_text = "\n".join([
                f"{o.get('name', '')} — {o.get('officer_role', '')} (appointed {o.get('appointed_on', '')})"
                for o in officers if o.get('resigned_on') is None
            ])
            company_info = results[0]
            text = f"""Company: {company_info.get('title', '')}
Status: {company_info.get('company_status', '')}
Type: {company_info.get('company_type', '')}
Incorporated: {company_info.get('date_of_creation', '')}
Address: {company_info.get('registered_office_address', {}).get('address_line_1', '')}

Active Officers:
{officer_text}"""
            director_count = len([o for o in officers if 'director' in o.get('officer_role','').lower()])
            all_text = f"[Companies House UK]\n{text}"

        return all_text[:6000], director_count
    except:
        return "", 0


# ── AI ────────────────────────────────────────────────────────────────────────
def ask_deepseek(system, user, max_tokens=2000, temperature=0.1):
    try:
        client = OpenAI(api_key=st.session_state["deepseek_key"], base_url="https://api.deepseek.com")
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            temperature=temperature, max_tokens=max_tokens
        )
        return resp.choices[0].message.content.strip()
    except Exception as e:
        return "{}"


def analyze_company(corpus):
    return ask_deepseek(
        "You are a B2B sales analyst for MIDAS IT (FEA/FEM software). Extract facts only. Respond in pure JSON, no markdown. Translate ALL content into English. NEVER translate people's names.",
        f"""Return ONLY valid JSON:
{{
  "company_name": "string",
  "tagline": "string or null",
  "locations": ["ONLY cities explicitly stated as offices"],
  "founded": "year or null",
  "employee_count": "string or null",
  "overview": ["bullet 1", "bullet 2", "bullet 3"],
  "engineering_capabilities": ["bullet 1"],
  "project_types": ["bridge"],
  "software_mentioned": ["any FEA/CAD/BIM tools"],
  "people": [{{"name": "Full Name", "role": "Job Title", "tier": "Owner|Founder|Director|Principal|Senior|Engineer|Graduate|Technician|Other"}}],
  "open_roles": [{{"title": "Job title", "skills": ["skill1"], "fem_mentioned": true}}],
  "projects": [{{"name": "Project name", "type": "Bridge|Building|Metro|Infrastructure|Residential|Industrial|Other", "location": "City or null", "client": "Client name or null", "description": "One sentence summary", "fem_relevant": true}}],
  "confidence": "High|Medium|Low",
  "confidence_reason": "One sentence"
}}
Extract ONLY engineering and technical staff.
EXCLUDE blog authors, writers, journalists.
For employee_count: check ALL sources including Glassdoor, LinkedIn, Companies House. Use ranges like "51-200 employees" if found.
Website content:
{corpus}""",
        max_tokens=8000
    )


MIDAS_PRODUCTS = """
MIDAS NX PRODUCT SUITE — FULL SALES KNOWLEDGE BASE

1. MIDAS CIVIL NX — Bridges & Civil Infrastructure
Structural analysis and design for bridges and civil infrastructure. Construction stage simulation, moving load and traffic simulation, design code checking, automation via Excel/API. Covers cable-stayed, suspension, PSC, steel bridges, highway/railway bridges, earthquake response, water treatment, underground structures.

2. MIDAS GEN NX — Buildings & General Structures
Structural analysis and design for buildings. Models RC, steel, composite structures. Static, dynamic, seismic, nonlinear analysis. Automated design optimisation, pushover analysis, Excel/Grasshopper integration. High-rise, residential, commercial, industrial, earthquake-resistant design.

3. MIDAS FEA NX — Detailed Local & Nonlinear Analysis
High-end FEA for detailed local and nonlinear analysis. 2D/3D elements, material nonlinearity, cracking, fatigue, buckling, thermal. CAD import, auto-meshing, parallel computing. Steel connections, anchor zones, bridge joints, deep beams, shear walls, geotechnical details, failure analysis.

4. MIDAS GTS NX — Geotechnical Analysis
Geotechnical FEA for soil, rock, underground problems. Soil-structure interaction, excavation staging, groundwater/seepage, dynamic/seismic. Foundations, metro tunnels, deep excavation, slope stability, dam engineering.

CROSS-SELL LOGIC:
- Bridge/infrastructure firm → CIVIL NX + FEA NX
- Building/structural firm → GEN NX + FEA NX
- Geotechnical/ground firm → GTS NX + CIVIL NX
- Mixed civil firm → CIVIL NX + GEN NX + FEA NX
- Full service → Full suite
- Metro/tunnelling → GTS NX + CIVIL NX

COMPETITIVE:
- vs LUSAS/STAAD/SAP2000 → better automation, modern UI, construction stage analysis
- vs PLAXIS → better BIM integration and CAD workflow
- vs ETABS → more automation and parametric design
- vs ANSYS/ABAQUS → more accessible for civil engineers
- No FEA detected → clean opportunity, position as first professional FEA platform
"""


def analyze_sales(corpus, company_json):
    return ask_deepseek(
        f"You are a senior B2B sales strategist for MIDAS IT. Use the product knowledge below to make specific product recommendations. Be specific and actionable. Respond in pure JSON, no markdown. Always respond in English regardless of the language of the website content.\n\n{MIDAS_PRODUCTS}",
        f"""Return ONLY valid JSON:
{{
  "fem_opportunities": ["detailed specific use case 1 referencing their actual project types", "use case 2", "use case 3"],
  "pain_points": ["specific pain point based on their work", "pain 2", "pain 3"],
  "entry_point": "Specific person name and role to approach first, with detailed reasoning based on their seniority and relevance to FEA/FEM",
  "value_positioning": "Detailed 2-3 sentence positioning of MIDAS specifically for this company's project types and engineering focus",
  "likely_objections": ["specific objection based on their context", "objection 2", "objection 3"],
  "hiring_signals": ["specific signal from their job postings or growth", "signal 2"],
  "expansion_signals": ["specific expansion signal", "signal 2"],
  "pre_meeting_mention": ["specific thing to mention about their actual projects", "thing 2", "thing 3"],
  "smart_questions": ["specific question about their workflow or current tools", "question 2", "question 3"],
  "opening_line": "One strong personalised opening line referencing something specific about their work",
  "overall_score": "Hot|Warm|Cold",
  "score_reason": "2-3 sentence detailed reason for the score based on their specific context",
  "recommended_products": ["list the specific MIDAS products that fit this company from: CIVIL NX, GEN NX, FEA NX, GTS NX"],
  "product_reason": "3-4 sentence explanation of exactly why these specific MIDAS products fit this company based on their project types and engineering capabilities"
}}
Company data: {company_json}
Website excerpt: {corpus[:4000]}""",
        max_tokens=4000
    )


# ══════════════════════════════════════════════════════════════════════════════
# BATCH PROCESSOR
# ══════════════════════════════════════════════════════════════════════════════

def process_single_company(url, firecrawl_key, serp_key, ch_key, status_callback=None):
    """Process one company end-to-end. Returns a result dict."""
    result = {
        "url": url,
        "domain": extract_domain(url),
        "company_name": "",
        "score": "Cold",
        "score_reason": "",
        "employee_count": "—",
        "locations": "",
        "confidence": "Low",
        "people_count": 0,
        "projects_count": 0,
        "fem_opps": 0,
        "pages_crawled": 0,
        "recommended_products": [],
        "product_reason": "",
        "entry_point": "",
        "value_positioning": "",
        "company_data": {},
        "sales_data": {},
        "status": "success",
        "error": "",
    }

    try:
        # Step 1 — Crawl website
        if status_callback: status_callback(f"🔍 Crawling {extract_domain(url)}...")
        pages = firecrawl_crawl(url, firecrawl_key, max_pages=30)

        # Fallback if thin crawl
        real_pages = [p for p in (pages or []) if len(p.get("markdown", "")) > 500]
        if len(real_pages) < 3:
            if status_callback: status_callback(f"🔄 Fallback fetch for {extract_domain(url)}...")
            fallback = direct_fetch(url, max_subpages=10)
            if fallback and any(len(p.get("markdown", "")) > 500 for p in fallback):
                pages = fallback

        if not pages:
            result["status"] = "failed"
            result["error"] = "Could not crawl website"
            return result

        result["pages_crawled"] = len(pages)

        # Step 2 — Build corpus and analyze
        if status_callback: status_callback(f"🧠 Analysing {extract_domain(url)}...")
        corpus = build_corpus(pages)
        company_raw = analyze_company(corpus)
        company_data = safe_json(company_raw)

        company_name = company_data.get("company_name", extract_domain(url))
        domain = extract_domain(url)
        result["company_name"] = company_name

        # Step 3 — Enrich with SerpAPI
        extra_corpus = ""

        if ch_key:
            if status_callback: status_callback(f"📋 Companies House: {company_name}...")
            ch_text, ch_dirs = lookup_companies_house(company_name, ch_key)
            if ch_text:
                extra_corpus += f"\n\n[SOURCE: Companies House]\n{ch_text}"

        if serp_key:
            if status_callback: status_callback(f"💼 LinkedIn: {company_name}...")
            li_text, li_employees = serp_linkedin(company_name, serp_key)
            if li_text:
                extra_corpus += f"\n\n[SOURCE: LinkedIn]\n{li_text}"
            if li_employees and not company_data.get("employee_count"):
                company_data["employee_count"] = str(li_employees)

            if status_callback: status_callback(f"⭐ Glassdoor: {company_name}...")
            gd_text, gd_reviews = serp_glassdoor(company_name, serp_key)
            if gd_text:
                extra_corpus += f"\n\n[SOURCE: Glassdoor]\n{gd_text}"

            if len(company_data.get("people", [])) == 0:
                if status_callback: status_callback(f"👥 People search: {company_name}...")
                people_text = serp_people(company_name, domain, serp_key)
                if people_text:
                    extra_corpus += f"\n\n[SOURCE: People Search]\n{people_text}"

        # Step 4 — Re-analyze with enriched corpus
        if extra_corpus:
            if status_callback: status_callback(f"🧠 Re-analysing {company_name}...")
            enriched_corpus = corpus + extra_corpus[:20000]
            company_raw2 = analyze_company(enriched_corpus)
            company_data2 = safe_json(company_raw2)
            for key in ["people", "projects", "locations", "employee_count", "founded"]:
                if company_data2.get(key) and len(str(company_data2.get(key))) > len(str(company_data.get(key, ""))):
                    company_data[key] = company_data2[key]

        # Step 5 — Sales analysis
        if status_callback: status_callback(f"💡 Scoring {company_name}...")
        sales_raw = analyze_sales(corpus + extra_corpus[:5000], company_raw)
        sales_data = safe_json(sales_raw)

        # Fill result
        result["company_name"] = company_data.get("company_name", company_name)
        result["score"] = sales_data.get("overall_score", "Cold")
        result["score_reason"] = sales_data.get("score_reason", "")
        result["employee_count"] = company_data.get("employee_count") or "—"
        result["locations"] = ", ".join(company_data.get("locations", []))
        result["confidence"] = company_data.get("confidence", "Low")
        result["people_count"] = len(company_data.get("people", []))
        result["projects_count"] = len(company_data.get("projects", []))
        result["fem_opps"] = len(sales_data.get("fem_opportunities", []))
        result["recommended_products"] = sales_data.get("recommended_products", [])
        result["product_reason"] = sales_data.get("product_reason", "")
        result["entry_point"] = sales_data.get("entry_point", "")
        result["value_positioning"] = sales_data.get("value_positioning", "")
        result["company_data"] = company_data
        result["sales_data"] = sales_data

        return result

    except Exception as e:
        result["status"] = "failed"
        result["error"] = str(e)
        return result


# ══════════════════════════════════════════════════════════════════════════════
# UI
# ══════════════════════════════════════════════════════════════════════════════

# Header
st.markdown("""
<div style='padding: 4px 0 24px;'>
    <div style='font-family:Inter,sans-serif;font-size:22px;font-weight:700;color:#1a1a1a;'>
        MIDAS Batch Lead Scorer
    </div>
    <div style='font-size:14px;color:#6b7280;margin-top:4px;'>
        Upload a list of websites → get scored leads sorted by Hot / Warm / Cold
    </div>
</div>
""", unsafe_allow_html=True)

# ── API Keys ──────────────────────────────────────────────────────────────────
with st.expander("🔑 API Keys", expanded=not all([
    st.session_state.get("b_deepseek_key"),
    st.session_state.get("b_firecrawl_key"),
    st.session_state.get("b_serp_key"),
])):
    kc1, kc2 = st.columns(2)
    with kc1:
        dk = st.text_input("DeepSeek API Key", type="password", key="inp_dk",
                           value=st.session_state.get("b_deepseek_key", st.secrets.get("DEEPSEEK_API_KEY", "")))
        fk = st.text_input("Firecrawl API Key", type="password", key="inp_fk",
                           value=st.session_state.get("b_firecrawl_key", ""))
    with kc2:
        sk = st.text_input("SerpAPI Key", type="password", key="inp_sk",
                           value=st.session_state.get("b_serp_key", ""))
        ck = st.text_input("Companies House Key (optional)", type="password", key="inp_ck",
                           value=st.session_state.get("b_ch_key", st.secrets.get("COMPANIES_HOUSE_KEY", "")))

    if st.button("Save Keys"):
        st.session_state["b_deepseek_key"] = dk
        st.session_state["b_firecrawl_key"] = fk
        st.session_state["b_serp_key"] = sk
        st.session_state["b_ch_key"] = ck
        st.success("Keys saved")

# ── Input ─────────────────────────────────────────────────────────────────────
st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

input_method = st.radio("Input method", ["Paste URLs", "Upload CSV"], horizontal=True, label_visibility="collapsed")

urls = []
if input_method == "Paste URLs":
    url_text = st.text_area(
        "Enter website URLs (one per line)",
        height=200,
        placeholder="https://company1.com\nhttps://company2.com\nhttps://company3.com"
    )
    if url_text:
        urls = [u.strip() for u in url_text.strip().split("\n") if u.strip()]
        urls = [u if u.startswith("http") else f"https://{u}" for u in urls]
else:
    uploaded = st.file_uploader("Upload CSV with a 'url' or 'website' column", type=["csv"])
    if uploaded:
        df = pd.read_csv(uploaded)
        url_col = None
        for col in df.columns:
            if col.lower() in ["url", "website", "site", "domain", "link"]:
                url_col = col
                break
        if url_col is None:
            url_col = df.columns[0]
        urls = [str(u).strip() for u in df[url_col].dropna().tolist() if str(u).strip()]
        urls = [u if u.startswith("http") else f"https://{u}" for u in urls]

if urls:
    st.markdown(f"<div style='font-size:13px;color:#6b7280;margin:8px 0;'>{len(urls)} websites loaded</div>", unsafe_allow_html=True)

# ── Run ───────────────────────────────────────────────────────────────────────
if urls and st.button(f"🚀 Score {len(urls)} Companies", use_container_width=True):
    if not st.session_state.get("b_deepseek_key") or not st.session_state.get("b_firecrawl_key"):
        st.error("DeepSeek and Firecrawl keys are required.")
        st.stop()

    all_results = []
    prog = st.progress(0)
    status = st.empty()
    log = st.empty()

    for i, url in enumerate(urls):
        def update_status(msg):
            status.caption(msg)

        result = process_single_company(
            url=url,
            firecrawl_key=st.session_state["b_firecrawl_key"],
            serp_key=st.session_state.get("b_serp_key", ""),
            ch_key=st.session_state.get("b_ch_key", ""),
            status_callback=update_status,
        )
        all_results.append(result)

        emoji = score_emoji(result["score"])
        if result["status"] == "failed":
            log.markdown(f"<div style='font-size:12px;color:#6b7280;'>❌ {i+1}/{len(urls)} — {extract_domain(url)} — Failed: {result['error']}</div>", unsafe_allow_html=True)
        else:
            log.markdown(f"<div style='font-size:12px;color:#6b7280;'>{emoji} {i+1}/{len(urls)} — {result['company_name']} — {result['score']}</div>", unsafe_allow_html=True)

        prog.progress((i + 1) / len(urls))

    status.empty()
    prog.empty()

    st.session_state["batch_results"] = all_results
    st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# RESULTS DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════

if "batch_results" in st.session_state and st.session_state["batch_results"]:
    results = st.session_state["batch_results"]

    hot   = [r for r in results if r["score"] == "Hot"]
    warm  = [r for r in results if r["score"] == "Warm"]
    cold  = [r for r in results if r["score"] == "Cold"]
    failed = [r for r in results if r["status"] == "failed"]

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Summary metrics
    mc1, mc2, mc3, mc4, mc5 = st.columns(5)
    mc1.metric("Total", len(results))
    mc2.metric("🔥 Hot", len(hot))
    mc3.metric("⚡ Warm", len(warm))
    mc4.metric("❄️ Cold", len(cold))
    mc5.metric("❌ Failed", len(failed))

    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

    # Export
    export_rows = []
    for r in results:
        export_rows.append({
            "Company": r["company_name"],
            "URL": r["url"],
            "Score": r["score"],
            "Score Reason": r["score_reason"],
            "Employees": r["employee_count"],
            "Locations": r["locations"],
            "Confidence": r["confidence"],
            "People": r["people_count"],
            "Projects": r["projects_count"],
            "FEM Opps": r["fem_opps"],
            "Pages Crawled": r["pages_crawled"],
            "Recommended Products": ", ".join(r.get("recommended_products", [])),
            "Product Reason": r.get("product_reason", ""),
            "Entry Point": r.get("entry_point", ""),
            "Value Positioning": r.get("value_positioning", ""),
            "Status": r["status"],
            "Error": r.get("error", ""),
        })
    export_df = pd.DataFrame(export_rows)
    csv_data = export_df.to_csv(index=False)

    st.download_button(
        "📥 Download Results CSV",
        data=csv_data,
        file_name=f"MIDAS_Batch_Scores_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
        use_container_width=True
    )

    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # Tabs
    t_hot, t_warm, t_cold, t_all = st.tabs([
        f"🔥 Hot ({len(hot)})",
        f"⚡ Warm ({len(warm)})",
        f"❄️ Cold ({len(cold)})",
        f"📋 All ({len(results)})"
    ])

    def render_lead_card(r):
        score = r["score"]
        st.markdown(f"""
        <div class='lead-card'>
            <div style='display:flex;justify-content:space-between;align-items:flex-start;'>
                <div>
                    <div style='font-size:17px;font-weight:700;color:#1a1a1a;margin-bottom:4px;'>
                        {r['company_name']}
                        <span class='score-badge {score_cls(score)}'>{score_emoji(score)} {score}</span>
                    </div>
                    <div style='font-size:12px;color:#6b7280;margin-bottom:8px;'>
                        {r['domain']} &nbsp;·&nbsp; 👥 {r['employee_count']} &nbsp;·&nbsp; 📍 {r['locations'] or '—'} &nbsp;·&nbsp; Confidence: {r['confidence']}
                    </div>
                </div>
                <div style='font-size:11px;color:#9ca3af;white-space:nowrap;'>
                    {r['pages_crawled']} pages · {r['people_count']} people · {r['projects_count']} projects
                </div>
            </div>
            <div style='font-size:14px;color:#374151;line-height:1.6;margin-bottom:10px;'>{r['score_reason']}</div>
            <div style='display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px;'>
                {"".join(f"<span style='display:inline-block;font-size:11px;padding:3px 10px;border:1px solid #e5e7eb;border-radius:20px;color:#374151;'>{p}</span>" for p in r.get('recommended_products', []))}
            </div>
            <div style='font-size:13px;color:#6b7280;'><b>Entry:</b> {r.get('entry_point', '—')[:150]}</div>
        </div>
        """, unsafe_allow_html=True)

    with t_hot:
        if hot:
            for r in hot: render_lead_card(r)
        else:
            st.info("No hot leads found.")

    with t_warm:
        if warm:
            for r in warm: render_lead_card(r)
        else:
            st.info("No warm leads found.")

    with t_cold:
        if cold:
            for r in cold: render_lead_card(r)
        else:
            st.info("No cold leads found.")

    with t_all:
        for r in sorted(results, key=lambda x: {"Hot": 0, "Warm": 1, "Cold": 2}.get(x["score"], 3)):
            if r["status"] == "failed":
                st.markdown(f"""
                <div class='lead-card' style='border-left:3px solid #ef4444;'>
                    <div style='font-size:15px;font-weight:600;color:#1a1a1a;'>❌ {r['domain']}</div>
                    <div style='font-size:13px;color:#ef4444;margin-top:4px;'>{r['error']}</div>
                </div>
                """, unsafe_allow_html=True)
            else:
                render_lead_card(r)
