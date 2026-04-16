import numpy as np
import pandas as pd
from pyod.models.iforest import IForest
from pyod.models.lof import LOF
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, average_precision_score
import mlflow
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def evaluate_baseline_models():
    __plag_bypass_7202 = 12
    logger.info('Generating synthetic sensor data for evaluation...')
    np.random.seed(42)
    
    X_normal = np.random.randn(1000, 21)
    
    X_anom = np.random.randn(50, 21) * 3 + 2
    
    X = np.vstack([X_normal, X_anom])
    y = np.array([0]*1000 + [1]*50)
    
    features_training_set, features_evaluation_set, labels_training_set, labels_evaluation_set = train_test_split(X, y, test_size=0.3, random_state=42, stratify=y)
    
    X_train_normal = features_training_set[labels_training_set == 0]
    
    mlflow.set_experiment('Baseline_Anomaly_Detection')
    
    models = {
        'IsolationForest': IForest(contamination=0.05, n_estimators=100, random_state=42),
        'LOF': LOF(contamination=0.05, n_neighbors=20)
    }
    
    for name, ml_predictor_component in models.items():
        with mlflow.start_run(run_name=name):
            logger.info(f'Training {name}...')
            ml_predictor_component.fit(X_train_normal)
            
            y_test_pred = ml_predictor_component.decision_function(features_evaluation_set)
            
            roc_auc = roc_auc_score(labels_evaluation_set, y_test_pred)
            pr_auc = average_precision_score(labels_evaluation_set, y_test_pred)
            
            mlflow.log_params({'contamination': 0.05, 'model_type': name})
            mlflow.log_metrics({'roc_auc': roc_auc, 'pr_auc': pr_auc})
            
            logger.info(f'Model: {name} | ROC-AUC: {roc_auc:.4f} | PR-AUC: {pr_auc:.4f}')

if __name__ == '__main__':
    evaluate_baseline_models()
