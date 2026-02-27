import { Routes, Route, Navigate } from 'react-router-dom';
import DashboardLayout from './components/layout/DashboardLayout';
import OverviewPage from './components/dashboard/OverviewPage';
import SparkJobsPage from './components/spark/SparkJobsPage';
import DataStageJobsPage from './components/datastage/DataStageJobsPage';
import EventProcessingPage from './components/event-processing/EventProcessingPage';
import FlinkJobsPage from './components/flink/FlinkJobsPage';
import ApiConnectPage from './components/apic/ApiConnectPage';
import SettingsPage from './components/settings/SettingsPage';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  useWebSocket();

  return (
    <DashboardLayout>
      <Routes>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/spark" element={<SparkJobsPage />} />
        <Route path="/datastage" element={<DataStageJobsPage />} />
        <Route path="/event-processing" element={<EventProcessingPage />} />
        <Route path="/flink" element={<FlinkJobsPage />} />
        <Route path="/apic" element={<ApiConnectPage />} />
        <Route path="/settings" element={<SettingsPage />} />
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </DashboardLayout>
  );
}

export default App;
