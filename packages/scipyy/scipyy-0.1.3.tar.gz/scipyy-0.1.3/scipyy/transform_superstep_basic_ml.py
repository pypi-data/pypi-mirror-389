# Logistic Regression 8A


import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.datasets import load_iris
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report
from sklearn.preprocessing import StandardScaler

# Load the iris dataset
iris = load_iris()
X = iris.data  # Features
y = iris.target  # Target (0: setosa, 1: versicolor, 2: virginica)

# Create a binary classification problem by dropping one species
# Let's keep only setosa (0) and versicolor (1), drop virginica (2)
mask = y != 2  # Keep only classes 0 and 1
X_binary = X[mask]
y_binary = y[mask]

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(
    X_binary, y_binary, test_size=0.2, random_state=42, stratify=y_binary
)

# Standardize the features 
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train)
X_test_scaled = scaler.transform(X_test)

# Create and train the logistic regression model
model = LogisticRegression(random_state=42, max_iter=1000)
model.fit(X_train_scaled, y_train)

# Make predictions
y_pred = model.predict(X_test_scaled)
y_pred_proba = model.predict_proba(X_test_scaled)

# Calculate metrics
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel Performance:")
print(f"Accuracy: {accuracy:.3f}")

# Confusion matrix
cm = confusion_matrix(y_test, y_pred)
print(f"\nConfusion Matrix:")
print(cm)


# Prac 8b
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_diabetes
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score

# Load a simple dataset
data = load_diabetes()
X = data.data[:, 2:3]  # Use only one feature for simplicity (BMI)
y = data.target
# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
# Create and train the linear regression model
model = LinearRegression()
model.fit(X_train, y_train)
# Make predictions
y_pred = model.predict(X_test)
# Calculate metrics
mse = mean_squared_error(y_test, y_pred)
r2 = r2_score(y_test, y_pred)
print(f"\nModel Performance:")
print(f"Mean Squared Error: {mse:.2f}")
print(f"R² Score: {r2:.3f}")
# Plot the results
plt.figure(figsize=(10, 6))
# Plot training data
plt.scatter(X_train, y_train, color='blue', alpha=0.7, label='Training Data', s=30)
# Plot test data
plt.scatter(X_test, y_test, color='green', alpha=0.7, label='Test Data', s=30)
# Plot regression line
x_line = np.linspace(X.min(), X.max(), 100).reshape(-1, 1)
y_line = model.predict(x_line)
plt.plot(x_line, y_line, color='red', linewidth=3, label='Regression Line')
plt.xlabel('BMI')
plt.ylabel('Disease Progression')
plt.title('Simple Linear Regression: BMI vs Disease Progression')
plt.legend()
plt.grid(True, alpha=0.3)
plt.show()
# Print the regression equation
print(f"\nRegression Equation:")
print(f"y = {model.coef_[0]:.3f} * BMI + {model.intercept_:.3f}")


#Prac 8C K-Means clustering
import numpy as np
import matplotlib.pyplot as plt
from sklearn.datasets import load_iris
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import plotly.express as px
import pandas as pd

# Load the iris dataset
iris = load_iris()
X = iris.data
feature_names = iris.feature_names
# Standardize the features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
# Apply K-Means clustering
kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
cluster_labels = kmeans.fit_predict(X_scaled)
# Create DataFrame for plotting
df = pd.DataFrame(X, columns=feature_names)
df['cluster'] = cluster_labels
df['cluster_str'] = df['cluster'].astype(str)  # For plotly coloring
# 2D Scatter Plot using Matplotlib
plt.figure(figsize=(10, 6))
scatter = plt.scatter(X[:, 0], X[:, 1], c=cluster_labels, cmap='viridis', 
                     alpha=0.8, s=50, edgecolor='black', linewidth=0.5)
plt.xlabel('Sepal Length (cm)')
plt.ylabel('Sepal Width (cm)')
plt.title('K-Means Clustering on Iris Dataset (2D)')
plt.colorbar(scatter, label='Cluster')
plt.grid(True, alpha=0.3)
plt.show()
# 3D Interactive Plot using Plotly (optional)
fig = px.scatter_3d(df, 
                    x='sepal length (cm)', 
                    y='sepal width (cm)', 
                    z='petal length (cm)',
                    color='cluster_str',
                    title='K-Means Clustering on Iris Dataset (3D Interactive)',
                    labels={'cluster_str': 'Cluster'},
                    opacity=0.8,
                    size_max=10)
fig.update_layout(margin=dict(l=0, r=0, b=0, t=30))
fig.show()
