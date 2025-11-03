import numpy as np

class SimpleLinearRegression:
    """
    Implements a simple linear regression model: y = m*x + c
    """

    def __init__(self):
        self.m = None  # slope
        self.c = None  # intercept

    def fit(self, X, y):
        """Estimate parameters from data"""
        X = np.array(X)
        y = np.array(y)

        x_mean = X.mean()
        y_mean = y.mean()

        numerator = np.sum((X - x_mean) * (y - y_mean))
        denominator = np.sum((X - x_mean) ** 2)
        self.m = numerator / denominator
        self.c = y_mean - self.m * x_mean
        return self

    def predict(self, X):
        """Predict values"""
        X = np.array(X)
        return self.m * X + self.c

    def score(self, X, y):
        """Compute R²"""
        y_pred = self.predict(X)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        return 1 - ss_res / ss_tot