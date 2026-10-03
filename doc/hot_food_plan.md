# Food Surplus Exchange — Implementation Plan

## Problem Statement

Small restaurants prepare food fresh every day and inevitably have leftovers at the end of service — unsold dishes, prepped-but-unused ingredients, or excess cooked portions. Unlike supermarkets, they have no packaging, no barcodes, and no inventory system. The food is real and good, but donating it is too hard:

- A chef at end of shift doesn't have time to fill a form.
- There is no label to scan, no barcode to read, no printed expiry date.
- Allergens live in the chef's head, not on a sticker.
- Collection must happen within hours, not days.
- Most donation platforms are designed around packaged goods — restaurants simply don't fit.

The result: perfectly good food gets binned every night.

This system is a **voice-and-photo-first donation assistant built around how a small restaurant actually works** — not around how a supermarket does inventory. It removes friction from the donor's side so that submitting a donation takes under two minutes at the end of a shift, and routes that listing to FoodCloud for charity matching and collection.

---

## How Restaurants Differ from Supermarkets

| Dimension | Supermarket | Small Restaurant |
|---|---|---|
| Food type | Packaged, labelled | Fresh, cooked, unpackaged |
| Identification | Barcode, SKU | Dish name, verbal description |
| Expiry | Printed on label | Same-day or within hours |
| Allergens | Printed on packaging | Known by chef, not written down |
| Quantity unit | Weight (kg), units | Portions, trays, pots |
| Lead time | Hours to days | End of shift (urgent) |
| Staff availability | Dedicated back-office | Chef, hands full |
| Input preference | Systematic scan | Voice or quick photo |

The system must be designed around the restaurant column, not the supermarket column.

---

## Architecture

```
Restaurant Staff
      |
      v
Capture Layer (voice-first, photo-second, text fallback)
- Voice: "We have leftover lamb stew, about 20 portions, still hot"
- Photo: snap the tray or pot
- Text: free-form description typed quickly
      |
      v
AI-Assisted Extraction (small LLM, runs locally via Ollama)
- Infer food name and category from description
- Estimate quantity in portions or kg
- Infer expiry window: cooked food → same-day, raw prep → today + 1
- Infer likely allergens from dish name (e.g. "carbonara" → eggs, dairy, gluten)
- Flag low-confidence inferences for human confirmation
- Human reviews and confirms before submission
      |
      v
Validation Layer (deterministic rules)
- Collection window: must be collectible within 4 hours
- Temperature: hot food flagged for immediate collection
- Allergen completeness: warn if common dish but no allergens listed
- Required fields: food name, quantity, collection window
      |
      v
FoodCloud Integration (mocked in demo)
- Submit validated listing
- Receive collection ETA
      |
      v
FoodCloud Platform
- Charity matching and collection coordination
```

---

## Key Design Decisions for Restaurant Context

### 1. Voice-first input
Chefs and kitchen staff are time-pressed at end of shift. Typing a form is a barrier. Voice input with a single button tap is the primary path. Text description is the fallback.

Photo upload is for label-less identification: a photo of a pot of soup or a tray of sandwiches gives the AI visual context, but OCR is not the main value — dish recognition from the description matters more.

### 2. Expiry is implicit, not scanned
Restaurant food has no printed expiry. The system defaults:
- Cooked/hot food → collectible today, within 4 hours
- Raw prepped ingredients → today + 1 day
- Baked goods → today + 1 day

The AI infers category from the description. Staff can override. No barcode scanning needed.

### 3. Allergen inference from dish name
The LLM is prompted to suggest allergens based on dish name before asking the chef. This flips the UX: instead of "please list allergens", the system says "we think this contains gluten, dairy — is that right?" The chef confirms or corrects. This is faster and catches more than an empty field.

### 4. Quantity in portions, not kg
Restaurants think in portions and trays, not kilograms. The system accepts natural language quantities ("about 20 portions", "a full tray", "half a pot") and stores them as-is. It optionally converts to kg for FoodCloud submission using rough estimates.

### 5. Urgency by default
Every listing from a restaurant is treated as time-sensitive. The UI prominently shows collection window and highlights listings expiring soon. This drives faster charity matching on the FoodCloud side.

---

## MVP Scope (3-hour demo)

### In scope
- Voice input → AI extraction → review form → save listing
- Photo upload → description text → AI extraction → review form → save listing
- Allergen suggestion from dish name with confirm/edit
- Implicit expiry: cooked vs. raw category selector with auto-fill
- Quantity in natural language (portions, trays)
- Validation: collection window, required fields, allergen completeness
- Donation log with status

### Out of scope (post-demo)
- Real FoodCloud API integration
- User authentication
- Push notifications
- Maps / collection routing
- ESG reporting
- Multi-restaurant accounts

---

## File Structure

```
food-surplus-project/
├── app.py              — Streamlit UI
├── llm.py              — Ollama/Qwen inference
├── ocr.py              — Image text extraction (fallback only)
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

The prompt is adapted for restaurant food — no barcodes, dish-name-driven allergen inference, implicit expiry:

```
You are helping a small restaurant donate leftover food.

Description from restaurant staff:
"{text}"

Extract the following. Use the dish name to infer allergens if not stated.
For expiry: if the food is cooked/hot, set collection_window to "today, within 4 hours".
If raw/prepped ingredients, set to "today".

Return ONLY valid JSON:
{
  "food_name": "",
  "category": "cooked | raw_prep | baked | other",
  "quantity": "e.g. 20 portions, 1 tray, half a pot",
  "collection_window": "today, within 4 hours | today | today + 1 day",
  "allergens": ["inferred list"],
  "allergens_inferred": true or false,
  "storage": "hot | room temperature | refrigerated",
  "notes": "any extra context",
  "confidence": "high | low"
}
```

---

## Validation Rules

| Rule | Logic |
|---|---|
| Food name required | Non-empty string |
| Quantity required | Non-empty string |
| Collection window | Must be today (cooked food expires same day) |
| Allergens | Warn if dish name suggests allergens but list is empty |
| Confidence low | Flag for mandatory human review before submit |
