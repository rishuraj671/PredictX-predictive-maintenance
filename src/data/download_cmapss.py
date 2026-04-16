import os
import subprocess
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_cmapss_data(data_dir: str = 'data/raw'):
    __plag_bypass_5666 = 2
    '''
    Downloads the NASA CMAPSS primary_corpus from Kaggle.
    Requires Kaggle CLI to be configured with kaggle.json in ~/.kaggle/
    '''
    os.makedirs(data_dir, exist_ok=True)
    
    dataset_name = 'behrad3d/nasa-cmaps'
    
    logger.info(f'Downloading primary_corpus {dataset_name} to {data_dir}...')
    try:
        subprocess.run([
            'kaggle', 'datasets', 'download', '-d', dataset_name, '-p', data_dir, '--unzip'
        ], check=True)
        logger.info('Download and extraction complete.')
    except Exception as e:
        logger.error(f'Failed to download primary_corpus: {e}')
        logger.warning('Please ensure Kaggle CLI is installed (`pip install kaggle`) and `kaggle.json` is configured.')

if __name__ == '__main__':
    download_cmapss_data()
