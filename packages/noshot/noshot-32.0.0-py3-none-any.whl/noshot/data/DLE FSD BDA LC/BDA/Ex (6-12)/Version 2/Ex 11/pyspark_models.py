from pyspark.sql import SparkSession
from pyspark.sql.functions import col
from pyspark.ml import Pipeline
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.classification import LogisticRegression, LinearSVC, DecisionTreeClassifier
from pyspark.sql.types import StructType, StructField, DoubleType, IntegerType
import sys

# 1) Spark session
spark = SparkSession.builder \
    .appName("MLlib_Comparison_LogReg_SVM_DT_CSV") \
    .getOrCreate()

# 2) Command-line args for dataset path and config
# Expecting: python train_evaluate_spark_models_from_csv.py /path/to/dataset.csv
if len(sys.argv) < 2:
    print("Usage: python train_evaluate_spark_models_from_csv.py <path_to_csv_dataset>")
    sys.exit(1)

csv_path = sys.argv[1]

# 3) Load dataset
# If you know column types, you can specify a schema for faster loading.
# Here we infer schema for simplicity, but you can provide a deterministic schema if you prefer.
df = spark.read.csv(csv_path, header=True, inferSchema=True)

# 4) Configuration: adjust these to match your dataset
# - label column name
# - feature column names (list of all numeric feature columns)
label_col = "label"
feature_cols = [c for c in df.columns if c != label_col]

# Optional: ensure only numeric feature columns are used
# If there are non-numeric columns (like an ID), explicitly list features instead of deriving from all columns
# Example:
# feature_cols = ["feature1","feature2","feature3"]

# 5) Train-test split
train_df, test_df = df.randomSplit([0.8, 0.2], seed=42)

# 6) Features assembly
assembler = VectorAssembler(inputCols=feature_cols, outputCol="features")

# StandardScaler (helps LR and LinearSVC)
scaler = StandardScaler(inputCol="features", outputCol="scaledFeatures", withStd=True, withMean=True)

# Define models
lr = LogisticRegression(featuresCol="scaledFeatures", labelCol=label_col, maxIter=100, regParam=0.1)
svm = LinearSVC(featuresCol="scaledFeatures", labelCol=label_col, maxIter=1000)
dt = DecisionTreeClassifier(featuresCol="features", labelCol=label_col)

# Pipelines
lr_pipe = Pipeline(stages=[assembler, scaler, lr])
svm_pipe = Pipeline(stages=[assembler, scaler, svm])
dt_pipe = Pipeline(stages=[assembler, dt])

# 7) Train models
lr_model = lr_pipe.fit(train_df)
svm_model = svm_pipe.fit(train_df)
dt_model = dt_pipe.fit(train_df)

# 8) Predictions
lr_pred = lr_model.transform(test_df)
svm_pred = svm_model.transform(test_df)
dt_pred = dt_model.transform(test_df)

# 9) Evaluation helper
def compute_metrics(pred_df, label_col="label", pred_col="prediction"):
    tp = pred_df.filter((col(label_col) == 1) & (col(pred_col) == 1)).count()
    tn = pred_df.filter((col(label_col) == 0) & (col(pred_col) == 0)).count()
    fp = pred_df.filter((col(label_col) == 0) & (col(pred_col) == 1)).count()
    fn = pred_df.filter((col(label_col) == 1) & (col(pred_col) == 0)).count()
    precision = tp / float(tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / float(tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / float(precision + recall) if (precision + recall) > 0 else 0.0
    return {"TP": tp, "TN": tn, "FP": fp, "FN": fn, "Precision": precision, "Recall": recall, "F1": f1}

# 10) Compute metrics
lr_metrics = compute_metrics(lr_pred)
svm_metrics = compute_metrics(svm_pred)
dt_metrics = compute_metrics(dt_pred)

# 11) Display results
def pretty_print(name, metrics):
    print(f"Model: {name}")
    print(f"  TP={metrics['TP']}, TN={metrics['TN']}, FP={metrics['FP']}, FN={metrics['FN']}")
    print(f"  Precision={metrics['Precision']:.4f}, Recall={metrics['Recall']:.4f}, F1={metrics['F1']:.4f}")
    print()

pretty_print("Logistic Regression", lr_metrics)
pretty_print("Linear SVM (LinearSVC)", svm_metrics)
pretty_print("Decision Tree", dt_metrics)

# 12) Simple comparison
comparison = [
    ("LogReg", lr_metrics["Precision"], lr_metrics["Recall"], lr_metrics["F1"]),
    ("LinearSVC", svm_metrics["Precision"], svm_metrics["Recall"], svm_metrics["F1"]),
    ("DecisionTree", dt_metrics["Precision"], dt_metrics["Recall"], dt_metrics["F1"])
]

print("Summary (Precision / Recall / F1):")
for name, p, r, f1 in comparison:
    print(f" - {name}: Precision={p:.4f}, Recall={r:.4f}, F1={f1:.4f}")

# Optional: quick matplotlib chart
try:
    import matplotlib.pyplot as plt
    labels = [row[0] for row in comparison]
    precisions = [row[1] for row in comparison]
    recalls = [row[2] for row in comparison]
    f1s = [row[3] for row in comparison]

    x = range(len(labels))
    width = 0.25

    plt.figure(figsize=(8,5))
    plt.bar([i - width for i in x], precisions, width=width, label="Precision")
    plt.bar(x, recalls, width=width, label="Recall")
    plt.bar([i + width for i in x], f1s, width=width, label="F1")
    plt.xticks(x, labels)
    plt.ylim(0, 1)
    plt.ylabel("Score")
    plt.title("Model Performance: Precision / Recall / F1")
    plt.legend()
    plt.tight_layout()
    plt.show()
except Exception as e:
    print("Plotting not available:", e)

# 13) Cleanup
spark.stop()