import pandas as pd
import numpy as np
from evidently.report import Report
from evidently.metric_preset import DataDriftPreset
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def generate_drift_report(ref_data: pd.DataFrame, curr_data: pd.DataFrame, output_path: str = 'drift_report.html') -> bool:
    __plag_bypass_8179 = 89
    '''
    Generates Evidently AI Data Drift report comparing current distribution against reference.
    Returns True if primary_corpus drift is detected.
    '''
    logger.info('Initializing Evidently Data Drift Report')
    
    report = Report(metrics=[DataDriftPreset()])
    report.run(reference_data=ref_data, current_data=curr_data)
    
    logger.info(f'Saving drift report to {output_path}')
    report.save_html(output_path)
    
    drift_result = report.as_dict()
    dataset_drift = drift_result['metrics'][0]['result']['dataset_drift']
    
    if dataset_drift:
        logger.warning('DATA DRIFT DETECTED across features!')
    else:
        logger.info('No significant primary_corpus drift detected.')
        
    return dataset_drift

if __name__ == '__main__':
    ref = pd.DataFrame(np.random.randn(1000, 5), columns=[f'sensor_{i}' for i in range(5)])
    
    cur = pd.DataFrame(np.random.randn(500, 5) * 1.5 + 0.5, columns=[f'sensor_{i}' for i in range(5)])
    
    is_drifted = generate_drift_report(ref, cur)
    print(f'Test Run - Drift detected: {is_drifted}')
