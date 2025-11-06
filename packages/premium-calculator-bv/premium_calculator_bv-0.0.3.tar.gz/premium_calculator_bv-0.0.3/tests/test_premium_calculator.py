
import unittest
from decimal import Decimal
from premium_calculator_pkg.premium_calculator import PremiumCalculator

class TestPremiumCalculator(unittest.TestCase):

    def setUp(self):
        """Set up a PremiumCalculator instance before each test."""
        self.calculator = PremiumCalculator()

    def test_calculate_risk_factor(self):
        """Test the calculate_risk_factor method."""
        # Test with valid collection types
        self.assertEqual(self.calculator.calculate_risk_factor('Vintage Pokemon'), Decimal('0.08'))
        self.assertEqual(self.calculator.calculate_risk_factor('Modern Pokemon'), Decimal('0.04'))
        self.assertEqual(self.calculator.calculate_risk_factor('Vintage Magic The Gathering'), Decimal('0.09'))
        self.assertEqual(self.calculator.calculate_risk_factor('Modern Magic The Gathering'), Decimal('0.03'))
        self.assertEqual(self.calculator.calculate_risk_factor('Other'), Decimal('0.02'))
        
        # Test with a collection not in the predefined types
        self.assertEqual(self.calculator.calculate_risk_factor('Non-existent Type'), Decimal('0.02'))

        # Test with invalid input types
        self.assertIsNone(self.calculator.calculate_risk_factor(123))
        self.assertIsNone(self.calculator.calculate_risk_factor(None))
        self.assertIsNone(self.calculator.calculate_risk_factor([]))

    def test_calculate_premium(self):
        """Test the calculate_premium method."""
        # Test with valid inputs
        self.assertEqual(self.calculator.calculate_premium(1000, 0.08), 108.00)
        self.assertEqual(self.calculator.calculate_premium('2000', '0.04'), 208.00)
        self.assertEqual(self.calculator.calculate_premium(500.50, Decimal('0.09')), 54.55)

        # Test with zero or negative values
        self.assertEqual(self.calculator.calculate_premium(0, 0.08), 0.0)
        self.assertEqual(self.calculator.calculate_premium(-1000, 0.08), 0.0)
        self.assertEqual(self.calculator.calculate_premium(1000, -0.08), 0.0)

        # Test with invalid input types
        self.assertEqual(self.calculator.calculate_premium('abc', 0.08), 0.0)
        self.assertEqual(self.calculator.calculate_premium(1000, 'xyz'), 0.0)
        self.assertEqual(self.calculator.calculate_premium(None, 0.08), 0.0)
        self.assertEqual(self.calculator.calculate_premium(1000, None), 0.0)

if __name__ == '__main__':
    unittest.main()
