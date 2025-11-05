# Confusion Matrix
from sklearn.metrics import confusion_matrix, classification_report
# Sample true and predicted labels
y_true = [0,1,0,1,0,1]
y_pred = [0,1,0,0,0,1]
# Confusion matrix
cm = confusion_matrix(y_true, y_pred)
print("Confusion Matrix:\n", cm)
# Classification report
print("Classification Report:\n", classification_report(y_true, y_pred))
