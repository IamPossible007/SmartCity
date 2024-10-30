from pyspark.sql import SparkSession
from jobs.config import configuration
import pyspark.sql.types as T
import pyspark.sql.functions as F
from pyspark.sql import DataFrame


def main():
    spark = SparkSession.builder.appName("SparkCity")\
        .config("spark.jars.packages",
                "org.apache.spark:spark-sql-kafka-0-10_2.13:3.5.3,"
                "org.apache.hadoop:hadoop-aws:3.3.1,"
                "com.amazonaws:aws-java-sdk:1.11.468")\
        .config("spark.hadoop.fs.s3a.impl", "org.apache.hadoop.fs.s3a.S3AFileSystem")\
        .config("spark.hadoop.fs.s3a.access.key", configuration.get("AWS_ACCESS_KEY"))\
        .config("spark.hadoop.fs.s3a.secret.key", configuration.get("AWS_SECRET_KEY"))\
        .config("spark.hadoop.fs.s3a.aws.credentials.provider", "org.apache.hadoop.fs.s3a.SimpleAWSCredentialsProvider")\
        .getOrCreate()
        
    spark.sparkContext.setLogLevel("WARN")

    
    #vehical schema
    vehicalSchema = T.StructType([
        T.StructField("id", T.StringType(), True),
        T.StructField("device_id", T.StringType(), True),
        T.StructField("timestamp", T.TimestampType(), True),
        T.StructField("location", T.StringType(), True),
        T.StructField("speed", T.DoubleType(), True),
        T.StructField("direction", T.StringType(), True),
        T.StructField("make", T.StringType(), True),
        T.StructField("model", T.StringType(), True),
        T.StructField("year", T.IntegerType(), True),
        T.StructField("fuelType", T.StringType(), True),        
    ])
    
    #gps schema
    gpsSchema = T.StructType([
        T.StructField("id", T.StringType(), True),
        T.StructField("device_id", T.StringType(), True),
        T.StructField("timestamp", T.TimestampType(), True),
        T.StructField("speed", T.DoubleType(), True),
        T.StructField("direction", T.StringType(), True),
        T.StructField("vehicleType", T.StringType(), True),        
    ])
    
    #trafic schema
    trafficSchema = T.StructType([
        T.StructField("id", T.StringType(), True),
        T.StructField("device_id", T.StringType(), True),
        T.StructField("camera_id", T.StringType(), True),
        T.StructField("timestamp", T.TimestampType(), True),
        T.StructField("snapshot", T.StringType(), True),        
    ])
    
    #weather schema
    weatherSchema = T.StructType([
        T.StructField("id", T.StringType(), True),
        T.StructField("device_id", T.StringType(), True),
        T.StructField("location", T.StringType(), True),
        T.StructField("timestamp", T.TimestampType(), True),
        T.StructField("temperature", T.DoubleType(), True),
        T.StructField("humidity", T.IntegerType(), True),
        T.StructField("windSpeed", T.DoubleType(), True),
        T.StructField("precipitation", T.DoubleType(), True),
        T.StructField("airQualityIndex", T.DoubleType(), True),
        T.StructField("weatherCondition", T.StringType(), True),        
    ])
    
    #emergency schema
    emergencySchema = T.StructType([
        T.StructField("id", T.StringType(), True),
        T.StructField("device_id", T.StringType(), True),
        T.StructField("incidentId", T.StringType(), True),
        T.StructField("timestamp", T.TimestampType(), True),
        T.StructField("location", T.StringType(), True),
        T.StructField("type", T.StringType(), True),
        T.StructField("status", T.StringType(), True),
        T.StructField("description", T.StringType(), True),        
    ])
    
    def read_kafka_topic(topic, schema):
        return(spark.readStream.format("kafka")\
            .format('kafka')
            .option('kafka.bootstrap.servers', configuration.get('broker'))
            .option('subscribe', topic)
            .option('startingOffsets', 'earliest')
            .load()
            .selectExpr("CAST(value AS STRING)")
            .select(F.from_json(F.col("value"), schema).alias("data"))
            .select("data.*")
            .withWatermark('timestamp', '2 minutes')
        )
    
    vehicalDF = read_kafka_topic('vehical_data', vehicalSchema).alias("vehical")
    gpsDF = read_kafka_topic('gps_data', gpsSchema).alias("gps")
    trafficDF = read_kafka_topic('traffic_data', trafficSchema).alias("traffic")
    weatherDF = read_kafka_topic('weather_data', weatherSchema).alias("weather")
    emergencyDF = read_kafka_topic('emergency_data', emergencySchema).alias("emergency")
    
    def streamWriter( input: DataFrame, checkpointFolder, output):
        return (input.writeStream
                .format('parquet')
                .option('checkpointLocation', checkpointFolder)
                .option('path', output)
                .outputMode('append')
                .start())
        
    #join with timestamp
    query1 = streamWriter(vehicalDF,'s3a://my-spark-streaming-data/checkpoints/vehical_data',
                 's3a://my-spark-streaming-data/data/vehical_data')
    query2 = streamWriter(gpsDF,'s3a://my-spark-streaming-data/checkpoints/gps_data',
                    's3a://my-spark-streaming-data/data/gps_data')
    query3 = streamWriter(trafficDF,'s3a://my-spark-streaming-data/checkpoints/traffic_data',
                    's3a://my-spark-streaming-data/data/traffic_data')
    query4 = streamWriter(weatherDF,'s3a://my-spark-streaming-data/checkpoints/weather_data',
                    's3a://my-spark-streaming-data/data/weather_data')
    query5 = streamWriter(emergencyDF,'s3a://my-spark-streaming-data/checkpoints/emergency_data',
                    's3a://my-spark-streaming-data/data/emergency_data')
    
    query5.awaitTermination()
    
    
    
                

if __name__ == "__main__":
    main()

