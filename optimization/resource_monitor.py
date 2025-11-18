#!/usr/bin/env python3
"""
Resource Monitor - Monitor system resource usage.

Features:
- CPU and memory monitoring
- Disk usage tracking
- Alert thresholds
- Historical metrics
- Thread-safe monitoring loop
"""

import psutil
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from collections import deque


class ResourceMonitor:
    """Monitor system resource usage."""

    def __init__(
        self,
        sample_interval: int = 5,
        alert_cpu_threshold: int = 90,
        alert_memory_threshold: int = 90
    ):
        """
        Initialize resource monitor.

        Args:
            sample_interval: Sampling interval in seconds
            alert_cpu_threshold: CPU usage alert threshold (percentage)
            alert_memory_threshold: Memory usage alert threshold (percentage)
        """
        self.sample_interval = sample_interval
        self.alert_cpu_threshold = alert_cpu_threshold
        self.alert_memory_threshold = alert_memory_threshold

        self.monitoring = False
        self.metrics: deque = deque(maxlen=1000)  # Keep last 1000 samples
        self.alerts: List[Dict[str, Any]] = []

        self.lock = threading.Lock()
        self.monitor_thread: Optional[threading.Thread] = None

        # Alert callbacks
        self.alert_callbacks: List[Callable] = []

    def start_monitoring(self) -> None:
        """Start resource monitoring."""
        if self.monitoring:
            return

        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop resource monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=self.sample_interval + 1)

    def _monitor_loop(self) -> None:
        """Monitoring loop."""
        while self.monitoring:
            try:
                # Collect metrics
                metric = {
                    "timestamp": time.time(),
                    "datetime": datetime.now().isoformat(),
                    "cpu_percent": psutil.cpu_percent(interval=1),
                    "memory_mb": psutil.virtual_memory().used / 1024 / 1024,
                    "memory_percent": psutil.virtual_memory().percent,
                    "disk_usage_percent": psutil.disk_usage('/').percent
                }

                with self.lock:
                    self.metrics.append(metric)

                # Check for alerts
                self._check_alerts(metric)

            except Exception as e:
                print(f"Warning: Resource monitoring error: {e}")

            # Wait for next sample
            time.sleep(self.sample_interval)

    def _check_alerts(self, metric: Dict[str, Any]) -> None:
        """
        Check for alert conditions.

        Args:
            metric: Current metric values
        """
        alerts = []

        # CPU alert
        if metric["cpu_percent"] > self.alert_cpu_threshold:
            alerts.append({
                "type": "cpu",
                "timestamp": metric["datetime"],
                "value": metric["cpu_percent"],
                "threshold": self.alert_cpu_threshold,
                "message": f"High CPU usage: {metric['cpu_percent']:.1f}%"
            })

        # Memory alert
        if metric["memory_percent"] > self.alert_memory_threshold:
            alerts.append({
                "type": "memory",
                "timestamp": metric["datetime"],
                "value": metric["memory_percent"],
                "threshold": self.alert_memory_threshold,
                "message": f"High memory usage: {metric['memory_percent']:.1f}%"
            })

        # Add alerts and trigger callbacks
        if alerts:
            with self.lock:
                self.alerts.extend(alerts)

            for alert in alerts:
                self._trigger_alert_callbacks(alert)

    def _trigger_alert_callbacks(self, alert: Dict[str, Any]) -> None:
        """
        Trigger alert callbacks.

        Args:
            alert: Alert information
        """
        for callback in self.alert_callbacks:
            try:
                callback(alert)
            except Exception as e:
                print(f"Warning: Alert callback error: {e}")

    def add_alert_callback(self, callback: Callable) -> None:
        """
        Add alert callback.

        Args:
            callback: Callback function accepting alert dict
        """
        self.alert_callbacks.append(callback)

    def get_current_usage(self) -> Dict[str, Any]:
        """
        Get current resource usage.

        Returns:
            Current usage metrics
        """
        try:
            return {
                "cpu_percent": psutil.cpu_percent(interval=0.1),
                "memory_mb": psutil.virtual_memory().used / 1024 / 1024,
                "memory_percent": psutil.virtual_memory().percent,
                "memory_available_mb": psutil.virtual_memory().available / 1024 / 1024,
                "disk_usage_percent": psutil.disk_usage('/').percent,
                "disk_free_gb": psutil.disk_usage('/').free / 1024 / 1024 / 1024
            }
        except Exception as e:
            return {"error": str(e)}

    def get_peak_usage(self) -> Dict[str, Any]:
        """
        Get peak resource usage.

        Returns:
            Peak usage metrics
        """
        with self.lock:
            if not self.metrics:
                return {}

            return {
                "peak_cpu_percent": max(m["cpu_percent"] for m in self.metrics),
                "peak_memory_mb": max(m["memory_mb"] for m in self.metrics),
                "peak_memory_percent": max(m["memory_percent"] for m in self.metrics),
                "samples": len(self.metrics)
            }

    def get_average_usage(self) -> Dict[str, Any]:
        """
        Get average resource usage.

        Returns:
            Average usage metrics
        """
        with self.lock:
            if not self.metrics:
                return {}

            return {
                "avg_cpu_percent": sum(m["cpu_percent"] for m in self.metrics) / len(self.metrics),
                "avg_memory_mb": sum(m["memory_mb"] for m in self.metrics) / len(self.metrics),
                "avg_memory_percent": sum(m["memory_percent"] for m in self.metrics) / len(self.metrics),
                "samples": len(self.metrics)
            }

    def get_metrics_history(self, last_n: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Get metrics history.

        Args:
            last_n: Optional limit to last N samples

        Returns:
            List of historical metrics
        """
        with self.lock:
            if last_n:
                return list(self.metrics)[-last_n:]
            else:
                return list(self.metrics)

    def get_alerts(self, clear: bool = False) -> List[Dict[str, Any]]:
        """
        Get alerts.

        Args:
            clear: Whether to clear alerts after retrieval

        Returns:
            List of alerts
        """
        with self.lock:
            alerts = list(self.alerts)
            if clear:
                self.alerts.clear()
            return alerts

    def clear_metrics(self) -> None:
        """Clear all metrics."""
        with self.lock:
            self.metrics.clear()

    def clear_alerts(self) -> None:
        """Clear all alerts."""
        with self.lock:
            self.alerts.clear()

    def get_stats(self) -> Dict[str, Any]:
        """
        Get monitoring statistics.

        Returns:
            Statistics dictionary
        """
        with self.lock:
            return {
                "monitoring": self.monitoring,
                "sample_interval": self.sample_interval,
                "total_samples": len(self.metrics),
                "total_alerts": len(self.alerts),
                "alert_cpu_threshold": self.alert_cpu_threshold,
                "alert_memory_threshold": self.alert_memory_threshold
            }

    def generate_report(self) -> str:
        """
        Generate resource monitoring report.

        Returns:
            Formatted report
        """
        current = self.get_current_usage()
        peak = self.get_peak_usage()
        average = self.get_average_usage()
        stats = self.get_stats()
        alerts = self.get_alerts()

        report = []
        report.append("=" * 80)
        report.append("RESOURCE MONITORING REPORT")
        report.append("=" * 80)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append(f"Monitoring: {'Active' if self.monitoring else 'Stopped'}")
        report.append("")

        # Current usage
        report.append("CURRENT USAGE:")
        report.append("-" * 80)
        if "error" not in current:
            report.append(f"CPU:              {current['cpu_percent']:.1f}%")
            report.append(f"Memory:           {current['memory_mb']:.1f} MB ({current['memory_percent']:.1f}%)")
            report.append(f"Memory Available: {current['memory_available_mb']:.1f} MB")
            report.append(f"Disk Usage:       {current['disk_usage_percent']:.1f}%")
            report.append(f"Disk Free:        {current['disk_free_gb']:.1f} GB")
        else:
            report.append(f"Error: {current['error']}")

        # Peak usage
        if peak:
            report.append("\nPEAK USAGE:")
            report.append("-" * 80)
            report.append(f"CPU:    {peak['peak_cpu_percent']:.1f}%")
            report.append(f"Memory: {peak['peak_memory_mb']:.1f} MB ({peak['peak_memory_percent']:.1f}%)")
            report.append(f"Samples: {peak['samples']}")

        # Average usage
        if average:
            report.append("\nAVERAGE USAGE:")
            report.append("-" * 80)
            report.append(f"CPU:    {average['avg_cpu_percent']:.1f}%")
            report.append(f"Memory: {average['avg_memory_mb']:.1f} MB ({average['avg_memory_percent']:.1f}%)")

        # Alerts
        if alerts:
            report.append("\nRECENT ALERTS:")
            report.append("-" * 80)
            for alert in alerts[-10:]:  # Last 10 alerts
                report.append(f"  [{alert['timestamp']}] {alert['message']}")

        report.append("\n" + "=" * 80)

        return "\n".join(report)


# Global monitor instance
_global_monitor = ResourceMonitor()


def get_resource_monitor() -> ResourceMonitor:
    """Get global resource monitor instance."""
    return _global_monitor


if __name__ == "__main__":
    # Example usage
    monitor = ResourceMonitor(sample_interval=2, alert_cpu_threshold=50, alert_memory_threshold=50)

    # Add alert callback
    def alert_handler(alert):
        print(f"🚨 ALERT: {alert['message']}")

    monitor.add_alert_callback(alert_handler)

    # Start monitoring
    print("Starting resource monitoring...")
    monitor.start_monitoring()

    # Let it run for 10 seconds
    try:
        time.sleep(10)
    except KeyboardInterrupt:
        pass

    # Get current usage
    print("\nCurrent Usage:")
    current = monitor.get_current_usage()
    for key, value in current.items():
        if isinstance(value, float):
            print(f"  {key}: {value:.1f}")
        else:
            print(f"  {key}: {value}")

    # Get stats
    print("\nMonitoring Stats:")
    stats = monitor.get_stats()
    for key, value in stats.items():
        print(f"  {key}: {value}")

    # Generate report
    print("\n" + monitor.generate_report())

    # Stop monitoring
    monitor.stop_monitoring()
    print("\nMonitoring stopped.")
