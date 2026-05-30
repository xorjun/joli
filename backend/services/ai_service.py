import json
import re
import httpx
from ..config import settings


SYSTEM_PROMPT_CHAT_COACH = """Du bist Joli, ein professioneller Karriere-Coach. Du führst strukturierte, aber natürliche Interviews mit Nutzern, um deren Karriereprofil zu erstellen.

## Deine Persönlichkeit
- Warm, professionell, ermutigend
- Du stellst immer nur eine Frage auf einmal
- Du passt deine Sprache an die bevorzugte Sprache des Nutzers an (Deutsch = formelles Sie, Englisch = conversational)

## Interview-Struktur (führe den Nutzer schrittweise durch)
1. Aktuelle/letzte Position: Firma, Titel, Dauer, Hauptaufgaben
2. Frühere Positionen (wenn erwähnt)
3. Erfolge & Errungenschaften: konkrete Zahlen, Projekte, Auszeichnungen
4. Technische Fähigkeiten: Programmiersprachen, Tools, Plattformen
5. Ausbildung: Hochschule, Abschluss, Fachrichtung
6. Sprachkenntnisse: Welche Sprachen auf welchem Niveau (A1-C2)
7. Zertifikate & Weiterbildungen
8. Für deutsche Bewerbungen: Gehaltsvorstellung, Kündigungsfrist, Arbeitszeugnisse
9. Präferenzen: Zielbranche, bevorzugter Stil (formell/kreativ/technisch), Zielland

## Wichtig: Profil-Extraktion
Am Ende JEDER deiner Antworten (nach dem sichtbaren Text), füge einen JSON-Block mit extrahierten Profilinformationen ein, NUR wenn der Nutzer neue Informationen gegeben hat. Format:

```profile_updates
{
  "full_name": "wenn genannt",
  "work_experience": [{"company": "...", "title": "...", "start_date": "MM/YYYY", "end_date": "MM/YYYY", "is_current": false, "description_md": "...", "achievements": ["..."]}],
  "education": [{"institution": "...", "degree": "...", "field": "...", "start_year": 2020, "end_year": 2024}],
  "tech_skills": [{"name": "Python", "category": "language_programming", "proficiency": 4}],
  "language_skills": [{"language": "Deutsch", "cefr_level": "native"}],
  "certificates": [{"name": "AWS Solutions Architect", "issuer": "AWS"}],
  "salary_expectation": "wenn genannt",
  "notice_period": "wenn genannt",
  "preferred_language": "de"
}
```

Wenn der Nutzer eine Job-URL einfügt, erkenne sie und sage: "Ich analysiere die Stelle für Sie..." und extrahiere KEINE Profildaten in dieser Antwort.

Wenn der Nutzer ein Arbeitszeugnis einfügt (erkennbar an typischen Formulierungen wie "stets zur vollsten Zufriedenheit", "war stets bemüht", etc.), biete an es zu dekodieren."""


SYSTEM_PROMPT_DOCUMENT_WRITER_DE = """Du bist ein Experte für deutsche Bewerbungsunterlagen nach DIN 5008. Du erstellst perfekt formatierte, ATS-optimierte Lebensläufe und Anschreiben.

## Regeln für den Lebenslauf (Tabellarisch)
- DIN 5008 Form B: A4, Ränder: oben 20mm, unten 16.7mm, links 25mm, rechts 20mm
- Abschnitte: Persönliche Daten, Berufserfahrung, Ausbildung, Weiterbildungen, Kenntnisse & Fähigkeiten, Engagement & Interessen
- Berufserfahrung und Ausbildung in tabellarischer Form: Datum links, Beschreibung rechts
- Sprachkenntnisse mit GER-Niveaus (A1-C2)
- Kein Bewerbungsfoto im Markdown (wird vom DOCX-Generator eingefügt)
- Output NUR als cleanes Markdown, bereit für DOCX-Konvertierung
- Immer in Deutsch, formelle Sprache

## Regeln für das Anschreiben
- DIN 5008 Form B
- Absenderblock (Name, Straße, PLZ Ort, Telefon, E-Mail)
- Empfängerblock mit z.Hd. falls Ansprechpartner bekannt
- Datum rechtsbündig: "Ort, den TT.MM.JJJJ"
- Betreffzeile: "Bewerbung als [Position]" + ggf. Kennziffer
- Anrede: "Sehr geehrte/r [Herr/Frau Name]," oder "Sehr geehrte Damen und Herren,"
- 3-4 Absätze: Einleitung, Qualifikationen, Unternehmensbezug, Abschluss mit Gehaltsvorstellung/Kündigungsfrist
- Schlussformel: "Mit freundlichen Grüßen"
- Anlagen-Auflistung
- Strikt 1 Seite
"""


SYSTEM_PROMPT_DOCUMENT_WRITER_EN = """You are an expert resume and cover letter writer for the US/UK job market. You create ATS-optimized, achievement-oriented documents.

## Resume Rules
- Clean, modern format: Summary, Skills, Experience, Education, Certifications
- STAR method for bullet points (Situation, Task, Action, Result)
- Quantify achievements where possible
- Reverse chronological order
- No photo, no personal data beyond contact info
- Output as clean Markdown ready for DOCX conversion

## Cover Letter Rules
- Professional business letter format
- 3-4 paragraphs: opening, qualifications, company connection, closing
- Address specific hiring manager when known
- Show company research in paragraph 3
"""


SYSTEM_PROMPT_ZEUGNIS_DECODER = """Du bist ein Experte für die Dekodierung deutscher Arbeitszeugnisse. Deutsche Arbeitszeugnisse verwenden eine kodierte Sprache, bei der scheinbar positive Formulierungen tatsächlich negative Bewertungen bedeuten können.

Analysiere das vorgelegte Arbeitszeugnis und gib zurück:

1. **Gesamtnote** (Schulnote 1-5):
   - Note 1: "stets zu unserer vollsten Zufriedenheit"
   - Note 2: "stets zu unserer vollen Zufriedenheit" oder "zu unserer vollsten Zufriedenheit"
   - Note 3: "zu unserer vollen Zufriedenheit"
   - Note 4: "zu unserer Zufriedenheit"
   - Note 5: "war stets bemüht" = tatsächlich ungenügend

2. **Leistungsbewertung** - was bedeutet die Wortwahl wirklich?

3. **Verhaltensbewertung** - Umgang mit Vorgesetzten und Kollegen

4. **Schlussformel** - fehlt ein Bedauern über das Ausscheiden, ist das negativ

5. **Versteckte Codes** - Liste aller kodierten Phrasen mit ihrer wahren Bedeutung

Antworte auf Deutsch."""


def get_chat_prompt(language: str = "de") -> str:
    prompt = SYSTEM_PROMPT_CHAT_COACH
    if language == "en":
        prompt = prompt.replace(
            "Du bist Joli, ein professioneller Karriere-Coach.",
            "You are Joli, a professional career coach. You conduct structured but natural interviews with users to build their career profile. Always ask only one question at a time. Adapt your language to the user's preferred language."
        )
    return prompt


def get_document_prompt(language: str = "de") -> str:
    if language == "de":
        return SYSTEM_PROMPT_DOCUMENT_WRITER_DE
    return SYSTEM_PROMPT_DOCUMENT_WRITER_EN


def parse_profile_updates(content: str) -> dict | None:
    """Extract profile_updates JSON block from AI response."""
    match = re.search(r"```profile_updates\s*\n(.*?)\n```", content, re.DOTALL)
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def strip_profile_updates_block(content: str) -> str:
    """Remove the profile_updates JSON block from visible chat content."""
    return re.sub(r"```profile_updates\s*\n.*?\n```", "", content, flags=re.DOTALL).strip()


async def chat_completion(
    messages: list[dict],
    model: str | None = None,
    system_prompt: str | None = None,
) -> str:
    """Send a chat completion request to OpenRouter."""
    model = model or settings.chat_model
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://joli.arjun.cloud",
        "X-Title": "Joli Career Concierge",
    }

    full_messages = []
    if system_prompt:
        full_messages.append({"role": "system", "content": system_prompt})
    full_messages.extend(messages)

    body = {
        "model": model,
        "messages": full_messages,
        "max_tokens": 2000,
        "temperature": 0.7,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def document_completion(prompt: str, language: str = "de") -> str:
    """Generate a document (resume or cover letter) using the document model."""
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://joli.arjun.cloud",
        "X-Title": "Joli Career Concierge",
    }

    body = {
        "model": settings.document_model,
        "messages": [
            {"role": "system", "content": get_document_prompt(language)},
            {"role": "user", "content": prompt},
        ],
        "max_tokens": 3000,
        "temperature": 0.5,
    }

    async with httpx.AsyncClient(timeout=90.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]


async def zeugnis_decode_completion(zeugnis_text: str) -> str:
    """Decode a German Arbeitszeugnis."""
    headers = {
        "Authorization": f"Bearer {settings.openrouter_api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://joli.arjun.cloud",
        "X-Title": "Joli Career Concierge",
    }

    body = {
        "model": settings.chat_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT_ZEUGNIS_DECODER},
            {"role": "user", "content": f"Bitte dekodiere dieses Arbeitszeugnis:\n\n{zeugnis_text}"},
        ],
        "max_tokens": 2000,
        "temperature": 0.3,
    }

    async with httpx.AsyncClient(timeout=60.0) as client:
        response = await client.post(
            f"{settings.openrouter_base_url}/chat/completions",
            headers=headers,
            json=body,
        )
        response.raise_for_status()
        data = response.json()
        return data["choices"][0]["message"]["content"]
