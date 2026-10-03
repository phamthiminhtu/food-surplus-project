# Food Surplus Demo

[FoodCloud](https://www.food.cloud/) solves food waste by connecting businesses with surplus food to local charities. Donors list what they have, charities claim it, and collections are coordinated through their Foodiverse platform.

This project sits one step earlier in that chain — it solves the **listing problem** for small restaurants. Getting surplus food into Foodiverse is the friction point; this tool removes it.

---

## The Problem

FoodCloud connects food donors with charities. To list a donation, staff need to fill in product name, quantity, expiry date, allergens, and storage requirements.

Foodiverse supports two input methods today:

| Method | Reality |
|---|---|
| Barcode scan | Only works if the barcode resolves in the Foodiverse database |
| Manual text entry | Every field typed by hand — too slow at end of service |

Small restaurants donating surplus ingredients already have all this information printed on the packaging. The bottleneck is getting it into the form. Enough friction means the donation never gets listed.

---

## The Fix

Add OCR and voice as new input paths. Staff photograph a label or read it aloud, an LLM extracts the structured fields, a human confirms, and the listing is ready to submit.

```
Photo / Voice / Text
        |
        v
OCR or speech-to-text  →  raw label text
        |
        v
LLM extraction (Ollama + qwen2.5:3b)  →  structured donation fields
        |
        v
Human review & edit
        |
        v
Validation  →  expiry check, required fields
        |
        v
Save / Submit to FoodCloud
```

No barcode scanner needed. No manual typing.

---

## Stack

| Layer | Tool |
|---|---|
| UI | Streamlit |
| LLM | Ollama + `qwen2.5:3b` (local, no API key) |
| OCR | pytesseract → easyocr fallback |
| Voice | SpeechRecognition + Google free tier |
| DB | DuckDB |
| FoodCloud | Mocked (out of scope for demo) |

**Why a small model?** `qwen2.5:3b` runs locally with no API cost, which matters for a high-volume, low-margin use case like food donation. The tradeoff: smaller models are less reliable at structured extraction and will need prompt tuning or fine-tuning to hit production accuracy.

---

## Run

```bash
source ~/workspace/env-food-surplus-project/bin/activate
streamlit run app.py
```

Requires [Ollama](https://ollama.com) running locally with `qwen2.5:3b` pulled:

```bash
ollama pull qwen2.5:3b
```

---

## Scope

**Demo includes:** photo upload → OCR → LLM extraction → editable review form → validation → save. Voice and text fallback also supported.

**Out of scope:** real Foodiverse API submission, barcode scanning, auth, multi-location.
