# Food Surplus Exchange — Implementation Plan

## Problem Statement

FoodCloud's Foodiverse platform currently supports two ways for donors to identify and list food products:

- **Barcode scanning** — works well for packaged, commercially produced goods with a standard barcode
- **Manual text entry** — a fallback that requires staff to type every field by hand

**OCR (reading text from packaging) and voice input are not implemented or advertised capabilities in Foodiverse.**

This is a meaningful gap. Small restaurants donating surplus food typically have:
- Packaged ingredients with printed labels (brand, product name, weight, expiry, allergens) — all the information needed for a listing, already printed on the box or packet
- No barcode scanner on hand, or goods whose barcodes don't resolve in the Foodiverse product database
- Staff with limited time who will not manually type every field on a form at end of service

The result: the information exists on the packaging, but extracting it into Foodiverse requires either a working barcode scan or tedious manual entry. Either path creates enough friction that many donations simply don't get listed.

**This system adds OCR and voice-from-packaging as new input methods** — a donor automation layer that sits in front of FoodCloud. Staff photograph a label or read it aloud, the AI extracts the structured fields, a human confirms, and the validated listing is submitted to FoodCloud. No barcode scanner required, no typing required.

---

## Gap in Foodiverse Today

| Input method | Foodiverse | This system |
|---|---|---|
| Barcode scan | Supported | Not needed (OCR/voice cover it) |
| Manual text entry | Supported | Replaced by AI extraction |
| OCR from label photo | **Not implemented** | Core feature |
| Voice from packaging | **Not implemented** | Core feature |

---

## Architecture

```
Restaurant / Small Donor
      |
      v
Capture Layer  (src/input_sources.py)
- Photo of label or packaging → OCR extracts printed text  [ImageInputSource]
- Voice: staff reads label aloud → speech-to-text           [VoiceInputSource]
- Text: manual fallback                                      [TextInputSource]
      |
      v
AI-Assisted Extraction  (src/extractor.py)
- Parse extracted text into structured fields via Ollama/Qwen [DonationExtractor]
- Returns DonationData with all FoodCloud-spec fields
- Human reviews and corrects before submission
      |
      v
Validation Layer  (src/validation.py)
- Deterministic rules on DonationData fields                [DonationValidator]
      |
      v
Persistence  (src/db.py)
- DuckDB local store, confirmed donations only              [DonationRepository]
      |
      v
FoodCloud Integration (mocked in demo)
- Submit validated listing to Foodiverse
```

---

## File Structure

```
food-surplus-project/
├── app.py                   — Streamlit UI; imports from src
├── requirements.txt
├── LICENSE                  — Apache 2.0
├── doc/
│   ├── implementation_plan.md
│   └── file_format.md       — FoodCloud CSV/Excel field spec
└── src/
    ├── __init__.py          — Re-exports public API
    ├── models.py            — DonationData dataclass
    ├── ocr.py               — OcrReader
    ├── input_sources.py     — InputSource ABC + Image/Text/Voice
    ├── extractor.py         — DonationExtractor (LLM)
    ├── validation.py        — DonationValidator
    └── db.py                — DonationRepository (DuckDB)
```

---

## Tech Stack

| Layer | Tool | Reason |
|---|---|---|
| UI | Streamlit | Zero frontend code, fast to build |
| LLM | Ollama + `qwen2.5:3b` | Free, runs locally, fast on CPU |
| OCR | pytesseract → easyocr fallback | Offline, no API key |
| Voice | SpeechRecognition + Google free tier | Simple mic access |
| DB | DuckDB | Zero setup, native LIST type for allergens |
| FoodCloud | Mocked button | Out of scope for demo |

---

## Component Details

### `src/models.py` — `DonationData`

A plain dataclass that is the single data-transfer object between every layer.

```python
@dataclass
class DonationData:
    food_name: str = ""
    quantity: str = ""
    expiry_date: str = ""
    allergens: list[str] = field(default_factory=list)
    storage: str = ""
    confidence: str = ""
    status: str = "pending"
    created_at: str = ""
```

| Method | Status | Notes |
|---|---|---|
| `to_dict()` | Implemented | Serialises all fields; allergens as Python list |
| `from_dict(data)` | Implemented | Handles allergens as list or comma-separated string |

**Design note:** `DonationData` currently maps to the old internal field names (`food_name`, `expiry_date`, etc.).
The extractor prompt was updated to target the FoodCloud CSV spec (`product_name`, `best_before_date`, etc. — see `doc/file_format.md`). `DonationData` fields need to be aligned with the spec in a follow-up.

---

### `src/ocr.py` — `OcrReader`

Extracts raw text from image bytes. Tries pytesseract first (faster, lower memory); falls back to easyocr if pytesseract is unavailable or returns empty.

```
extract_text(image_bytes) → str
  ├── _try_pytesseract(image_bytes) → str    [Pillow + pytesseract]
  └── _try_easyocr(image_bytes) → str        [easyocr + numpy + Pillow]
```

| Method | Status | Notes |
|---|---|---|
| `extract_text` | Implemented | Returns `""` if both engines fail |
| `_try_pytesseract` | Implemented | `pytesseract.image_to_string` on PIL Image |
| `_try_easyocr` | Implemented | `easyocr.Reader(["en"])`, converts PIL Image to numpy array |

Both engine methods catch all exceptions silently and return `""` — the caller decides what to do with an empty result.

---

### `src/input_sources.py` — `InputSource` + concrete classes

All three input methods are polymorphic under one ABC so `app.py` can call `source.get_text(...)` uniformly.

```
InputSource (ABC)
├── ImageInputSource   — wraps OcrReader
├── TextInputSource    — strips and returns raw string
└── VoiceInputSource   — microphone + SpeechRecognition
```

| Class | Method | Status | Notes |
|---|---|---|---|
| `ImageInputSource` | `get_text(bytes)` | **Stub** | Should call `self.ocr_reader.extract_text(raw_input)` |
| `TextInputSource` | `get_text(str)` | Implemented | `return raw_input.strip()` |
| `VoiceInputSource` | `get_text()` | **Stub** | Should use `sr.Recognizer` + `sr.Microphone`, 5 s listen window |

`ImageInputSource.__init__` already instantiates `self.ocr_reader = OcrReader()`.

**To implement `VoiceInputSource.get_text`:**
```python
import speech_recognition as sr
recognizer = sr.Recognizer()
with sr.Microphone() as source:
    audio = recognizer.listen(source, timeout=5)
return recognizer.recognize_google(audio)
```

---

### `src/extractor.py` — `DonationExtractor`

Sends raw text to a local Ollama instance and parses the JSON response into a `DonationData`.

**Configuration (class attributes):**

| Attribute | Value |
|---|---|
| `OLLAMA_URL` | `http://localhost:11434/api/generate` |
| `MODEL` | `qwen2.5:3b` |

**Prompt output schema** (aligned with `doc/file_format.md`):

| Field | Type | Required |
|---|---|---|
| `product_name` | string | Yes |
| `product_description` | string | Yes |
| `category` | `bakery / fruit_veg / chilled / ambient / other` | Yes |
| `quantity` | number | Yes |
| `unit` | `each / kg / pack` | Yes |
| `available_from` | `YYYY-MM-DDTHH:MM:SS` | Yes |
| `available_until` | `YYYY-MM-DDTHH:MM:SS` | Yes |
| `best_before_date` | `YYYY-MM-DD` | Yes |
| `store_id` | string | Optional |
| `weight_kg` | number \| null | Optional |
| `unit_price` | number \| null | Optional |
| `total_value` | number \| null | Optional |
| `surplus_reason` | string | Optional |

| Method | Status | Notes |
|---|---|---|
| `extract(raw_text)` | **Stub** | POST to Ollama, call `_parse_llm_response`, return `DonationData.from_dict(...)` |
| `_parse_llm_response(str)` | Implemented | `re.search(r"\{.*\}", raw, re.DOTALL)` then `json.loads` |

**To implement `extract`:**
```python
import requests
payload = {"model": self.MODEL, "prompt": self.PROMPT_TEMPLATE.format(text=raw_text), "stream": False}
response = requests.post(self.OLLAMA_URL, json=payload, timeout=60)
response.raise_for_status()
parsed = self._parse_llm_response(response.json()["response"])
return DonationData.from_dict(parsed)
```

---

### `src/validation.py` — `DonationValidator`

Deterministic rule checks on a `DonationData` instance. Returns `(is_valid: bool, errors: list[str])`.

```
validate(donation) → (bool, list[str])
  ├── _check_food_name(donation) → list[str]
  ├── _check_quantity(donation) → list[str]
  └── _check_expiry_date(donation) → list[str]
```

| Rule | Check | Error message |
|---|---|---|
| Food name required | `donation.food_name.strip()` non-empty | `"Food name is required."` |
| Quantity required | `donation.quantity.strip()` non-empty | `"Quantity is required."` |
| Expiry date format | `date.fromisoformat(expiry_str)` succeeds | `"Invalid expiry date format: '…'. Use YYYY-MM-DD."` |
| Expiry not in past | `expiry >= date.today()` | `"Food has already expired (…)."` |

All methods are fully implemented. Expiry check is skipped when `expiry_date` is empty (field is optional).

---

### `src/db.py` — `DonationRepository`

DuckDB-backed persistence. One file (`donations.duckdb`) in the working directory.

**Schema:**

```sql
CREATE TABLE IF NOT EXISTS donations (
    food_name    TEXT,
    quantity     TEXT,
    expiry_date  TEXT,
    allergens    TEXT[],   -- native DuckDB list, no comma-join needed
    storage      TEXT,
    confidence   TEXT,
    status       TEXT DEFAULT 'pending',
    created_at   TEXT
)
```

| Method | Status | Notes |
|---|---|---|
| `init_db()` | Implemented | `CREATE TABLE IF NOT EXISTS` inside `with duckdb.connect(...)` |
| `save(donation)` | Implemented | Inserts all fields; `allergens` passed as Python list; `status` hardcoded to `"pending"`; `created_at` set to `datetime.now().isoformat()` |
| `get_all()` | Implemented | `SELECT … ORDER BY created_at DESC`; returns `list[DonationData]`; `allergens` column returns Python list natively |

`duckdb.connect()` used as a context manager — auto-commits on exit, no explicit `conn.commit()` needed.

---

### `app.py` — Streamlit UI

Thin orchestration layer. No business logic.

**Module-level singletons** (instantiated once at import time):
```python
repository = DonationRepository()
extractor  = DonationExtractor()
validator  = DonationValidator()
repository.init_db()
```

**Tab 1 — New Donation flow:**

```
radio: Photo / Label | Text description | Voice
  │
  ├─ Photo  → ImageInputSource().get_text(bytes)  → raw_text
  ├─ Text   → TextInputSource().get_text(str)     → raw_text
  └─ Voice  → VoiceInputSource().get_text()       → raw_text
  │
  └─ "Extract with AI →" button
       → extractor.extract(raw_text) → DonationData → session_state["extracted"]
       │
       └─ Review & Edit form (edits DonationData fields in place)
            → validator.validate(donation) → show errors or green tick
            → "Confirm & Submit" → repository.save(donation)
```

**Tab 2 — Donation Log:**
```
repository.get_all() → list[DonationData] → expanders per record
```

---

## MVP Scope (demo)

### In scope
- Photo upload → OCR → LLM extraction → editable review form → save listing
- Voice input → LLM extraction → editable review form → save listing
- Text description fallback
- Validation: expiry date, required fields
- Donation log

### Out of scope (post-demo)
- Real FoodCloud / Foodiverse API submission
- Barcode scanning
- User authentication
- Push notifications / collection coordination
- ESG reporting
- Multi-location accounts

---

## Known Gaps / Follow-up Work

| Item | Detail |
|---|---|
| `DonationData` field alignment | Fields still use old names (`food_name`, `expiry_date`). Should be updated to match FoodCloud spec (`product_name`, `best_before_date`, etc.) from `doc/file_format.md`. |
| `ImageInputSource.get_text` | Stub — one-liner: `return self.ocr_reader.extract_text(raw_input)` |
| `VoiceInputSource.get_text` | Stub — implement with `speech_recognition` (see above) |
| `DonationExtractor.extract` | Stub — implement with `requests.post` to Ollama (see above) |
| Validation coverage | `_check_food_name` maps to old `food_name` field; update when `DonationData` is realigned |
