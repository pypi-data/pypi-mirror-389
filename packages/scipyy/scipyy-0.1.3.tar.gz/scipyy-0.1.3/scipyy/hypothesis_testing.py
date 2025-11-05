# Practical 7A

# One Sample t-Test
# Example: Is the average weight significantly different from 70?
from scipy import stats

# Sample data
weights = [68, 72, 71, 69, 75, 70, 74, 73]

t_stat, p_value = stats.ttest_1samp(weights, popmean=70)

print(f"T-statistic: {t_stat:.4f}")
print(f"P-value: {p_value:.4f}")

if p_value < 0.05:
    print("Reject H0: There is a significant difference from the mean 70.")
else:
    print("Fail to reject H0: No significant difference from the mean 70.")


# Practical 7B

# Two-Sample t-Test
# Example: Compare test scores of two different classes

from scipy import stats

# Two sample groups
group1 = [80, 85, 78, 90, 88]
group2 = [75, 70, 80, 78, 72]

t_stat, p_value = stats.ttest_ind(group1, group2)

print(f"T-statistic: {t_stat:.4f}")
print(f"P-value: {p_value:.4f}")

# Interpret result
if p_value < 0.05:
    print("Reject H0: There is a significant difference between the two groups.")
else:
    print("Fail to reject H0: No significant difference between the two groups.")


# Practical 7C

# Chi-Square Test of Independence
# Example: Is there a relationship between Gender and Purchase?
import scipy.stats as stats
import pandas as pd


data = [[30, 10],
        [20, 40]]

chi2, p_value, dof, expected = stats.chi2_contingency(data)

print(f"Chi-Square Statistic: {chi2:.4f}")
print(f"P-value: {p_value:.4f}")
print("Expected Frequencies:")
print(pd.DataFrame(expected))

# Interpret result
if p_value < 0.05:
    print("Reject H0: There is a significant association between gender and purchase behavior.")
else:
    print("Fail to reject H0: No significant association between gender and purchase behavior.")
