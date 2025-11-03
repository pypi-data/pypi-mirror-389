# linear_regression_ayoub

A simple linear regression model built from scratch in Python.

## Usage

```python
from linear_regression_ayoub import SimpleLinearRegression

X = [1, 2, 3, 4, 5]
y = [2, 4, 5, 4, 5]

model = SimpleLinearRegression()
model.fit(X, y)
print("Slope:", model.m)
print("Intercept:", model.c)
print("R²:", model.score(X, y))
```
