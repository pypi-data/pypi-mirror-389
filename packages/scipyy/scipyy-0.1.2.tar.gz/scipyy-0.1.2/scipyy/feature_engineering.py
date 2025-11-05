# Practical - 6A
import pandas as pd



# Read CSV file
df = pd.read_csv(r"")  # Make sure to replace with your actual csv file path

# Min-Max Normalization Function
def min_max_normalize(column):
    return (column - column.min()) / (column.max() - column.min())

# Apply normalization on numerical columns
df['Age_norm'] = min_max_normalize(df['Age'])
df['Income_norm'] = min_max_normalize(df['Income'])
df['Score_norm'] = min_max_normalize(df['Score'])

# Show original and normalized values
print(df[['Age', 'Age_norm', 'Income', 'Income_norm', 'Score', 'Score_norm']])


# Practical - 6B
import pandas as pd

df = pd.read_csv(r"")

# Standardization Function (Z-score)
def standardize(column):
    mean = column.mean()
    std = column.std()
    return (column - mean) / std

# Apply to numeric columns
df['Age_std_manual'] = standardize(df['Age'])
df['Income_std_manual'] = standardize(df['Income'])
df['Score_std_manual'] = standardize(df['Score'])

# Print original and standardized values
print(df[['Age', 'Age_std_manual', 'Income', 'Income_std_manual', 'Score', 'Score_std_manual']])


# Practical - 6C
import pandas as pd


df = pd.read_csv(r"")

df['Gender_label'] = df['gender'].map({'m': 1, 'f': 0})


print(df[['gender', 'Gender_label']])


# Practical - 6D (i)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

data = {'Skewed_Feature': np.random.exponential(scale=1000, size=500)}
df = pd.DataFrame(data)

# Add transformed columns
df['Log_Transform'] = np.log1p(df['Skewed_Feature'])
df['Sqrt_Transform'] = np.sqrt(df['Skewed_Feature'])

plt.figure(figsize=(15, 5))

# Original distribution
plt.subplot(1, 3, 1)
sns.histplot(df['Skewed_Feature'], kde=True, color='skyblue')
plt.title('Original Skewed Data')

# Log-transformed
plt.subplot(1, 3, 2)
sns.histplot(df['Log_Transform'], kde=True, color='orange')
plt.title('Log Transformed')

# Sqrt-transformed
plt.subplot(1, 3, 3)
sns.histplot(df['Sqrt_Transform'], kde=True, color='green')
plt.title('Sqrt Transformed')

plt.tight_layout()
plt.show()


# Practical - 6D (ii)

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

np.random.seed(42)
data = {'Left_Skewed_Feature': np.random.beta(a=6, b=2, size=500) * 100}
df = pd.DataFrame(data)

# Square transformation (to reduce left skew)
df['Squared_Transform'] = df['Left_Skewed_Feature'] ** 2

plt.figure(figsize=(12, 5))

# Original
plt.subplot(1, 2, 1)
sns.histplot(df['Left_Skewed_Feature'], kde=True, color='purple')
plt.title('Original Left-Skewed')

# Transformed
plt.subplot(1, 2, 2)
sns.histplot(df['Squared_Transform'], kde=True, color='teal')
plt.title('After Square Transformation')

plt.tight_layout()
plt.show()
