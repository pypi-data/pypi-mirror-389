from pyspark.sql import SparkSession
from pyspark.ml.feature import VectorAssembler, StandardScaler
from pyspark.ml.clustering import KMeans
from pyspark.ml.evaluation import ClusteringEvaluator
import matplotlib.pyplot as plt
import sys

def main(csv_path):
    spark = SparkSession.builder \
        .appName("KMeans_CC_General") \
        .getOrCreate()

    # 1) Load data
    data_customer = spark.read.csv(csv_path, header=True, inferSchema=True)

    # 2) Basic cleaning
    data_customer = data_customer.na.drop()

    # 3) Feature assembly (as per your list)
    feature_cols = [
        'BALANCE',
        'BALANCE_FREQUENCY',
        'PURCHASES',
        'ONEOFF_PURCHASES',
        'INSTALLMENTS_PURCHASES',
        'CASH_ADVANCE',
        'PURCHASES_FREQUENCY',
        'ONEOFF_PURCHASES_FREQUENCY',
        'PURCHASES_INSTALLMENTS_FREQUENCY',
        'CASH_ADVANCE_FREQUENCY',
        'CASH_ADVANCE_TRX',
        'PURCHASES_TRX',
        'CREDIT_LIMIT',
        'PAYMENTS',
        'MINIMUM_PAYMENTS',
        'PRC_FULL_PAYMENT',
        'TENURE'
    ]

    assemble = VectorAssembler(inputCols=feature_cols, outputCol='features')

    assembled_data = assemble.transform(data_customer)

    # 4) Scale features
    scale = StandardScaler(inputCol='features', outputCol='standardized')
    data_scale = scale.fit(assembled_data).transform(assembled_data)

    # 5) Evaluator setup (will be used for each k)
    evaluator = ClusteringEvaluator(
        predictionCol='prediction',
        featuresCol='standardized',
        metricName='silhouette',
        distanceMeasure='squaredEuclidean'
    )

    silhouette_scores = []
    centers_by_k = {}

    # 6) Run KMeans for k = 2..9
    for k in range(2, 10):
        kmeans = KMeans(featuresCol='standardized', k=int(k))
        model = kmeans.fit(data_scale)
        predictions = model.transform(data_scale)
        score = evaluator.evaluate(predictions)
        silhouette_scores.append(score)

        centers = model.clusterCenters()
        centers_by_k[k] = centers

        print(f"K={k} -> Silhouette Score: {score:.6f}")

        # Optional: print centers for this k
        print("Cluster Centers:")
        for idx, center in enumerate(centers):
            print(f"  Center {idx}: {center}")

    # 7) Plot silhouette scores
    plt.figure(figsize=(8,6))
    ks = list(range(2, 10))
    plt.plot(ks, silhouette_scores, marker='o')
    plt.xlabel('k')
    plt.ylabel('Silhouette Score')
    plt.title('KMeans Silhouette Score by k')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

    spark.stop()

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python kmeans_cc_general.py /path/to/CC_GENERAL.csv")
        sys.exit(1)
    csv_path = sys.argv[1]
    main(csv_path)