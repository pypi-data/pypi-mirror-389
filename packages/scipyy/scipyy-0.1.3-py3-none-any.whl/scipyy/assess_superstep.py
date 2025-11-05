# Practical 5A  Handling Missing Values with Mean Imputation
import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt



# Step 1: Create data with missing values
np.random.seed(42)
marks = np.random.randint(20, 100, size=20).astype(float)
marks[[2, 5, 11, 15, 19]] = np.nan

df = pd.DataFrame({'Marks': marks})
print("Original Data with Missing Values:")
print(df)

# Step 2: Fill missing values using mean
df_filled = df.fillna(df['Marks'].mean())
print("\nData After Mean Imputation:")
print(df_filled)

# Step 3: Plot before and after side by side
fig, ax = plt.subplots(1, 2, figsize=(10, 4))

sns.histplot(df['Marks'], kde=True, ax=ax[0])
ax[0].set_title("Before Mean Imputation")
ax[0].set_xlabel("Marks")

sns.histplot(df_filled['Marks'], kde=True, ax=ax[1])
ax[1].set_title("After Mean Imputation")
ax[1].set_xlabel("Marks")

plt.tight_layout()
plt.show()


#5B. Handling Missing Values with Median Imputation# Practical 5B


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Step 1: Create data with missing values
np.random.seed(24)
marks = np.random.randint(20, 120, size=20).astype(float)
marks[[3, 7, 9, 12, 17]] = np.nan

df = pd.DataFrame({'Marks': marks})
print("Original Data with Missing Values:")
print(df)

# Step 2: Fill missing values using median
df_filled = df.fillna(df['Marks'].median())
print("\nData After Median Imputation:")
print(df_filled)

# Step 3: Plot before and after side by side
fig, ax = plt.subplots(1, 2, figsize=(10, 4))

sns.histplot(df['Marks'], kde=True, ax=ax[0])
ax[0].set_title("Before Median Imputation")
ax[0].set_xlabel("Marks")

sns.histplot(df_filled['Marks'], kde=True, ax=ax[1])
ax[1].set_title("After Median Imputation")
ax[1].set_xlabel("Marks")

plt.tight_layout()
plt.show()

# Practical 5C  Handling Outliers using IQR Method (for non-normal/skewed data)


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt

# Step 1: Create non-normal (exponential) data
np.random.seed(101)
non_normal_data = np.random.exponential(scale=2.0, size=100)
df = pd.DataFrame({'Value': non_normal_data})

# Step 2: Detect outliers using IQR
Q1 = df['Value'].quantile(0.25)
Q3 = df['Value'].quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Step 3: Filter the data
df_filtered = df[(df['Value'] >= lower_bound) & (df['Value'] <= upper_bound)]

# Step 4: Plot side-by-side boxplots
fig, ax = plt.subplots(1, 2, figsize=(12, 4))

sns.boxplot(x=df['Value'], ax=ax[0])
ax[0].set_title("Before Removing Outliers")

sns.boxplot(x=df_filtered['Value'], ax=ax[1])
ax[1].set_title("After Removing Outliers (IQR Method)")

plt.tight_layout()
plt.show()


# 5 d : # Practical 5D Handling Outliers using Z-Score Method (for normal distribution)


import pandas as pd
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy import stats

# Step 1: Generate normally distributed data
np.random.seed(202)
normal_data = np.random.normal(loc=50, scale=10, size=100)
df = pd.DataFrame({'Value': normal_data})

# Step 2: Calculate Z-scores and remove outliers
z_scores = np.abs(stats.zscore(df['Value']))
df_filtered = df[z_scores < 3]

# Step 3: Plot side-by-side histograms
fig, ax = plt.subplots(1, 2, figsize=(12, 4))

sns.histplot(df['Value'], kde=True, ax=ax[0])
ax[0].set_title("Before Removing Outliers")

sns.histplot(df_filtered['Value'], kde=True, ax=ax[1])
ax[1].set_title("After Removing Outliers (Z-score Method)")

plt.tight_layout()
plt.show()

