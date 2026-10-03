from datetime import datetime

import duckdb

from .models import DonationData


class DonationRepository:
    """DuckDB-backed persistence for donation records."""

    DB_PATH = "donations.duckdb"

    def init_db(self) -> None:
        """Create the donations table if it does not exist."""
        with duckdb.connect(self.DB_PATH) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS donations (
                    food_name TEXT,
                    quantity TEXT,
                    expiry_date TEXT,
                    allergens TEXT[],
                    storage TEXT,
                    confidence TEXT,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT
                )
            """)

    def save(self, donation: DonationData) -> None:
        """Persist a donation record to the database."""
        with duckdb.connect(self.DB_PATH) as conn:
            conn.execute("""
                INSERT INTO donations
                    (food_name, quantity, expiry_date, allergens, storage, confidence, status, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                donation.food_name,
                donation.quantity,
                donation.expiry_date,
                donation.allergens,
                donation.storage,
                donation.confidence,
                "pending",
                datetime.now().isoformat(),
            ))

    def get_all(self) -> list[DonationData]:
        """Return all donations ordered by creation time descending."""
        with duckdb.connect(self.DB_PATH) as conn:
            rows = conn.execute(
                "SELECT food_name, quantity, expiry_date, allergens, storage, confidence, status, created_at "
                "FROM donations ORDER BY created_at DESC"
            ).fetchall()
        return [
            DonationData(
                food_name=row[0],
                quantity=row[1],
                expiry_date=row[2],
                allergens=row[3] or [],
                storage=row[4],
                confidence=row[5],
                status=row[6],
                created_at=row[7],
            )
            for row in rows
        ]
