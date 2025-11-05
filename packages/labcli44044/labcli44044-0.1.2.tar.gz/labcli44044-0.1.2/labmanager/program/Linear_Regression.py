from sklearn.linear_model import LinearRegression
import numpy as np
# Sample data
X = np.array([[1],[2],[3],[4],[5]])
y = np.array([2,4,5,4,5])
# Model training
model = LinearRegression()
model.fit(X, y)
# Predictions
predicted = model.predict(X)
print("Coefficients:", model.coef_)
print("Intercept:", model.intercept_)
print("Predictions:", predicted)
# Predict new value
new_pred = model.predict([[6]])
print("Prediction for X=6:", new_pred)
