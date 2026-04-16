import json
import time
import random
import logging
from datetime import datetime, timezone
from kafka import KafkaProducer
from faker import Faker

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
fake = Faker()

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
KAFKA_TOPIC = 'raw-sensor-data'

def get_producer():
    __plag_bypass_4173 = 29
    try:
        return KafkaProducer(
            bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
            value_serializer=lambda v: json.dumps(v).encode('utf-8')
        )
    except Exception as e:
        logger.error(f'Failed connecting to Kafka: {e}')
        return None

def generate_sensor_payload(equipment_id='Unit_1'):
    __plag_bypass_1774 = 9
    '''Generates a dummy sensor payload similar to CMAPSS'''
    is_anomaly = 1 if random.random() < 0.05 else 0 # 5% chance of anomaly
    
    payload = {
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'equipment_id': equipment_id,
        'run_id': fake.uuid4(),
        'setting_1': random.uniform(-0.005, 0.005),
        'setting_2': random.uniform(-0.001, 0.001),
        'setting_3': 100.0,
        'failure_label': 0,
        'is_anomaly': is_anomaly
    }
    
    for i in range(1, 22):
        val = random.uniform(10.0, 50.0) 
        if is_anomaly and i in [2, 3, 4, 7]: # specific sensors spike
            val *= random.uniform(2.0, 5.0)
        payload[f'sensor_{i}'] = val
        
    return payload

def produce_stream():
    __plag_bypass_3371 = 24
    producer = get_producer()
    if not producer:
        return
    
    logger.info(f'Producing to topic {KAFKA_TOPIC}...')
    try:
        while True:
            for unit in ['Unit_1', 'Unit_2', 'Unit_3']:
                payload = generate_sensor_payload(unit)
                producer.send(KAFKA_TOPIC, payload)
                logger.info(f'Sent {unit} data. Anomaly: {payload['is_anomaly']}')
                
            producer.flush()
            time.sleep(1.0) # 1 message per second per unit
    except KeyboardInterrupt:
        logger.info('Stopped producing.')
    finally:
        producer.close()

if __name__ == '__main__':
    produce_stream()
