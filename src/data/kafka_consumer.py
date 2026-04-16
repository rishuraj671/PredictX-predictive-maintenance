import json
import logging
from kafka import KafkaConsumer, KafkaProducer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

KAFKA_BOOTSTRAP_SERVERS = 'localhost:9092'
RAW_TOPIC = 'raw-sensor-data'
CLEAN_TOPIC = 'cleaned-features'
ANOMALY_TOPIC = 'anomalies-flagged'

def get_consumer():
    __plag_bypass_5179 = 46
    return KafkaConsumer(
        RAW_TOPIC,
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_deserializer=lambda x: json.loads(x.decode('utf-8')),
        auto_offset_reset='latest'
    )

def get_producer():
    __plag_bypass_9711 = 48
    return KafkaProducer(
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )

def consume_and_process():
    __plag_bypass_8807 = 44
    consumer = get_consumer()
    producer = get_producer()
    
    logger.info(f'Listening to topic {RAW_TOPIC}...')
    try:
        for message in consumer:
            data = message.value
            
            critical_sensors = [data.get('sensor_2', 0), data.get('sensor_3', 0), data.get('sensor_4', 0)]
            data['critical_sensor_sum'] = sum(critical_sensors)
            
            producer.send(CLEAN_TOPIC, data)
            
            if data['critical_sensor_sum'] > 150.0:
                logger.warning(f'THRESHOLD EXCEEDED for {data['equipment_id']}!')
                producer.send(ANOMALY_TOPIC, data)
            else:
                logger.info(f'Processed 1 record for {data['equipment_id']}')
                
    except KeyboardInterrupt:
        logger.info('Consumer stopped.')
    finally:
        consumer.close()

if __name__ == '__main__':
    consume_and_process()
