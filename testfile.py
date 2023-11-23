import numpy as np

from pyspark.sql import SparkSession
import time
import matplotlib.dates as dates
import matplotlib.dates as mdates
import lxml
import xxhash
import jsonschema
import tabulate
import termcolor
import requests

start_time = time.time()

os.environ["AWS_PROFILE"] = "default"

spark = (
    SparkSession.builder.appName("Test_XGBoost")
    .master("local[*]")
    .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")
    .config(
        "spark.jars.packages",
        "org.apache.hadoop:hadoop-aws:3.2.2,"
        "com.amazonaws:aws-java-sdk-bundle:1.12.180",
    )
    .getOrCreate()
)
spark._jsc.hadoopConfiguration().set("com.amazonaws.services.s3.enableV4", "true")
spark._jsc.hadoopConfiguration().set(
    "fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem"
)
spark._jsc.hadoopConfiguration().set(
    "fs.s3a.aws.credentials.provider",
    "com.amazonaws.auth.InstanceProfileCredentialsProvider,com.amazonaws.auth.DefaultAWSCredentialsProviderChain",
)
spark._jsc.hadoopConfiguration().set(
    "fs.AbstractFileSystem.s3a.impl", "org.apache.hadoop.fs.s3a.S3A"
)


from pyspark.ml import Pipeline
from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.feature import StringIndexer, VectorAssembler
from pyspark.sql.functions import col, date_format, to_date, when
from xgboost.spark import SparkXGBRegressor

# Load the data into a pyspark DataFrame
df_hist = spark.read.parquet(
    "s3a://takdllandingdev/dengue/static_compiled/silver/singapore_cases"
)
df_act = spark.read.parquet(
    "s3a://takdllandingdev/dengue/silver/dengue_cases/singapore/singapore_weekly"
)
df = (
    df_act.withColumnRenamed("weekly_cases", "dengue_cases")
    .unionByName(df_hist, allowMissingColumns=True)
    .withColumn(
        "date", when(col("date") == "2023-12-18", "2022-12-18").otherwise(col("date"))
    )
    .withColumn("date", to_date(col("date")))
    .sort("date")
)
df.show(10000)
# spark.sql("set spark.sql.legacy.timeParserPolicy=LEGACY")
df = (
    df.withColumn("year", date_format(col("date"), "y").cast("int"))
    .withColumn("month", date_format(col("date"), "M").cast("int"))
    .withColumn("day", date_format(col("date"), "d").cast("int"))
    .select("date", "dengue_cases", "year", "month", "day")
    .sort("date")
)
df = df.na.fill(0)
df.show(10000)
df.printSchema()


train = df.filter(col("date") < "2020-01-01").sort("date")
test = df.filter(col("date") > "2020-01-01").sort("date")

from pyspark.ml.feature import VectorAssembler, VectorIndexer

# Remove the target column and unwanted columns from the input feature set.
featuresCols = df.columns
featuresCols = [
    e
    for e in featuresCols
    if e not in ("date", "geo_country", "dengue_cases", "weekly_tavg", "weekly_prcp")
]
print(featuresCols)

# vectorAssembler combines all feature columns into a single feature vector column, "rawFeatures".
vectorAssembler = VectorAssembler(inputCols=featuresCols, outputCol="features")

# vectorIndexer identifies categorical features and indexes them, and creates a new column "features".
""" vectorIndexer = VectorIndexer(
    inputCol="rawFeatures", outputCol="features", maxCategories=4
) """

from xgboost.spark import SparkXGBRegressor

# The next step is to define the model training stage of the pipeline.
# The following command defines a XgboostRegressor model that takes an input column "features" by default and learns to predict the labels in the "cnt" column.
# If you are running Databricks Runtime for Machine Learning 9.0 ML or above, you can set the `num_workers` parameter to leverage the cluster for distributed training.
xgb_regressor = SparkXGBRegressor(
    num_workers=3,
    label_col="dengue_cases",
    missing=0.0,
)

from pyspark.ml.evaluation import RegressionEvaluator
from pyspark.ml.tuning import CrossValidator, ParamGridBuilder

# Define a grid of hyperparameters to test:
#  - maxDepth: maximum depth of each decision tree
#  - maxIter: iterations, or the total number of trees
paramGrid = (
    ParamGridBuilder()
    .addGrid(xgb_regressor.max_depth, [2, 5])
    .addGrid(xgb_regressor.n_estimators, [10, 100])
    .build()
)

# Define an evaluation metric.
# The CrossValidator compares the true labels with predicted values for each combination of parameters,
# and calculates this value to determine the best model.
evaluator = RegressionEvaluator(
    metricName="rmse",
    labelCol=xgb_regressor.getLabelCol(),
    predictionCol=xgb_regressor.getPredictionCol(),
)

# Declare the CrossValidator, which performs the model tuning.
cv = CrossValidator(
    estimator=xgb_regressor, evaluator=evaluator, estimatorParamMaps=paramGrid
)

from pyspark.ml import Pipeline

pipeline = Pipeline(stages=[vectorAssembler, cv])

pipelineModel = pipeline.fit(train)

predictions = pipelineModel.transform(test)

predictions.select("dengue_cases", "prediction", *featuresCols).show(1000)

rmse = evaluator.evaluate(predictions)
print("Accuracy RMSE: %g" % rmse)
print("--- %s seconds ---" % (time.time() - start_time))

import matplotlib.pyplot as plt

all = train.unionByName(predictions, allowMissingColumns=True)
"""
pdf = all.select("date", "dengue_cases", "prediction", "weekly_tavg", "weekly_prcp").toPandas()
pdf.set_index("date")
pdf.plot(x="date", y=["dengue_cases", "prediction", "weekly_prcp"])
plt.show()
"""

# R2 Accuracy computation
# cases_arr = pdf["dengue_cases"].values
# predictions_arr = pdf["prediction"].values
# from sklearn.metrics import r2_score
# r2 = r2_score(cases_arr, predictions_arr)
# print(f"Accuracy R2: {int(r2*100)} %")

from pyspark.sql.functions import sequence, to_date, explode, col

data = spark.sql(
    "SELECT sequence(to_date('2023-01-10'), to_date('2024-01-01'), interval 1 week) as date"
).withColumn("date", explode(col("date")))
new_df = (
    data.withColumn("year", date_format(col("date"), "y").cast("int"))
    .withColumn("month", date_format(col("date"), "M").cast("int"))
    .withColumn("day", date_format(col("date"), "d").cast("int"))
    .sort("date")
)

new_predictions = pipelineModel.transform(new_df)
new_predictions.select("prediction", *featuresCols).show(1000)

all = all.drop("prediction")  # drop previous testing predictions
all = all.unionByName(new_predictions, allowMissingColumns=True)
pdf = all.select("date", "prediction", "dengue_cases").toPandas()
pdf.set_index("date")
pdf.plot(x="date", y=["dengue_cases", "prediction"])
plt.gca().xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
plt.gca().xaxis.set_major_locator(mdates.YearLocator())
plt.gca().xaxis.grid(True)
plt.show()
