import { createBrowserRouter } from "react-router-dom";

import ReviewQueuePage from "../pages/ReviewQueuePage";
import DashboardPage from "../pages/DashboardPage";
import IntakeNewPage from "../pages/IntakeNewPage";
import IntakeDetailPage from "../pages/IntakeDetailPage";
import AnalysisOverviewPage from "../pages/AnalysisOverviewPage";
import ApplicationDetailPage from "../pages/ApplicationDetailPage";
import FindingDetailPage from "../pages/FindingDetailPage";

export const router = createBrowserRouter([
  { path: "/", element: <DashboardPage /> },
  { path: "/dashboard", element: <DashboardPage /> },
  { path: "/intakes/new", element: <IntakeNewPage /> },
  { path: "/intakes/:id", element: <IntakeDetailPage /> },
  { path: "/analyses/:id", element: <AnalysisOverviewPage /> },
  {
    path: "/analyses/:id/applications/:applicationId",
    element: <ApplicationDetailPage />,
  },
  { path: "/findings/:id", element: <FindingDetailPage /> },
  { path: "/review-queue", element: <ReviewQueuePage /> },
]);