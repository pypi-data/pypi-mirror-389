def doc():
    print(r"""
| Function | Description |
|:--------:|-------------|
| characteristics() |  Numeric Col Analysis(distribution, skewness/kurtosis, histogram, box-plot, q-q plot), Categorical Col Analysis(Categorical Distribution), Correlation HeatMap |
| cleaning() | missing values, duplicates, outliers |
| fiveNumSum() | five number summary |
| dataSmoothing() | smoothing, normalization, redundancy (Pearson, Chi Square), discretization (equal width, equal frequency, custom width binning) |
| dimRed() | PCA, Feature Selection |
""")
    
def characteristics():
    print(r"""
===============================CELL 1====================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif, chi2, RFE
from sklearn.ensemble import RandomForestClassifier

===============================CELL 2====================================
df = pd.read_csv('your_dataset.csv')

print("="*80)
print("TASK 1: IDENTIFY CHARACTERISTICS & VISUALIZE")
print("="*80)

# Basic Information
print("\n1. Dataset Shape:")
print(f"Rows: {df.shape[0]}, Columns: {df.shape[1]}")

print("\n2. Data Types:")
print(df.dtypes)

print("\n3. First Few Rows:")
print(df.head())

print("\n4. Statistical Summary:")
print(df.describe(include='all'))

print("\n5. Missing Values:")
print(df.isnull().sum())

print("\n6. Duplicate Rows:")
print(f"Number of duplicates: {df.duplicated().sum()}")

# Separate numeric and categorical columns
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

print(f"\nNumeric Columns: {numeric_cols}")
print(f"Categorical Columns: {categorical_cols}")

# Distribution Analysis for Numeric Columns
print("\n7. Distribution Analysis (Skewness & Kurtosis):")
for col in numeric_cols:
    skew = df[col].skew()
    kurt = df[col].kurtosis()
    print(f"{col}: Skewness={skew:.3f}, Kurtosis={kurt:.3f}")

# VISUALIZATIONS
fig, axes = plt.subplots(len(numeric_cols), 3, figsize=(15, 5*len(numeric_cols)))
if len(numeric_cols) == 1:
    axes = axes.reshape(1, -1)

for idx, col in enumerate(numeric_cols):
    # Histogram
    axes[idx, 0].hist(df[col].dropna(), bins=30, edgecolor='black', alpha=0.7)
    axes[idx, 0].set_title(f'Histogram - {col}')
    axes[idx, 0].set_xlabel(col)
    axes[idx, 0].set_ylabel('Frequency')
    
    # Box Plot
    axes[idx, 1].boxplot(df[col].dropna())
    axes[idx, 1].set_title(f'Box Plot - {col}')
    axes[idx, 1].set_ylabel(col)
    
    # Q-Q Plot
    stats.probplot(df[col].dropna(), dist="norm", plot=axes[idx, 2])
    axes[idx, 2].set_title(f'Q-Q Plot - {col}')

plt.tight_layout()
plt.savefig('numeric_distributions.png', dpi=300, bbox_inches='tight')
plt.show()

# Categorical Variables
if categorical_cols:
    n_cats = len(categorical_cols)
    fig, axes = plt.subplots(n_cats, 1, figsize=(12, 5*n_cats))
    if n_cats == 1:
        axes = [axes]
    
    for idx, col in enumerate(categorical_cols):
        value_counts = df[col].value_counts().head(10)
        axes[idx].bar(range(len(value_counts)), value_counts.values)
        axes[idx].set_xticks(range(len(value_counts)))
        axes[idx].set_xticklabels(value_counts.index, rotation=45, ha='right')
        axes[idx].set_title(f'Value Counts - {col}')
        axes[idx].set_ylabel('Count')
    
    plt.tight_layout()
    plt.savefig('categorical_distributions.png', dpi=300, bbox_inches='tight')
    plt.show()

# Correlation Heatmap
if len(numeric_cols) > 1:
    plt.figure(figsize=(10, 8))
    sns.heatmap(df[numeric_cols].corr(), annot=True, cmap='coolwarm', center=0, fmt='.2f')
    plt.title('Correlation Matrix')
    plt.tight_layout()
    plt.savefig('correlation_heatmap.png', dpi=300, bbox_inches='tight')
    plt.show()
""")
def cleaning():
    print(r"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif, chi2, RFE
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv('your_dataset.csv')

print("\n" + "="*80)
print("TASK 2: DATA CLEANING")
print("="*80)

df_cleaned = df.copy()

print("\n1. Handling Missing Values:")
print(f"Total missing values: {df_cleaned.isnull().sum().sum()}")

# Strategy for missing values
for col in df_cleaned.columns:
    missing_pct = (df_cleaned[col].isnull().sum() / len(df_cleaned)) * 100
    
    if missing_pct > 0:
        print(f"\n{col}: {missing_pct:.2f}% missing")
        
        if missing_pct > 50:
            print(f"  -> Dropping column (>50% missing)")
            df_cleaned.drop(col, axis=1, inplace=True)
        elif df_cleaned[col].dtype in [np.float64, np.int64]:
            median_val = df_cleaned[col].median()
            df_cleaned[col].fillna(median_val, inplace=True)
            print(f"  -> Filled with median: {median_val}")
        else:
            mode_val = df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 'Unknown'
            df_cleaned[col].fillna(mode_val, inplace=True)
            print(f"  -> Filled with mode: {mode_val}")

print("\n2. Handling Duplicates:")
duplicates = df_cleaned.duplicated().sum()
if duplicates > 0:
    df_cleaned.drop_duplicates(inplace=True)
    print(f"Removed {duplicates} duplicate rows")
else:
    print("No duplicates found")

print("\n3. Handling Outliers (Optional - IQR Method):")
# Update numeric columns after cleaning
numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns.tolist()

for col in numeric_cols:
    Q1 = df_cleaned[col].quantile(0.25)
    Q3 = df_cleaned[col].quantile(0.75)
    IQR = Q3 - Q1
    lower = Q1 - 1.5 * IQR
    upper = Q3 + 1.5 * IQR
    outliers = df_cleaned[(df_cleaned[col] < lower) | (df_cleaned[col] > upper)][col].count()
    print(f"{col}: {outliers} outliers detected")

print(f"\n4. Final Dataset Shape: {df_cleaned.shape}")
""")
def fiveNumSum():
    print(r"""
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from sklearn.preprocessing import StandardScaler, MinMaxScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import SelectKBest, f_classif, chi2, RFE
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv('your_dataset.csv')

df_cleaned = df.copy()

numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns.tolist()

print("\n" + "="*80)
print("TASK 3: FIVE NUMBER SUMMARY & STATISTICS")
print("="*80)

for col in numeric_cols:
    print(f"\n--- {col} ---")
    data = df_cleaned[col].dropna()
    
    # Five Number Summary
    minimum = data.min()
    q1 = data.quantile(0.25)
    median = data.median()
    q3 = data.quantile(0.75)
    maximum = data.max()
    
    print(f"Five Number Summary:")
    print(f"  Minimum: {minimum}")
    print(f"  Q1 (25%): {q1}")
    print(f"  Median (50%): {median}")
    print(f"  Q3 (75%): {q3}")
    print(f"  Maximum: {maximum}")
    
    # Additional Statistics
    mode_val = data.mode().values[0] if len(data.mode()) > 0 else "No unique mode"
    midrange = (minimum + maximum) / 2
    iqr = q3 - q1
    
    print(f"\nAdditional Statistics:")
    print(f"  Mode: {mode_val}")
    print(f"  Midrange: {midrange}")
    print(f"  IQR: {iqr}")
    print(f"  Mean: {data.mean()}")
    print(f"  Std Dev: {data.std()}")
    print(f"  Variance: {data.var()}")
    
    # Outlier Detection using Quartile Method
    lower_bound = q1 - 1.5 * iqr
    upper_bound = q3 + 1.5 * iqr
    outliers = data[(data < lower_bound) | (data > upper_bound)]
    
    print(f"\nOutlier Detection (IQR Method):")
    print(f"  Lower Bound: {lower_bound}")
    print(f"  Upper Bound: {upper_bound}")
    print(f"  Number of Outliers: {len(outliers)}")
    if len(outliers) > 0 and len(outliers) <= 10:
        print(f"  Outlier Values: {outliers.values}")
    
    # Z-Score Method
    z_scores = np.abs(stats.zscore(data))
    z_outliers = data[z_scores > 3]
    print(f"  Outliers (Z-score > 3): {len(z_outliers)}")

""")
def dataSmoothing():
    print(r"""
import pandas as pd
import numpy as np
from scipy import stats
import matplotlib.pyplot as plt
from sklearn.preprocessing import MinMaxScaler, StandardScaler

df = pd.read_csv('your_dataset.csv')

df_cleaned = df.copy()

numeric_cols = df_cleaned.select_dtypes(include=[np.number]).columns.tolist()

categorical_cols = df_cleaned.select_dtypes(include=['object', 'category']).columns.tolist()

print("\n" + "="*80)
print("TASK 4: SMOOTHING, NORMALIZATION & REDUNDANCY")
print("="*80)

print("\n1. DATA SMOOTHING (Mean Binning):")

if len(numeric_cols) > 0:
    sample_col = numeric_cols[0]
    bins = 5  
    
    df_cleaned[f'{sample_col}_binned'] = pd.cut(df_cleaned[sample_col], bins=bins)
    df_cleaned[f'{sample_col}_smoothed'] = df_cleaned.groupby(f'{sample_col}_binned')[sample_col].transform('mean')

    plt.figure(figsize=(12, 4))
    plt.plot(df_cleaned[sample_col].head(50), label='Original', marker='o')
    plt.plot(df_cleaned[f'{sample_col}_smoothed'].head(50), label='Smoothed (Mean Binning)', marker='s')
    plt.title(f'Data Smoothing (Mean Binning) - {sample_col}')
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig('data_smoothing_mean_binning.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    print(f"Applied mean binning smoothing on {sample_col} using {bins} bins")

print("\n2. DATA NORMALIZATION:")

# Min-Max Normalization
print("\na) Min-Max Normalization (0-1 scaling):")
scaler_minmax = MinMaxScaler()
df_minmax = pd.DataFrame(
    scaler_minmax.fit_transform(df_cleaned[numeric_cols]),
    columns=[f'{col}_minmax' for col in numeric_cols]
)
print(df_minmax.head())

# Z-Score Normalization
print("\nb) Z-Score Normalization (Standardization):")
scaler_standard = StandardScaler()
df_standard = pd.DataFrame(
    scaler_standard.fit_transform(df_cleaned[numeric_cols]),
    columns=[f'{col}_zscore' for col in numeric_cols]
)
print(df_standard.head())

# Decimal Scaling
print("\nc) Decimal Scaling:")
df_decimal = pd.DataFrame()
for col in numeric_cols:
    max_val = df_cleaned[col].abs().max()
    j = len(str(int(max_val)))
    df_decimal[f'{col}_decimal'] = df_cleaned[col] / (10 ** j)
print(df_decimal.head())

print("\n3. REDUNDANCY ANALYSIS:")

print("\na) Pearson Correlation (Numeric Variables):")
if len(numeric_cols) > 1:
    corr_matrix = df_cleaned[numeric_cols].corr()
    print(corr_matrix)
    
    # Identify highly correlated pairs
    high_corr_pairs = []
    for i in range(len(corr_matrix.columns)):
        for j in range(i+1, len(corr_matrix.columns)):
            if abs(corr_matrix.iloc[i, j]) > 0.8:
                high_corr_pairs.append((corr_matrix.columns[i], corr_matrix.columns[j], corr_matrix.iloc[i, j]))
    
    if high_corr_pairs:
        print("\nHighly Correlated Pairs (|r| > 0.8):")
        for pair in high_corr_pairs:
            print(f"  {pair[0]} <-> {pair[1]}: {pair[2]:.3f}")
    else:
        print("\nNo highly correlated pairs found (|r| > 0.8)")

print("\nb) Chi-Square Test (Categorical Variables):")
categorical_cols = df_cleaned.select_dtypes(include=['object', 'category']).columns.tolist()

if len(categorical_cols) >= 2:
    cat1, cat2 = categorical_cols[0], categorical_cols[1]
    contingency_table = pd.crosstab(df_cleaned[cat1], df_cleaned[cat2])
    chi2_stat, p_value, dof, expected = stats.chi2_contingency(contingency_table)
    
    print(f"\nChi-Square Test: {cat1} vs {cat2}")
    print(f"  Chi-Square Statistic: {chi2_stat:.4f}")
    print(f"  P-value: {p_value:.4f}")
    print(f"  Degrees of Freedom: {dof}")
    
    if p_value < 0.05:
        print(f"  Result: Variables are dependent (reject H0)")
    else:
        print(f"  Result: Variables are independent (fail to reject H0)")
else:
    print("Not enough categorical variables for Chi-Square test")

print("\n4. DISCRETIZATION (Intuitive Partitioning):")
if len(numeric_cols) > 0:
    sample_col = numeric_cols[0]
    
    # Equal-width binning
    df_cleaned[f'{sample_col}_equal_width'] = pd.cut(df_cleaned[sample_col], bins=5, labels=['Very Low', 'Low', 'Medium', 'High', 'Very High'])
    
    # Equal-frequency binning
    df_cleaned[f'{sample_col}_equal_freq'] = pd.qcut(df_cleaned[sample_col], q=5, labels=['Q1', 'Q2', 'Q3', 'Q4', 'Q5'], duplicates='drop')
    
    # Custom binning (example)
    bins = [df_cleaned[sample_col].min(), df_cleaned[sample_col].quantile(0.33), 
            df_cleaned[sample_col].quantile(0.67), df_cleaned[sample_col].max()]
    df_cleaned[f'{sample_col}_custom'] = pd.cut(df_cleaned[sample_col], bins=bins, labels=['Low', 'Medium', 'High'], include_lowest=True)
    
    print(f"\nDiscretization applied on {sample_col}:")
    print("\nEqual-Width Binning:")
    print(df_cleaned[f'{sample_col}_equal_width'].value_counts().sort_index())
    print("\nEqual-Frequency Binning:")
    print(df_cleaned[f'{sample_col}_equal_freq'].value_counts().sort_index())

""")
def dimRed():
    print(r"""
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.feature_selection import VarianceThreshold, SelectKBest, f_classif
from sklearn.feature_selection import RFE
from sklearn.ensemble import RandomForestClassifier

df = pd.read_csv('your_dataset.csv')

df_cleaned = df.copy()

print("\n" + "="*80)
print("TASK 5: DIMENSIONALITY REDUCTION & FEATURE SELECTION")
print("="*80)

# Prepare data for dimensionality reduction
numeric_cols_clean = df_cleaned.select_dtypes(include=[np.number]).columns.tolist()
# Remove any smoothed or normalized columns for clean analysis
numeric_cols_original = [col for col in numeric_cols_clean if not any(x in col for x in ['_smoothed', '_minmax', '_zscore', '_decimal'])]

if len(numeric_cols_original) > 1:
    X = df_cleaned[numeric_cols_original].dropna()
    
    print("\n1. PRINCIPAL COMPONENT ANALYSIS (PCA):")
    
    # Standardize before PCA
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Apply PCA
    pca = PCA()
    X_pca = pca.fit_transform(X_scaled)
    
    print(f"Original Features: {X.shape[1]}")
    print(f"\nExplained Variance Ratio:")
    for i, var in enumerate(pca.explained_variance_ratio_):
        print(f"  PC{i+1}: {var:.4f} ({var*100:.2f}%)")
    
    print(f"\nCumulative Explained Variance:")
    cumsum = np.cumsum(pca.explained_variance_ratio_)
    for i, var in enumerate(cumsum):
        print(f"  Up to PC{i+1}: {var:.4f} ({var*100:.2f}%)")
    
    # Determine optimal components (95% variance)
    n_components = np.argmax(cumsum >= 0.95) + 1
    print(f"\nComponents needed for 95% variance: {n_components}")
    
    # Visualize
    plt.figure(figsize=(12, 5))
    
    plt.subplot(1, 2, 1)
    plt.bar(range(1, len(pca.explained_variance_ratio_)+1), pca.explained_variance_ratio_)
    plt.xlabel('Principal Component')
    plt.ylabel('Explained Variance Ratio')
    plt.title('Scree Plot')
    plt.grid(True)
    
    plt.subplot(1, 2, 2)
    plt.plot(range(1, len(cumsum)+1), cumsum, marker='o')
    plt.axhline(y=0.95, color='r', linestyle='--', label='95% Variance')
    plt.xlabel('Number of Components')
    plt.ylabel('Cumulative Explained Variance')
    plt.title('Cumulative Variance Explained')
    plt.legend()
    plt.grid(True)
    
    plt.tight_layout()
    plt.savefig('pca_analysis.png', dpi=300, bbox_inches='tight')
    plt.show()
    
    # Apply optimal PCA
    pca_optimal = PCA(n_components=n_components)
    X_pca_reduced = pca_optimal.fit_transform(X_scaled)
    print(f"\nReduced dimensions: {X.shape[1]} -> {n_components}")
    
    
print("\n" + "="*80)
print("ANALYSIS COMPLETE!")
print("="*80)
print("\nAll visualizations have been saved as PNG files.")
print("Dataset cleaned and analyzed successfully.")
""")
