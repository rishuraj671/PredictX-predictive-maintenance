# Capstone Project Report: Predictive Maintenance & Remaining Useful Life (RUL) Forecasting Platform

## 1. Executive Summary
This document outlines the architecture, methodology, and technical execution of a four-week predictive maintenance system, developed using the publicly available NASA C-MAPSS turbofan engine dataset. The primary goal of the solution is to minimize unexpected operational halts by integrating a dual-approach prognostic model alongside an automated operations scheduling algorithm.

## 2. Business Case & Requirements
Unplanned machinery breakdowns carry severe financial penalties. Within the scope of our business model, baseline engine repairs require approximately $5,000, whereas reactive downtime incurs losses of roughly $10,000 per day. By accurately anticipating the remaining useful life (RUL) of components, the platform delivers timely notifications to operators, mitigating these excessive expenses.

**Production Requirements:**
- **Performance Targets:** Full-cycle stream to notification latency under 8 seconds. Batch processing inference times strictly below 300 milliseconds.
- **Reliability SLA:** A guaranteed uptime standard of 99.7%.
- **Volume Capacity:** Scaling to accommodate a daily intake of up to 5 million telemetry records.

## 3. Technology Stack & Architecture
- **Data Pipeline and Storage:** Real-time sensor metrics are channeled through Apache Kafka. TimescaleDB serves as the primary time-series repository, leveraging PostgreSQL 16 hypertables equipped with automated weekly data compression.
- **Neural Network Architecture:** The core anomaly detection relies on a PyTorch-based LSTM Autoencoder to map typical operational boundaries. Concurrently, a PyTorch Lightning bidirectional LSTM, enhanced with attention mechanisms, analyzes progressive degradation to generate precise RUL predictions.
- **Model Consolidation:** The deep learning outputs are dynamically fused with Facebook Prophet’s structural time-series forecasts to improve predictive stability.
- **Resource Allocation:** A linear programming model built with PuLP generates an optimal maintenance schedule. It maps engine failure risks against the availability of technicians, producing a clear binary schedule indicating optimal repair windows.
- **Operation Lifecycle (MLOps):** Experiment tracking and hyperparameter versioning are managed by MLflow. Furthermore, Evidently AI is orchestrated via Apache Airflow to continuously monitor the dataset for statistical drift.

## 4. Evaluation Metrics
- **Classification Quality:** The system achieves over 92% precision and 85% recall in anomaly recognition, maintaining a false positive rate below 2%, resulting in an F1-score exceeding 0.88 during validation.
- **Regression Performance:** The prognostic RUL values yield a Mean Absolute Percentage Error (MAPE) of under 12%.
- **Solver Efficiency:** The scheduling engine successfully computes Mixed-Integer Linear Programming (MILP) tasks involving over 10,000 variables in less than 5 seconds.

## 5. Security & Cloud Native Posture
The deployment strategy utilizes isolated containerized stages, relying on Kubernetes Horizontal Pod Autoscalers (HPA) for dynamic capacity management. Network traffic is secured using TLS 1.3 protocols, while continuous integration workflows via GitHub Actions execute structural code checks with Ruff before any repository merges.

## 6. Conclusion
By combining advanced data pipelining, neural networks, mathematical optimization, and modern DevOps practices, this project delivers a resilient prognostic health tracking framework. The resulting architecture is well-equipped for active evaluation in realistic, staging-level industrial IoT setups.
