
class SimpleLinearRegression:

    def __init__(self):
        self.m = 0
        self.b = 0

    def fit(self, X, y):
        n = len(X)

        sum_x = sum(X)
        sum_y = sum(y)
        sum_xy = sum(x * y for x, y in zip(X, y))
        sum_xx = sum(x * x for x in X)

        self.m = (n * sum_xy - sum_x * sum_y) / (n * sum_xx - sum_x ** 2)
        self.b = (sum_y - self.m * sum_x) / n

    def predict(self, X):
        return [self.m * x + self.b for x in X]
