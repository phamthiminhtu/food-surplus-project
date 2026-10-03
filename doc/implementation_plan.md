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
Capture Layer
- Photo of label or packaging → OCR extracts printed text
- Voice: staff reads label aloud → speech-to-text transcription
- Text: manual fallback
      |
      v
AI-Assisted Extraction (small LLM via Ollama)
- Parse extracted text into structured fields:
  food name, quantity, expiry date, allergens, storage
- Flag fields that could not be confidently extracted
- Human reviews and corrects before submission
      |
      v
Validation Layer (deterministic rules)
- Expiry date: must be today or future
- Required fields: food name, quantity
- Allergen completeness check
      |
      v
FoodCloud Integration (mocked in demo)
- Submit validated listing to Foodiverse
- Receive acceptance and collection status
      |
      v
FoodCloud Platform
- Charity matching and collection coordination
```

---

## Key Design Decisions

### 1. OCR as the primary input path
The label photo is the most natural action for a staff member with a packaged item in hand. OCR extracts the printed text, which the LLM then parses into structured fields. This covers the common case where the barcode is absent, damaged, or not in Foodiverse's database.

### 2. Voice as an alternative to OCR
For staff who find it faster to read a label aloud than photograph it, voice input produces the same unstructured text that the LLM parses. Both paths converge at the same extraction step.

### 3. LLM extracts structure from unstructured text
Whether input comes from OCR, voice, or typing, the text is unstructured. The LLM's job is to identify and normalise the relevant fields — product name, quantity, expiry date, allergens, storage instructions — from whatever text it receives. Low-confidence extractions are flagged for human correction.

### 4. Human confirmation before submission
The AI never submits directly. Every listing goes through a review step where staff can see what was extracted, correct any errors, and confirm. This keeps the human in the loop for food safety accountability.

---

## MVP Scope (3-hour demo)

### In scope
- Photo upload → OCR → LLM extraction → editable review form → save listing
- Voice input → LLM extraction → editable review form → save listing
- Text description fallback
- Validation: expiry date, required fields, allergen check
- Donation log

### Out of scope (post-demo)
- Real FoodCloud / Foodiverse API submission
- Barcode scanning
- User authentication
- Push notifications / collection coordination
- ESG reporting
- Multi-location accounts

---

## File Structure

```
food-surplus-project/
├── app.py              — Streamlit UI
├── llm.py              — Ollama/Qwen inference
├── ocr.py              — Label text extraction from image
├── validation.py       — Deterministic safety checks
├── db.py               — SQLite persistence
├── requirements.txt
└── doc/
    └── implementation_plan.md
```

---

## Tech Stack

| Layer | Tool | Reason |
|---|---|---|
| UI | Streamlit | Zero frontend code, fast to build |
| LLM | Ollama + `qwen2.5:3b` | Free, runs locally, fast on CPU |
| OCR | pytesseract / easyocr | Offline, no API key |
| Voice | SpeechRecognition + Google free tier | Simple browser mic |
| DB | SQLite | Zero setup |
| FoodCloud | Mocked button | Out of scope for demo |

---

## LLM Prompt Design

The prompt treats all input as text extracted from packaging — OCR output, voice transcription, or manual description:

```
You are helping a food donor prepare a listing for FoodCloud.

The following text was extracted from a food label or spoken by staff reading a label:
"{text}"

Extract the structured fields below. Use only what is present in the text — do not invent values.
If a field cannot be determined, return an empty string or empty array.

Return ONLY valid JSON:
{
  "food_name": "",
  "quantity": "e.g. 500g, 2 kg, 12 units",
  "expiry_date": "YYYY-MM-DD or empty string",
  "allergens": ["list from label, empty array if none stated"],
  "storage": "e.g. refrigerate after opening, store in a cool dry place",
  "confidence": "high or low"
}
```

---

## Validation Rules

| Rule | Logic |
|---|---|
| Food name required | Non-empty string |
| Quantity required | Non-empty string |
| Expiry date format | Must parse as YYYY-MM-DD if provided |
| Expiry not in past | Reject if expiry date < today |
| Confidence low | Flag for mandatory human review before submit |
