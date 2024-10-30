#!/bin/bash

# Function to check if a container is healthy
check_container() {
    local container=$1
    local max_attempts=$2
    local attempt=1
    
    echo "Waiting for $container to be ready..."
    while [ $attempt -le $max_attempts ]; do
        if docker ps | grep -q $container; then
            echo "$container is ready!"
            return 0
        fi
        echo "Attempt $attempt/$max_attempts: $container not ready yet..."
        sleep 5
        attempt=$((attempt + 1))
    done
    echo "$container failed to start properly"
    return 1
}

# Clean up any existing containers
echo "Cleaning up existing containers..."
docker-compose down --remove-orphans
docker system prune -f

# Create necessary directories
mkdir -p jobs jars

# Start services one by one
echo "Starting Zookeeper..."
docker-compose up -d zookeeper
check_container "zookeeper" 6 || exit 1

echo "Starting Kafka broker..."
docker-compose up -d broker
check_container "broker" 6 || exit 1

echo "Starting Spark master..."
docker-compose up -d spark-master
check_container "spark-master" 6 || exit 1

echo "Starting Spark workers..."
docker-compose up -d spark-worker-1 spark-worker-2
check_container "spark-worker-1" 6 || exit 1
check_container "spark-worker-2" 6 || exit 1

# Final verification
echo "Verifying all services..."
docker-compose ps

# Check Spark UI availability
echo "Checking Spark UI availability..."
timeout 30 bash -c 'while ! curl -s http://localhost:8080 > /dev/null; do sleep 1; done' && echo "Spark UI is available!" || echo "Warning: Spark UI might not be ready"

echo "All services started! You can access:"
echo "- Spark UI: http://localhost:8080"
echo "- Kafka broker: localhost:9092"
echo "- Zookeeper: localhost:2181"

echo "To submit your Spark job, use:"
echo "docker exec -it spark-master spark-submit \\"
echo "    --master spark://spark-master:7077 \\"
echo "    --packages org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.3,org.apache.spark:spark-streaming-kafka-0-10_2.12:3.5.3,org.apache.kafka:kafka-clients:3.4.0,org.apache.hadoop:hadoop-aws:3.3.1,com.amazonaws:aws-java-sdk:1.11.468 \\"
echo "    /opt/bitnami/spark/jobs/spark-city.py"