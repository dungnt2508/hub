'use client';

import React, { useState, useEffect } from 'react';
import { AlertCircle, TrendingUp, Database, Activity, AlertTriangle, CheckCircle } from 'lucide-react';

interface QueryMetric {
  query_hash: string;
  mean_time_ms: number;
  max_time_ms: number;
  total_calls: number;
  recorded_at: string;
}

interface Alert {
  id: string;
  alert_type: string;
  severity: 'CRITICAL' | 'HIGH' | 'MEDIUM' | 'LOW' | 'INFO';
  title: string;
  message: string;
  created_at: string;
  status: 'ACTIVE' | 'ACKNOWLEDGED' | 'RESOLVED';
}

interface DBADashboardProps {
  connectionId?: string;
}

export default function DBADashboard({ connectionId }: DBADashboardProps) {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [metrics, setMetrics] = useState<QueryMetric[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch alerts
        const alertsResponse = await fetch(
          `/api/dba/alerts${connectionId ? `?connection_id=${connectionId}` : ''}`
        );
        if (alertsResponse.ok) {
          const alertsData = await alertsResponse.json();
          setAlerts(alertsData.alerts || []);
        }

        // Fetch metrics
        const metricsResponse = await fetch(
          `/api/dba/metrics${connectionId ? `?connection_id=${connectionId}` : ''}`
        );
        if (metricsResponse.ok) {
          const metricsData = await metricsResponse.json();
          setMetrics(metricsData.metrics || []);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
    // Refresh every 30 seconds
    const interval = setInterval(fetchDashboardData, 30000);
    return () => clearInterval(interval);
  }, [connectionId]);

  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-100 border-red-400 text-red-800';
      case 'HIGH':
        return 'bg-orange-100 border-orange-400 text-orange-800';
      case 'MEDIUM':
        return 'bg-yellow-100 border-yellow-400 text-yellow-800';
      case 'LOW':
        return 'bg-blue-100 border-blue-400 text-blue-800';
      default:
        return 'bg-gray-100 border-gray-400 text-gray-800';
    }
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'CRITICAL':
        return <AlertTriangle className="w-5 h-5" />;
      case 'HIGH':
        return <AlertCircle className="w-5 h-5" />;
      default:
        return <Activity className="w-5 h-5" />;
    }
  };

  const activeAlerts = alerts.filter(a => a.status === 'ACTIVE');
  const criticalAlerts = activeAlerts.filter(a => a.severity === 'CRITICAL');
  const avgQueryTime = metrics.length > 0
    ? metrics.reduce((sum, m) => sum + m.mean_time_ms, 0) / metrics.length
    : 0;

  if (loading) {
    return (
      <div className="flex items-center justify-center h-screen">
        <div className="text-gray-600">Đang tải dữ liệu...</div>
      </div>
    );
  }

  return (
    <div className="p-6 bg-gray-50 min-h-screen">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <h1 className="text-3xl font-bold text-gray-900 mb-2">DBA Dashboard</h1>
          <p className="text-gray-600">Giám sát hiệu năng cơ sở dữ liệu</p>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg text-red-800">
            <p className="font-semibold">Lỗi:</p>
            <p>{error}</p>
          </div>
        )}

        {/* KPIs */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
          {/* Critical Alerts */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-red-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Alerts Nghiêm Trọng</p>
                <p className="text-3xl font-bold text-red-600 mt-2">{criticalAlerts.length}</p>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500 opacity-20" />
            </div>
          </div>

          {/* Active Alerts */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-orange-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Alerts Đang Hoạt Động</p>
                <p className="text-3xl font-bold text-orange-600 mt-2">{activeAlerts.length}</p>
              </div>
              <AlertCircle className="w-8 h-8 text-orange-500 opacity-20" />
            </div>
          </div>

          {/* Avg Query Time */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-blue-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Thời Gian Query Tb</p>
                <p className="text-3xl font-bold text-blue-600 mt-2">
                  {avgQueryTime.toFixed(2)}ms
                </p>
              </div>
              <TrendingUp className="w-8 h-8 text-blue-500 opacity-20" />
            </div>
          </div>

          {/* Metrics Count */}
          <div className="bg-white rounded-lg shadow p-6 border-l-4 border-green-500">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-gray-600 text-sm">Metrics Được Lưu</p>
                <p className="text-3xl font-bold text-green-600 mt-2">{metrics.length}</p>
              </div>
              <Database className="w-8 h-8 text-green-500 opacity-20" />
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Alerts Section */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow overflow-hidden">
              <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
                <h2 className="text-lg font-semibold text-gray-900">Alerts Đang Hoạt Động</h2>
              </div>
              <div className="divide-y divide-gray-200">
                {activeAlerts.length > 0 ? (
                  activeAlerts.slice(0, 10).map(alert => (
                    <div key={alert.id} className={`p-4 border-l-4 ${getSeverityColor(alert.severity)}`}>
                      <div className="flex items-start gap-3">
                        {getSeverityIcon(alert.severity)}
                        <div className="flex-1">
                          <h3 className="font-semibold">{alert.title}</h3>
                          <p className="text-sm mt-1">{alert.message}</p>
                          <p className="text-xs mt-2 opacity-75">
                            {new Date(alert.created_at).toLocaleString('vi-VN')}
                          </p>
                        </div>
                        <span className={`text-xs px-2 py-1 rounded ${
                          alert.severity === 'CRITICAL' ? 'bg-red-200' : 'bg-gray-200'
                        }`}>
                          {alert.severity}
                        </span>
                      </div>
                    </div>
                  ))
                ) : (
                  <div className="p-8 text-center text-gray-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-2 opacity-30" />
                    <p>Không có alerts</p>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Metrics Summary */}
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200 bg-gray-50">
              <h2 className="text-lg font-semibold text-gray-900">Metrics Gần Đây</h2>
            </div>
            <div className="p-6">
              {metrics.length > 0 ? (
                <div className="space-y-4">
                  {metrics.slice(0, 5).map((metric, idx) => (
                    <div key={idx} className="pb-4 border-b border-gray-100 last:border-0">
                      <p className="text-sm font-mono text-gray-600 truncate">
                        Query: {metric.query_hash.substring(0, 12)}...
                      </p>
                      <div className="mt-2 space-y-1 text-sm">
                        <p>
                          <span className="text-gray-600">Trung bình:</span>
                          <span className="ml-2 font-semibold text-blue-600">
                            {metric.mean_time_ms.toFixed(2)}ms
                          </span>
                        </p>
                        <p>
                          <span className="text-gray-600">Tối đa:</span>
                          <span className="ml-2 font-semibold text-orange-600">
                            {metric.max_time_ms.toFixed(2)}ms
                          </span>
                        </p>
                        <p>
                          <span className="text-gray-600">Calls:</span>
                          <span className="ml-2 font-semibold text-green-600">
                            {metric.total_calls}
                          </span>
                        </p>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-500 text-center py-8">
                  Chưa có metrics
                </p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
