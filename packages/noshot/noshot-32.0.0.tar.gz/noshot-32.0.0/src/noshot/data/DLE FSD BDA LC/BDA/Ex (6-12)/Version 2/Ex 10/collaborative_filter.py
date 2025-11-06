from pyspark.sql import SparkSession
from pyspark.ml.recommendation import ALS
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.sql.functions import col

# Initialize Spark Session
spark = SparkSession.builder \
    .appName("CollaborativeFiltering") \
    .config("spark.sql.adaptive.enabled", "true") \
    .getOrCreate()

# Load data
file_path = "ratings.csv"
df = spark.read.csv(file_path, header=False, inferSchema=True)
df = df.withColumnRenamed("_c0", "user_id") \
       .withColumnRenamed("_c1", "item_id") \
       .withColumnRenamed("_c2", "rating") \
       .withColumnRenamed("_c3", "timestamp")

# Keep only needed columns
ratings = df.select("user_id", "item_id", "rating")

print("=== Ratings Schema ===")
ratings.printSchema()
print("=== Sample Ratings ===")
ratings.show(5)

# Split data into train and test
train, test = ratings.randomSplit([0.8, 0.2], seed=42)

# Build ALS model
als = ALS(
    maxIter=10,
    regParam=0.01,
    userCol="user_id",
    itemCol="item_id",
    ratingCol="rating",
    coldStartStrategy="drop",  # Drop users/items not in training
    nonnegative=True           # Ratings are positive
)

# Train model
model = als.fit(train)

# Generate predictions
predictions = model.transform(test)

print("=== Predictions (user, item, actual, predicted) ===")
predictions.select("user_id", "item_id", "rating", "prediction").show(10)

# Evaluate model
evaluator = RegressionEvaluator(
    metricName="rmse",
    labelCol="rating",
    predictionCol="prediction"
)

rmse = evaluator.evaluate(predictions)
print(f"Root Mean Square Error (RMSE) = {rmse:.4f}")

# Generate top 3 recommendations for each user
user_recs = model.recommendForAllUsers(3)
print("=== Top 3 Recommendations per User ===")
user_recs.show(truncate=False)

# Stop Spark
spark.stop()