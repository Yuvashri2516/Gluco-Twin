import React from 'react';
import { ArrowUpRight, ArrowDownRight, ArrowRight } from 'lucide-react';
import Badge from './Badge';

/**
 * Summary KPI Metric Card Component
 */
export default function MetricCard({
  title,
  value,
  unit,
  badgeText,
  badgeVariant = 'target',
  trend = 'stable', // 'rising' | 'falling' | 'stable'
  deltaText,
  subtext,
  className = ''
}) {
  const renderTrendIcon = () => {
    if (trend === 'rising') return <ArrowUpRight size={15} color="var(--color-critical-rose)" />;
    if (trend === 'falling') return <ArrowDownRight size={15} color="var(--color-warning-amber)" />;
    return <ArrowRight size={15} color="var(--color-target-green)" />;
  };

  return (
    <div className={`metric-card ${className}`}>
      <div className="metric-header">
        <span className="metric-title">{title}</span>
        {badgeText && <Badge variant={badgeVariant}>{badgeText}</Badge>}
      </div>

      <div className="metric-value-row">
        <span className="metric-value">{value}</span>
        {unit && <span className="metric-unit">{unit}</span>}
      </div>

      <div className="metric-footer">
        {trend && renderTrendIcon()}
        {deltaText && <span style={{ fontWeight: 600, color: 'var(--color-navy-800)' }}>{deltaText}</span>}
        {subtext && <span style={{ color: 'var(--color-navy-500)' }}>{subtext}</span>}
      </div>
    </div>
  );
}
