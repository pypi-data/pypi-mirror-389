from decimal import Decimal


# Class to calculate insurance premium
class PremiumCalculator:

    RISK_FACTOR_BY_COLLECTION = {
        'Vintage Pokemon': 8,
        'Modern Pokemon': 4,
        'Vintage Magic The Gathering': 9,
        'Modern Magic The Gathering': 3,
        'Other': 2,
    }

    def __init__(self, base_rate=0.10):
        """Initialize PremiumCalculator with a base rate of 10%."""
        self.base_rate = base_rate

    def calculate_risk_factor(self, card_collection_type):
        """Return the risk factor as a Decimal fraction."""
        if not isinstance(card_collection_type, str):
            return None
        try:
            base_factor = self.RISK_FACTOR_BY_COLLECTION.get(
                card_collection_type,
                self.RISK_FACTOR_BY_COLLECTION.get('Other'),
            )
            if base_factor is not None:
                factor = Decimal(str(base_factor)) / Decimal('100')
                return factor
            else:
                return None
        except (TypeError, ValueError):
            return None

    def calculate_premium(self, collection_value, risk_factor):
        """Calculate insurance premium from collection value and risk factor.

        Args:
            collection_value (float|str): The total value of the card collection (major units).
            risk_factor (float|Decimal|str): Fractional risk factor (e.g. 0.08 for 8%).

        Returns:
            float: The calculated insurance premium rounded to 2 decimal places,
                   or 0.0 for invalid input.
        """
        try:
            value = float(collection_value)
            if isinstance(risk_factor, Decimal):
                factor = float(risk_factor)
            else:
                factor = float(risk_factor)

            if value <= 0 or factor < 0 or risk_factor is None:
                return 0.0

            premium = value * self.base_rate * (1 + factor)
            return round(premium, 2)

        except (TypeError, ValueError):
            return 0.0
