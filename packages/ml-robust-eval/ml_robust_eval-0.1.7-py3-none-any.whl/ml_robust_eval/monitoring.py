"""
Production monitoring module for ML models.
Tracks model performance metrics in real-time using Prometheus.
"""
import time
from typing import Callable, Optional, List, Dict, Any
from functools import wraps
from collections import deque
import threading

_metrics_initialized = False
_shared_metrics = {}
_metrics_lock = threading.Lock()

try:
    from prometheus_client import Counter, Histogram, Gauge, start_http_server, Summary, CollectorRegistry, REGISTRY
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    import threading
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def time(self, *args, **kwargs): return lambda x: x
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Summary:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    def start_http_server(*args, **kwargs): pass
    class CollectorRegistry:
        pass
    REGISTRY = None

import threading


class ModelPerformanceMonitor:
    """
    Monitor model performance in production using Prometheus metrics.
    
    Tracks:
    - Prediction latency
    - Model accuracy, precision, recall, F1
    - Prediction confidence scores
    - Data drift indicators
    - Model degradation signals
    """
    
    def __init__(self, model_name: str = "default_model", prometheus_port: int = 8000):
        """
        Initialize the model performance monitor.
        
        Args:
            model_name: Name identifier for the model
            prometheus_port: Port to expose Prometheus metrics endpoint
        """
        self.model_name = model_name
        self.prometheus_port = prometheus_port
        self.metrics_initialized = False
        
        if not PROMETHEUS_AVAILABLE:
            print("Warning: prometheus_client not installed. Install with: pip install prometheus-client")
            return
        
        self._initialize_metrics()
        self._start_metrics_server()
        
        # Store baseline metrics for comparison
        self.baseline_metrics = {}
        self.recent_metrics = deque(maxlen=1000)  # Store last 1000 predictions
        self.lock = threading.Lock()
    
    def _initialize_metrics(self):
        """Initialize all Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE:
            return
        
        global _metrics_initialized, _shared_metrics, _metrics_lock
        
        with _metrics_lock:
            # Reuse metrics if already initialized
            if _metrics_initialized:
                self.prediction_latency = _shared_metrics['prediction_latency']
                self.prediction_count = _shared_metrics['prediction_count']
                self.accuracy_gauge = _shared_metrics['accuracy_gauge']
                self.precision_gauge = _shared_metrics['precision_gauge']
                self.recall_gauge = _shared_metrics['recall_gauge']
                self.f1_score_gauge = _shared_metrics['f1_score_gauge']
                self.mae_gauge = _shared_metrics['mae_gauge']
                self.mse_gauge = _shared_metrics['mse_gauge']
                self.r2_score_gauge = _shared_metrics['r2_score_gauge']
                self.prediction_confidence = _shared_metrics['prediction_confidence']
                self.feature_distribution = _shared_metrics['feature_distribution']
                self.degradation_signal = _shared_metrics['degradation_signal']
                self.performance_degradation = _shared_metrics['performance_degradation']
                self.metrics_initialized = True
                return
            
            # Prediction latency metrics
            self.prediction_latency = Histogram(
            'model_prediction_latency_seconds',
            'Time taken for model prediction',
            ['model_name'],
            buckets=[0.001, 0.005, 0.01, 0.05, 0.1, 0.5, 1.0, 5.0]
        )
        
        # Prediction count
        self.prediction_count = Counter(
            'model_predictions_total',
            'Total number of predictions made',
            ['model_name', 'status']
        )
        
        # Performance metrics (classification)
        self.accuracy_gauge = Gauge(
            'model_accuracy',
            'Model accuracy over time',
            ['model_name']
        )
        
        self.precision_gauge = Gauge(
            'model_precision',
            'Model precision over time',
            ['model_name']
        )
        
        self.recall_gauge = Gauge(
            'model_recall',
            'Model recall over time',
            ['model_name']
        )
        
        self.f1_score_gauge = Gauge(
            'model_f1_score',
            'Model F1 score over time',
            ['model_name']
        )
        
        # Regression metrics
        self.mae_gauge = Gauge(
            'model_mae',
            'Model Mean Absolute Error',
            ['model_name']
        )
        
        self.mse_gauge = Gauge(
            'model_mse',
            'Model Mean Squared Error',
            ['model_name']
        )
        
        self.r2_score_gauge = Gauge(
            'model_r2_score',
            'Model R² Score',
            ['model_name']
        )
        
        # Prediction confidence/distribution
        self.prediction_confidence = Histogram(
            'model_prediction_confidence',
            'Distribution of prediction confidence scores',
            ['model_name'],
            buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
        )
        
        # Data drift indicators
        self.feature_distribution = Histogram(
            'model_feature_value',
            'Distribution of feature values (for drift detection)',
            ['model_name', 'feature_name'],
            buckets=[0.0, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 50.0, 100.0, float('inf')]
        )
        
        # Model degradation signal
        self.degradation_signal = Gauge(
            'model_degradation_signal',
            'Signal indicating model degradation (0=normal, 1=degraded)',
            ['model_name']
        )
        
        # Performance degradation percentage
        self.performance_degradation = Gauge(
            'model_performance_degradation_percent',
            'Percentage degradation compared to baseline',
            ['model_name', 'metric_name']
        )
        
        # Store metrics in shared dict for reuse
        _shared_metrics['prediction_latency'] = self.prediction_latency
        _shared_metrics['prediction_count'] = self.prediction_count
        _shared_metrics['accuracy_gauge'] = self.accuracy_gauge
        _shared_metrics['precision_gauge'] = self.precision_gauge
        _shared_metrics['recall_gauge'] = self.recall_gauge
        _shared_metrics['f1_score_gauge'] = self.f1_score_gauge
        _shared_metrics['mae_gauge'] = self.mae_gauge
        _shared_metrics['mse_gauge'] = self.mse_gauge
        _shared_metrics['r2_score_gauge'] = self.r2_score_gauge
        _shared_metrics['prediction_confidence'] = self.prediction_confidence
        _shared_metrics['feature_distribution'] = self.feature_distribution
        _shared_metrics['degradation_signal'] = self.degradation_signal
        _shared_metrics['performance_degradation'] = self.performance_degradation
        
        _metrics_initialized = True
        self.metrics_initialized = True
    
    def _start_metrics_server(self):
        """Start HTTP server to expose Prometheus metrics."""
        if not PROMETHEUS_AVAILABLE or not self.metrics_initialized:
            return
        
        global _metrics_server_started
        if '_metrics_server_started' not in globals():
            globals()['_metrics_server_started'] = set()
        
        # Only start server once per port
        if self.prometheus_port not in globals()['_metrics_server_started']:
            try:
                start_http_server(self.prometheus_port)
                globals()['_metrics_server_started'].add(self.prometheus_port)
                print(f"Prometheus metrics server started on port {self.prometheus_port}")
                print(f"Metrics endpoint: http://localhost:{self.prometheus_port}/metrics")
            except Exception as e:
                print(f"Warning: Could not start metrics server: {e}")
    
    def set_baseline_metrics(self, metrics: Dict[str, float]):
        """
        Set baseline metrics for comparison.
        
        Args:
            metrics: Dictionary with metric names and baseline values
                    e.g., {'accuracy': 0.95, 'precision': 0.92, 'recall': 0.93}
        """
        self.baseline_metrics = metrics.copy()
        print(f"Baseline metrics set for {self.model_name}: {metrics}")
    
    def track_prediction(self, latency: float, status: str = "success"):
        """
        Track a single prediction.
        
        Args:
            latency: Time taken for prediction in seconds
            status: Status of prediction ('success', 'error', etc.)
        """
        if not self.metrics_initialized:
            return
        
        self.prediction_latency.labels(model_name=self.model_name).observe(latency)
        self.prediction_count.labels(model_name=self.model_name, status=status).inc()
    
    def track_confidence(self, confidence: float):
        """
        Track prediction confidence score.
        
        Args:
            confidence: Confidence score between 0 and 1
        """
        if not self.metrics_initialized:
            return
        
        self.prediction_confidence.labels(model_name=self.model_name).observe(confidence)
    
    def track_feature_value(self, feature_name: str, value: float):
        """
        Track feature value for drift detection.
        
        Args:
            feature_name: Name of the feature
            value: Feature value
        """
        if not self.metrics_initialized:
            return
        
        self.feature_distribution.labels(
            model_name=self.model_name,
            feature_name=str(feature_name)
        ).observe(value)
    
    def update_classification_metrics(self, accuracy: float, precision: float, 
                                     recall: float, f1_score: float):
        """
        Update classification performance metrics.
        
        Args:
            accuracy: Accuracy score
            precision: Precision score
            recall: Recall score
            f1_score: F1 score
        """
        if not self.metrics_initialized:
            return
        
        self.accuracy_gauge.labels(model_name=self.model_name).set(accuracy)
        self.precision_gauge.labels(model_name=self.model_name).set(precision)
        self.recall_gauge.labels(model_name=self.model_name).set(recall)
        self.f1_score_gauge.labels(model_name=self.model_name).set(f1_score)
        
        # Check for degradation
        self._check_degradation('accuracy', accuracy)
        self._check_degradation('precision', precision)
        self._check_degradation('recall', recall)
        self._check_degradation('f1_score', f1_score)
    
    def update_regression_metrics(self, mae: float, mse: float, r2_score: float):
        """
        Update regression performance metrics.
        
        Args:
            mae: Mean Absolute Error
            mse: Mean Squared Error
            r2_score: R² Score
        """
        if not self.metrics_initialized:
            return
        
        self.mae_gauge.labels(model_name=self.model_name).set(mae)
        self.mse_gauge.labels(model_name=self.model_name).set(mse)
        self.r2_score_gauge.labels(model_name=self.model_name).set(r2_score)
        
        # Check for degradation (for regression, lower is better for MAE/MSE, higher for R²)
        if 'mae' in self.baseline_metrics:
            degradation = ((mae - self.baseline_metrics['mae']) / self.baseline_metrics['mae']) * 100
            self.performance_degradation.labels(
                model_name=self.model_name,
                metric_name='mae'
            ).set(degradation)
        
        if 'mse' in self.baseline_metrics:
            degradation = ((mse - self.baseline_metrics['mse']) / self.baseline_metrics['mse']) * 100
            self.performance_degradation.labels(
                model_name=self.model_name,
                metric_name='mse'
            ).set(degradation)
        
        if 'r2_score' in self.baseline_metrics:
            degradation = ((self.baseline_metrics['r2_score'] - r2_score) / abs(self.baseline_metrics['r2_score']) + 1e-8) * 100
            self.performance_degradation.labels(
                model_name=self.model_name,
                metric_name='r2_score'
            ).set(degradation)
    
    def _check_degradation(self, metric_name: str, current_value: float, 
                          threshold: float = 0.05):
        """
        Check if model performance has degraded compared to baseline.
        
        Args:
            metric_name: Name of the metric
            current_value: Current metric value
            threshold: Degradation threshold (default 5%)
        """
        if not self.metrics_initialized:
            return
        
        if metric_name not in self.baseline_metrics:
            return
        
        baseline = self.baseline_metrics[metric_name]
        degradation = ((baseline - current_value) / baseline) * 100
        
        self.performance_degradation.labels(
            model_name=self.model_name,
            metric_name=metric_name
        ).set(degradation)
        
        # Set degradation signal if threshold exceeded
        if degradation > threshold * 100:
            self.degradation_signal.labels(model_name=self.model_name).set(1)
        else:
            self.degradation_signal.labels(model_name=self.model_name).set(0)
    
    def store_prediction(self, y_true: Any, y_pred: Any, confidence: Optional[float] = None):
        """
        Store prediction for batch metric calculation.
        
        Args:
            y_true: True label/value
            y_pred: Predicted label/value
            confidence: Optional confidence score
        """
        with self.lock:
            self.recent_metrics.append({
                'y_true': y_true,
                'y_pred': y_pred,
                'confidence': confidence,
                'timestamp': time.time()
            })


def monitor_model_predictions(model_name: str = "default_model", 
                             prometheus_port: int = 8000):
    """
    Decorator to automatically monitor model predictions.
    
    Usage:
        @monitor_model_predictions(model_name="my_model")
        def predict(model, X):
            return model.predict(X)
    """
    monitor = ModelPerformanceMonitor(model_name, prometheus_port)
    
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                latency = time.time() - start_time
                monitor.track_prediction(latency, status="success")
                return result
            except Exception as e:
                latency = time.time() - start_time
                monitor.track_prediction(latency, status="error")
                raise e
        
        wrapper.monitor = monitor
        return wrapper
    
    return decorator


class ModelMonitoringWrapper:
    """
    Wrapper class to monitor model predictions in production.
    """
    
    def __init__(self, model, model_name: str = "default_model", 
                 prometheus_port: int = 8000):
        """
        Initialize monitoring wrapper.
        
        Args:
            model: The ML model to monitor
            model_name: Name identifier for the model
            prometheus_port: Port for Prometheus metrics endpoint
        """
        self.model = model
        self.monitor = ModelPerformanceMonitor(model_name, prometheus_port)
    
    def predict(self, X, track_features: bool = False):
        """
        Make prediction with monitoring.
        
        Args:
            X: Input features
            track_features: Whether to track feature values for drift detection
        """
        start_time = time.time()
        
        try:
            predictions = self.model.predict(X)
            latency = time.time() - start_time
            
            self.monitor.track_prediction(latency, status="success")
            
            # Track feature values if requested
            if track_features and hasattr(X, '__iter__'):
                if isinstance(X[0], (list, tuple)):
                    for i, feature_values in enumerate(zip(*X)):
                        for val in feature_values:
                            self.monitor.track_feature_value(f"feature_{i}", float(val))
            
            return predictions
        except Exception as e:
            latency = time.time() - start_time
            self.monitor.track_prediction(latency, status="error")
            raise e
    
    def predict_proba(self, X):
        """Make probability prediction with monitoring."""
        start_time = time.time()
        
        try:
            probabilities = self.model.predict_proba(X)
            latency = time.time() - start_time
            
            self.monitor.track_prediction(latency, status="success")
            
            # Track confidence scores
            if hasattr(probabilities, 'max'):
                max_confidences = probabilities.max(axis=1)
                for conf in max_confidences:
                    self.monitor.track_confidence(float(conf))
            
            return probabilities
        except Exception as e:
            latency = time.time() - start_time
            self.monitor.track_prediction(latency, status="error")
            raise e

