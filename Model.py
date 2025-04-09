import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import classification_report
import xgboost as xgb

# Загрузка данных
df = pd.read_csv("clean_football_matches.csv", low_memory=False)
print(df)
# Целевая переменная
label_encoder = LabelEncoder()
y_encoded = label_encoder.fit_transform(df["FTR"])

# Только числовые признаки
X = df.select_dtypes(include=["float64", "int64"]).drop(columns=["FTHG", "FTAG"], errors="ignore")


# Обновим y под X
y_encoded = label_encoder.transform(df.loc[X.index, "FTR"])

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)

# Обучение XGBoost
model = xgb.XGBClassifier(
    n_estimators=100,
    max_depth=5,
    learning_rate=0.1,
    use_label_encoder=False,
    eval_metric="mlogloss",
    tree_method="hist"
)
model.fit(X_train, y_train)

# Оценка
y_pred = model.predict(X_test)
print(classification_report(y_test, y_pred, target_names=label_encoder.classes_))
