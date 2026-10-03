from dataclasses import dataclass, field


@dataclass
class DonationData:
    """Represents a single food donation record."""

    food_name: str = ""
    quantity: str = ""
    expiry_date: str = ""
    allergens: list[str] = field(default_factory=list)
    storage: str = ""
    confidence: str = ""
    status: str = "pending"
    created_at: str = ""

    def to_dict(self) -> dict:
        """Serialize to a plain dict (allergens as list)."""
        return {
            "food_name": self.food_name,
            "quantity": self.quantity,
            "expiry_date": self.expiry_date,
            "allergens": self.allergens,
            "storage": self.storage,
            "confidence": self.confidence,
            "status": self.status,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "DonationData":
        """Construct from a plain dict. Allergens may be a list or comma-separated string."""
        allergens = data.get("allergens", [])
        if isinstance(allergens, str):
            allergens = [a.strip() for a in allergens.split(",") if a.strip()]
        return cls(
            food_name=data.get("food_name", ""),
            quantity=data.get("quantity", ""),
            expiry_date=data.get("expiry_date", ""),
            allergens=allergens,
            storage=data.get("storage", ""),
            confidence=data.get("confidence", ""),
            status=data.get("status", "pending"),
            created_at=data.get("created_at", ""),
        )
