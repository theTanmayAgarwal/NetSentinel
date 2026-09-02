import React from "react";
import { Routes, Route } from "react-router-dom";
import { SOCLayout } from "./layouts/SOCLayout";
import { Dashboard } from "./pages/Dashboard";
import { Audits } from "./pages/Audits";
import { Devices } from "./pages/Devices";
import { DeviceDetail } from "./pages/DeviceDetail";
import { Findings } from "./pages/Findings";
import { TrainingCenter } from "./pages/TrainingCenter";
import { KnowledgeBase } from "./pages/KnowledgeBase";
import { Reports } from "./pages/Reports";
import { Settings } from "./pages/Settings";

export default function App() {
  return (
    <SOCLayout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/audits" element={<Audits />} />
        <Route path="/devices" element={<Devices />} />
        <Route path="/devices/:id" element={<DeviceDetail />} />
        <Route path="/findings" element={<Findings />} />
        <Route path="/training" element={<TrainingCenter />} />
        <Route path="/knowledge-base" element={<KnowledgeBase />} />
        <Route path="/reports" element={<Reports />} />
        <Route path="/settings" element={<Settings />} />
      </Routes>
    </SOCLayout>
  );
}
