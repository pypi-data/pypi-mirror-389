class SimpleLinearRegression:
    def __init__(self):
        self.b0 = 0
        self.b1 = 0

    def fit(self, X, Y):
        n = len(X)
        mean_x = sum(X) / n
        mean_y = sum(Y) / n

        numerator = sum((X[i] - mean_x) * (Y[i] - mean_y) for i in range(n))
        denominator = sum((X[i] - mean_x)**2 for i in range(n))
        self.b1 = numerator / denominator
        self.b0 = mean_y - self.b1 * mean_x
        
        print(f"\nIntercept (b0) = {self.b0}")
        print(f"Pente (b1) = {self.b1}")
        print(f"Équation : y = {self.b0:.2f} + {self.b1:.2f}*x")

    def predict(self, X):
        return [self.b0 + self.b1 * x for x in X]
    def afficher_b0(self):
        print(f"Intercept (b0) = {self.b0}")

    def afficher_b1(self):
        print(f"Pente (b1) = {self.b1}")
        

    def afficher_equation(self):
        print(f"Équation : y = {self.b0:.2f} + {self.b1:.2f}*x")
            # Métriques
    def mae(self, X, Y):
        y_pred = self.predict(X)
        return sum(abs(Y[i]-y_pred[i]) for i in range(len(Y))) / len(Y)

    def rmse(self, X, Y):
        import math
        y_pred = self.predict(X)
        mse = sum((Y[i]-y_pred[i])**2 for i in range(len(Y))) / len(Y)
        return math.sqrt(mse)

    def r2_score(self, X, Y):
        y_pred = self.predict(X)
        mean_y = sum(Y)/len(Y)
        ss_total = sum((Y[i]-mean_y)**2 for i in range(len(Y)))
        ss_res = sum((Y[i]-y_pred[i])**2 for i in range(len(Y)))
        return 1 - (ss_res/ss_total)