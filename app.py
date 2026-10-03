import streamlit as st

from src import DonationData, DonationRepository, DonationExtractor, DonationValidator
from src import ImageInputSource, TextInputSource, VoiceInputSource

repository = DonationRepository()
extractor = DonationExtractor()
validator = DonationValidator()

repository.init_db()

st.set_page_config(page_title="Food Surplus Exchange", page_icon="🥗", layout="wide")
st.title("🥗 Food Surplus Exchange")
st.caption("AI-assisted donor automation layer — prep accurate listings for FoodCloud in seconds")

tab_capture, tab_log = st.tabs(["New Donation", "Donation Log"])

# ── Tab 1: Capture ────────────────────────────────────────────────────────────
with tab_capture:
    st.subheader("Capture Food Details")

    input_method = st.radio("Input method", ["Photo / Label", "Text description", "Voice"], horizontal=True)

    raw_text = ""

    if input_method == "Photo / Label":
        uploaded = st.file_uploader("Upload a photo of the food or its label", type=["jpg", "jpeg", "png"])
        if uploaded:
            st.image(uploaded, width=320)
            with st.spinner("Running OCR..."):
                raw_text = ImageInputSource().get_text(uploaded.read())
            if raw_text:
                raw_text = st.text_area("Extracted text (edit if needed)", value=raw_text, height=120)
            else:
                st.warning("OCR found no text. Describe the food manually below.")
                raw_text = st.text_area("Manual description", height=120)

    elif input_method == "Text description":
        raw_text = TextInputSource().get_text(
            st.text_area(
                "Describe the surplus food",
                placeholder="e.g. 10 kg of ripe tomatoes, best before 2026-10-10, stored at room temperature, no allergens",
                height=120,
            )
        )

    elif input_method == "Voice":
        if st.button("Record (5 seconds)"):
            try:
                raw_text = VoiceInputSource().get_text()
                st.success(f"Heard: {raw_text}")
            except Exception as error:
                st.error(f"Voice input failed: {error}. Switch to Text description.")

    if raw_text and st.button("Extract with AI →", type="primary"):
        with st.spinner("Sending to Qwen 2.5 via Ollama..."):
            try:
                st.session_state["extracted"] = extractor.extract(raw_text)
            except Exception as error:
                st.error(f"AI extraction failed: {error}\n\nIs Ollama running? `ollama serve`")

    # ── Review & edit extracted data ─────────────────────────────────────────
    if "extracted" in st.session_state:
        st.divider()
        st.subheader("Review & Edit")
        donation: DonationData = st.session_state["extracted"]

        col_left, col_right = st.columns(2)
        with col_left:
            donation.food_name = st.text_input("Food Name *", value=donation.food_name)
            donation.quantity = st.text_input("Quantity *", value=donation.quantity)
            donation.expiry_date = st.text_input("Expiry Date (YYYY-MM-DD)", value=donation.expiry_date)
        with col_right:
            allergens_raw = st.text_input(
                "Allergens (comma-separated)",
                value=", ".join(donation.allergens),
            )
            donation.allergens = [a.strip() for a in allergens_raw.split(",") if a.strip()]
            donation.storage = st.text_input("Storage conditions", value=donation.storage)
            st.text_input("AI confidence", value=donation.confidence, disabled=True)

        is_valid, errors = validator.validate(donation)

        if errors:
            for err in errors:
                st.error(err)
        else:
            st.success("All checks passed — ready to submit to FoodCloud")

        if st.button("Confirm & Submit Donation", type="primary", disabled=not is_valid):
            repository.save(donation)
            st.success("Donation submitted! (Demo: saved locally — production would push to FoodCloud API)")
            st.balloons()
            del st.session_state["extracted"]

# ── Tab 2: Donation Log ───────────────────────────────────────────────────────
with tab_log:
    st.subheader("Donation Log")
    donations = repository.get_all()

    if not donations:
        st.info("No donations yet. Go to 'New Donation' to add one.")
    else:
        st.caption(f"{len(donations)} donation(s) on record")
        for donation in donations:
            label = f"**{donation.food_name}** — {donation.quantity} — expires {donation.expiry_date or 'unknown'}"
            with st.expander(label):
                col1, col2 = st.columns(2)
                col1.markdown(f"**Allergens:** {', '.join(donation.allergens) or 'none'}")
                col1.markdown(f"**Storage:** {donation.storage or '—'}")
                col2.markdown(f"**Status:** `{donation.status}`")
                col2.markdown(f"**Submitted:** {donation.created_at[:19]}")
