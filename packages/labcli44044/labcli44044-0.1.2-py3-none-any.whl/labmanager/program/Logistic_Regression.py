# Logistic Regression
from sklearn.linear_model import LogisticRegression
# Sample dataset
X = [[0],[1],[2],[3],[4],[5]]
y = [0,0,0,1,1,1]
# Model training
model = LogisticRegression()
model.fit(X, y)
# Prediction
y_pred = model.predict([[1.5], [3.5]])
print("Predictions:", y_pred)
# Probability
print("Predicted Probabilities:\n", model.predict_proba([[1.5],[3.5]]))
