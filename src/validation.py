from datetime import date

from .models import DonationData


class DonationValidator:
    """Validates a DonationData instance before submission."""

    def validate(self, donation: DonationData) -> tuple[bool, list[str]]:
        """Return (is_valid, errors) for the given donation."""
        errors = (
            self._check_food_name(donation)
            + self._check_quantity(donation)
            + self._check_expiry_date(donation)
        )
        return len(errors) == 0, errors

    def _check_food_name(self, donation: DonationData) -> list[str]:
        """Return an error if food_name is empty."""
        if not donation.food_name.strip():
            return ["Food name is required."]
        return []

    def _check_quantity(self, donation: DonationData) -> list[str]:
        """Return an error if quantity is empty."""
        if not donation.quantity.strip():
            return ["Quantity is required."]
        return []

    def _check_expiry_date(self, donation: DonationData) -> list[str]:
        """Return an error if expiry_date is malformed or already past."""
        expiry_str = donation.expiry_date.strip()
        if not expiry_str:
            return []
        try:
            expiry = date.fromisoformat(expiry_str)
            if expiry < date.today():
                return [f"Food has already expired ({expiry_str})."]
        except ValueError:
            return [f"Invalid expiry date format: '{expiry_str}'. Use YYYY-MM-DD."]
        return []
