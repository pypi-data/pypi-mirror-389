import numpy as np

class SimpleLinearRegression:
    def __init__(self):
        self.m = 0  # slope
        self.b = 0  # intercept

    def fit(self, X, y):
        """
        Fit the model to training data.
        X: list or numpy array of input features
        y: list or numpy array of output values
        """
        X = np.array(X)
        y = np.array(y)
        n = len(X)
        X_mean = np.mean(X)
        y_mean = np.mean(y)

        numerator = np.sum((X - X_mean) * (y - y_mean))
        denominator = np.sum((X - X_mean)**2)
        self.m = numerator / denominator
        self.b = y_mean - self.m * X_mean

    def predict(self, X):
        """
        Predict values for input X.
        """
        X = np.array(X)
        return self.m * X + self.b

    def coefficients(self):
        """
        Return the slope and intercept.
        """
        return self.m, self.b
