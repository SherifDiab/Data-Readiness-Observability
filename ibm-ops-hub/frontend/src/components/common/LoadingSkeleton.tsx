import clsx from 'clsx';

interface LoadingSkeletonProps {
  rows?: number;
  className?: string;
}

export default function LoadingSkeleton({ rows = 5, className }: LoadingSkeletonProps) {
  return (
    <div className={clsx('space-y-3', className)}>
      {Array.from({ length: rows }).map((_, i) => (
        <div key={i} className="bg-bg-tertiary rounded-lg border border-border-color p-4 animate-pulse">
          <div className="flex items-center gap-4">
            <div className="h-4 bg-bg-hover rounded w-1/4" />
            <div className="h-4 bg-bg-hover rounded w-1/6" />
            <div className="h-4 bg-bg-hover rounded w-1/5" />
            <div className="h-4 bg-bg-hover rounded w-1/6" />
          </div>
        </div>
      ))}
    </div>
  );
}
