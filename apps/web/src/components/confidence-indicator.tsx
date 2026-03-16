import * as React from 'react';
import { AlertTriangle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface ConfidenceIndicatorProps {
  /** Confidence score between 0.0 and 1.0 */
  confidence: number;
  /** Whether to show the percentage label alongside the badge text */
  showLabel?: boolean;
  className?: string;
}

interface ConfidenceTier {
  label: string;
  variant: 'success' | 'warning' | 'orange' | 'muted';
  showWarning: boolean;
  barColor: string;
}

function getConfidenceTier(confidence: number): ConfidenceTier {
  if (confidence > 0.85) {
    return {
      label: 'Sikkert funn',
      variant: 'success',
      showWarning: false,
      barColor: 'bg-green-500',
    };
  }
  if (confidence >= 0.65) {
    return {
      label: 'Sannsynlig funn',
      variant: 'warning',
      showWarning: false,
      barColor: 'bg-yellow-500',
    };
  }
  if (confidence >= 0.4) {
    return {
      label: 'Mulig funn',
      variant: 'orange',
      showWarning: false,
      barColor: 'bg-orange-500',
    };
  }
  return {
    label: 'Usikkert',
    variant: 'muted',
    showWarning: true,
    barColor: 'bg-slate-400',
  };
}

export function ConfidenceIndicator({
  confidence,
  showLabel = false,
  className,
}: ConfidenceIndicatorProps) {
  const clamped = Math.max(0, Math.min(1, confidence));
  const tier = getConfidenceTier(clamped);
  const pct = Math.round(clamped * 100);

  return (
    <div className={cn('inline-flex flex-col gap-1', className)}>
      <div className="inline-flex items-center gap-1.5">
        {tier.showWarning && (
          <AlertTriangle
            className="h-3.5 w-3.5 text-slate-400 shrink-0"
            aria-hidden="true"
          />
        )}
        <Badge variant={tier.variant}>
          {tier.label}
        </Badge>
        {showLabel && (
          <span className="text-xs text-muted-foreground tabular-nums">
            {pct}%
          </span>
        )}
      </div>
      {showLabel && (
        <div className="w-full bg-slate-200 rounded-full h-1.5 overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all', tier.barColor)}
            style={{ width: `${pct}%` }}
            role="progressbar"
            aria-valuenow={pct}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label={`Konfidens: ${pct}%`}
          />
        </div>
      )}
    </div>
  );
}
