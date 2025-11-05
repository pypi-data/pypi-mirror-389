# Practical 10A

import pandas as pd
import matplotlib.pyplot as plt

marks = [45, 60, 55, 70, 65, 50, 75, 80, 60, 55]

df = pd.DataFrame({"Marks": marks})

# --- Descriptive Statistics ---
print("Mean:", df["Marks"].mean())
print("Median:", df["Marks"].median())
print("Mode:", df["Marks"].mode()[0])
print("Standard Deviation:", df["Marks"].std())
print("Minimum:", df["Marks"].min())
print("Maximum:", df["Marks"].max())

# Histogram
plt.hist(df["Marks"], bins=5, edgecolor="black")
plt.title("Histogram of Marks")
plt.xlabel("Marks")
plt.ylabel("Frequency")
plt.show()

# Boxplot
plt.boxplot(df["Marks"], vert=False)
plt.title("Boxplot of Marks")
plt.xlabel("Marks")
plt.show()


# Practical 10B

import pandas as pd
import matplotlib.pyplot as plt
data = {
    "Study_Hours": [2, 4, 6, 8, 10, 12],
    "Marks": [40, 60, 65, 75, 80, 90],
}
df = pd.DataFrame(data)
# --- Descriptive Relationship ---
print("Correlation between Study Hours and Marks:", df["Study_Hours"].corr(df["Marks"]))
# Scatter Plot
plt.scatter(df["Study_Hours"], df["Marks"], color="blue")
plt.title("Study Hours vs Marks")
plt.xlabel("Study Hours")
plt.ylabel("Marks")
plt.grid(True)
plt.show()
# Line Plot (to visualize trend)
plt.plot(df["Study_Hours"], df["Marks"], marker="o", linestyle="--", color="green")
plt.title("Study Hours vs Marks (Trend)")
plt.xlabel("Study Hours")
plt.ylabel("Marks")
plt.grid(True)
plt.show()


# Practical 10C

import pandas as pd
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

data = {
    "Study_Hours": [2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12],
    "Sleep_Hours": [8, 8, 7, 7, 7, 6, 6, 6, 5, 5, 5],
    "Marks": [50, 52, 55, 58, 62, 66, 70, 75, 80, 85, 90]
}

df = pd.DataFrame(data)

# --- Basic Multivariate Relationships ---
print("Correlation Matrix:")
print(df.corr())

# --- 3D Visualization ---
fig = plt.figure(figsize=(8, 6))
ax = fig.add_subplot(111, projection='3d')

ax.scatter(df["Study_Hours"], df["Sleep_Hours"], df["Marks"],
           c='blue', marker='o', s=50)

ax.set_title("Multivariate Analysis: Study, Sleep, and Marks")
ax.set_xlabel("Study Hours")
ax.set_ylabel("Sleep Hours")
ax.set_zlabel("Marks")

plt.show()
