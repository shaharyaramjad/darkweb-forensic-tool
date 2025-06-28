import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder, StandardScaler
from sklearn.metrics import classification_report
from sklearn.metrics import confusion_matrix
from sklearn.impute import SimpleImputer
import joblib
import numpy as np

# Load sample data
df = pd.read_csv("C:/Users/moham/Downloads/Darknet.csv")  # Use smaller version of your dataset

# Drop rows with missing values
df.dropna(inplace=True)

# Identify feature columns (numerical)
numeric_features = df.select_dtypes(include=['int64', 'float64']).columns.tolist()

# Identify target column
target_col = 'Label' if 'Label' in df.columns else df.columns[-1]

# Drop target from feature list
if target_col in numeric_features:
    numeric_features.remove(target_col)

X = df[numeric_features]
y = df[target_col]

# Clean data: handle infinite values and outliers
# 1. Handle Infinite values
inf_threshold = 0.5  # Drop column if > 50% of values are infinite
cols_to_drop = [
    col for col in X.columns if np.isinf(X[col].values).sum() / len(X) > inf_threshold
]

if cols_to_drop:
    X.drop(columns=cols_to_drop, inplace=True)
    print(f"Dropped columns with >{int(inf_threshold * 100)}% infinite values: {cols_to_drop}")

# Replace remaining infinite values with NaN to be imputed
X.replace([np.inf, -np.inf], np.nan, inplace=True)

# Impute NaN values (making them finite) using the median
imputer = SimpleImputer(strategy='median')
# Preserve index and columns
X = pd.DataFrame(imputer.fit_transform(X), columns=X.columns, index=X.index)

# Remove outliers using IQR method
Q1 = X.quantile(0.25)
Q3 = X.quantile(0.75)
IQR = Q3 - Q1
lower_bound = Q1 - 1.5 * IQR
upper_bound = Q3 + 1.5 * IQR

# Create mask for outliers and apply it to both X and y
outlier_mask = ((X >= lower_bound) & (X <= upper_bound)).all(axis=1)
X = X[outlier_mask]
y = y.loc[X.index]  # Use .loc with index after filtering X

# Reset indices for downstream processing
X.reset_index(drop=True, inplace=True)
y.reset_index(drop=True, inplace=True)

print(f"Data shape after cleaning: {X.shape}")
print(f"Number of samples: {len(X)}")

# Encode labels
le = LabelEncoder()
y_encoded = le.fit_transform(y)

# Normalize features
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)

# Split data
X_train, X_test, y_train, y_test = train_test_split(X_scaled, y_encoded, test_size=0.3, random_state=42)

# Train classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Evaluate
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred, target_names=le.classes_))

# Print confusion matrix
cm = confusion_matrix(y_test, y_pred)
print("Confusion Matrix:")
print(cm)

# Save model & label encoder
joblib.dump(model, "risk_model.pkl")
joblib.dump(le, "label_encoder.pkl")
joblib.dump(scaler, "scaler.pkl")

print("Model training completed successfully!")
print("Files saved: risk_model.pkl, label_encoder.pkl, scaler.pkl")
