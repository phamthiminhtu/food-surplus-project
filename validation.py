from datetime import date


def validate_donation(data: dict) -> tuple[bool, list[str]]:
    errors = []

    if not data.get("food_name", "").strip():
        errors.append("Food name is required.")

    if not data.get("quantity", "").strip():
        errors.append("Quantity is required.")

    expiry_str = data.get("expiry_date", "").strip()
    if expiry_str:
        try:
            expiry = date.fromisoformat(expiry_str)
            if expiry < date.today():
                errors.append(f"Food has already expired ({expiry_str}).")
        except ValueError:
            errors.append(f"Invalid expiry date format: '{expiry_str}'. Use YYYY-MM-DD.")

    return len(errors) == 0, errors
