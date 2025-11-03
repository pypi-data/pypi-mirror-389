# package_name

`rocket` is a Python library for Creating and move rockets in a 2D space, Compare rocket equality by position, Calculate distances between rockets and Specialized CircleRocket class with area and circumference calculations

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install `rocket`.

```bash
pip install rocket
```

## Usage

```python
from rocket import Rocket, CircleRocket

# Create a basic Rocket object
r1 = Rocket(0, 0)
r2 = Rocket(3, 4)

# Move a rocket
r1.move_rocket(1, 2)
print(r1)  # prints new position

# Compare two rockets
print(r1 == r2)  # checks if positions are equal

# Measure distance between rockets
print(r1.get_distance(r2))

# Create a CircleRocket (inherits from Rocket)
cr1 = CircleRocket(0, 0, 10)
print(cr1.get_area())          # prints area of the circular rocket
print(cr1.get_circumference()) # prints circumference
```

## License
[MIT]("C:\Users\nabil\Downloads\AI DS\SEDS_Lab3\rocket\rocket\LICENCE.txt")