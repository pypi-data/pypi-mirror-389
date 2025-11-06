# Premium Calculator Library

This is a simple package to calculate insurance premium. This library puporse is to use on master's project, its puporse is to demostrate that I learned how to deploy a library and use on my CA project. 

## Features

- Calculate premiums
- Default base rate of 10%

## Instalation

pip install premium-calculator-bv

## Usage

Here is an example of how to use the **PremiumCalculator** class:

```python
from premium_calculator_pkg.premium_calculator import PremiumCalculator

# Initialize the calculator
calculator = PremiumCalculator()

collection_type = 'Vintage Pokemon'
risk_factor = calculator.calculate_risk_factor(collection_type)
if risk_factor is not None:
    premium2 = calculator.calculate_premium(1000, risk_factor)
    print(f"The calculated premium for {collection_type} is: {premium2}")
else:
    print(f"Could not calculate premium for {collection_type} due to invalid risk factor.")

```

