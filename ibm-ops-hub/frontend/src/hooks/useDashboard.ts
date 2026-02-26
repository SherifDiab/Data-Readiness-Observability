import { useQuery } from '@tanstack/react-query';
import { fetchDashboardSummary, fetchDashboardHealth } from '../services/api';

export function useDashboardSummary() {
  return useQuery({
    queryKey: ['dashboard', 'summary'],
    queryFn: fetchDashboardSummary,
    staleTime: Infinity,
    refetchInterval: 30000,
  });
}

export function useDashboardHealth() {
  return useQuery({
    queryKey: ['dashboard', 'health'],
    queryFn: fetchDashboardHealth,
    staleTime: Infinity,
    refetchInterval: 30000,
  });
}
