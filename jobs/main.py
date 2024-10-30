import os
import uuid
from confluent_kafka import SerializingProducer
import simplejson as json
from datetime import datetime, timedelta
import random
import time

# 19.0760° N, 72.8777° E  21.1702° N, 72.8311° E

MUMBAI_COORDINATES = {
    'latitude': 19.0760,
    'longitude': 72.8777
}

SURAT_COORDINATES = {
    'latitude': 21.1702,
    'longitude': 72.8311
}

#CALCULATING THE INCREMENT IN LATITUDE AND LONGITUDE
LATITUDE_INCREMENT = (SURAT_COORDINATES['latitude'] - MUMBAI_COORDINATES['latitude']) / 100
LONGITUDE_INCREMENT = (SURAT_COORDINATES['longitude'] - MUMBAI_COORDINATES['longitude']) / 100

KAFKA_BOOTSTRAP_SERVERS = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
VEHICAL_TOPIC = os.getenv('VEHICAL_TOPIC', 'vehical_data')
GPS_TOPIC = os.getenv('GPS_TOPIC', 'gps_data')
TRAFFIC_TOPIC = os.getenv('TRAFFIC_TOPIC', 'traffic_data')
WEATHER_TOPIC = os.getenv('WEATHER_TOPIC', 'weather_data')
EMERGENCY_TOPIC = os.getenv('EMERGENCY_TOPIC', 'emergency_data')


random.seed(42)

start_time = datetime.now()
start_location = MUMBAI_COORDINATES.copy()

def generate_weather_data(device_id, timestamp, location):
    return {
        'id': uuid.uuid4(),
        'device_id': device_id,
        'timestamp': timestamp,
        'location': location,
        'temperature': random.randint(20, 40),
        'weatherCondition': random.choice(['Sunny','Rainy','Cloudy']),
        'precipitation': random.randint(0, 25),
        'windSpeed': random.randint(0, 100),
        'humidity': random.randint(0, 100),
        'airQualityIndex': random.randint(0, 500),
        
    }

def get_next_time():
    global start_time
    start_time += timedelta(seconds=random.randint(30,60))
    return start_time

def simulate_vehical_movement():
    global start_location
    
    start_location['latitude'] += LATITUDE_INCREMENT
    start_location['longitude'] += LONGITUDE_INCREMENT
    
    start_location['latitude'] += random.uniform(-0.0005,0.0005)
    start_location['longitude'] += random.uniform(-0.0005,0.0005)
    
    return start_location

def generate_vehicle_data(device_id):
    location =  simulate_vehical_movement()
    return {
        'id': uuid.uuid4(),
        'device_id': device_id,
        'timestamp': datetime.now().isoformat(),
        'location': (location['latitude'], location['longitude']),
        'speed': random.randint(40, 90),
        'direction': 'North-East',
        'make':'Toyota',
        'model':'Supra',
        'year': 2021,
        'fuelType': 'Hybrid',
    }


def generate_gps_data(device_id, timestamp, vehical_type = 'private'):
    
    return {
        'id': uuid.uuid4(),
        'device_id': device_id,
        'timestamp': timestamp,
        'speed': random.uniform(40, 90),
        'direction': 'North-East',
        'vehicleType': vehical_type,
        
    }

def generate_traffic_camera_data(device_id, timestamp, camera_id):
    return {
        'id': uuid.uuid4(),
        'device_id': device_id,
        camera_id: camera_id,
        'timestamp': timestamp,
        'snapshot': 'Base64EncodedString',
    }
    
def generate_emergency_incident_data(device_id, timestamp, location):
    return {
        'id': uuid.uuid4(),
        'incidentId': uuid.uuid4(),
        'device_id': device_id,
        'timestamp': timestamp,
        'location': location,
        'type': random.choice(['Accident','Traffic','Fire','Medical','Police','None']),
        'status': random.choice(['Active','Resolved']),
        'description': 'Incident Description',
    }
    
def json_serializer(obj):
    if isinstance(obj , uuid.UUID):
        return str(obj)
    raise TypeError(f'Cannot serialize object of type {obj.__class__.__name__} is not JSON serializable',)
    
def delivery_report(err, msg):
    if err is not None:
        print('Message delivery failed: {}'.format(err))
    else:
        print('Message delivered to {} [{}]'.format(msg.topic(), msg.partition()))

def produce_data_to_kafka(producer, topic, data):
    producer.produce(topic, value=json.dumps(data, default=json_serializer), key=str(data['id']), on_delivery=delivery_report)
    producer.flush()

    
def simulate_journey(producer, device_id):
    while True:
        vehicle_data = generate_vehicle_data(device_id)
        gps_data = generate_gps_data(device_id, vehicle_data['timestamp'])
        traffic_camera_data = generate_traffic_camera_data(device_id, vehicle_data['timestamp'], 'camera-1')
        weather_data = generate_weather_data(device_id, vehicle_data['timestamp'],vehicle_data['location'])
        emergency_incident_data = generate_emergency_incident_data(device_id,vehicle_data['timestamp'],vehicle_data['location'])
        
        if (vehicle_data['location'][0] >= SURAT_COORDINATES['latitude'] and vehicle_data['location'][1] <= SURAT_COORDINATES['longitude']):
            print('Journey completed')
            break
        
        produce_data_to_kafka(producer, VEHICAL_TOPIC, vehicle_data)
        produce_data_to_kafka(producer, GPS_TOPIC, gps_data)
        produce_data_to_kafka(producer, TRAFFIC_TOPIC, traffic_camera_data)
        produce_data_to_kafka(producer, WEATHER_TOPIC, weather_data)
        produce_data_to_kafka(producer, EMERGENCY_TOPIC, emergency_incident_data)
        
        
        time.sleep(5)
        

if __name__ == "__main__":
    producer_config ={
        'bootstrap.servers': KAFKA_BOOTSTRAP_SERVERS,
        'error_cb': lambda err: print(f'Error: {err}')
    }
    producer = SerializingProducer(producer_config)
   
    try:
       simulate_journey(producer, 'vehical-number-1')
    
    except KeyboardInterrupt:
        print('Exiting...')
        
    except Exception as e:
        print(f'An error occured: {e}')
        
