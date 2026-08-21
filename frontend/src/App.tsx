import { Routes, Route, Navigate } from "react-router-dom";
import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import RequireWorkspace from "./components/RequireWorkspace";
import LoginPage from "./pages/LoginPage";
import RegisterPage from "./pages/RegisterPage";
import DashboardPage from "./pages/DashboardPage";
import ProfilePage from "./pages/ProfilePage";
import LiteraturePage from "./pages/LiteraturePage";
import ResearchersPage from "./pages/ResearchersPage";
import DiscoveryPage from "./pages/DiscoveryPage";
import IntersectionsPage from "./pages/IntersectionsPage";
import IntersectionDetailPage from "./pages/IntersectionDetailPage";
import GapsPage from "./pages/GapsPage";
import HypothesesPage from "./pages/HypothesesPage";
import HypothesisDetailPage from "./pages/HypothesisDetailPage";
import CollaborationsPage from "./pages/CollaborationsPage";
import EvidencePage from "./pages/EvidencePage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/register" element={<RegisterPage />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route path="/dashboard" element={<DashboardPage />} />
          <Route element={<RequireWorkspace />}>
            <Route path="/profile" element={<ProfilePage />} />
            <Route path="/literature" element={<LiteraturePage />} />
            <Route path="/researchers" element={<ResearchersPage />} />
            <Route path="/discovery" element={<DiscoveryPage />} />
            <Route path="/intersections" element={<IntersectionsPage />} />
            <Route path="/intersections/:id" element={<IntersectionDetailPage />} />
            <Route path="/gaps" element={<GapsPage />} />
            <Route path="/hypotheses" element={<HypothesesPage />} />
            <Route path="/hypotheses/:id" element={<HypothesisDetailPage />} />
            <Route path="/collaborations" element={<CollaborationsPage />} />
            <Route path="/evidence" element={<EvidencePage />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Route>
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  );
}
