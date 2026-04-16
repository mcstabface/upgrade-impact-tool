import { createBrowserRouter } from "react-router-dom";

import RequireAuth from "../auth/RequireAuth";
import RequireRole from "../auth/RequireRole";
import LoginPage from "../pages/LoginPage";
import ReviewQueuePage from "../pages/ReviewQueuePage";
import DashboardPage from "../pages/DashboardPage";
import IntakeNewPage from "../pages/IntakeNewPage";
import IntakeDetailPage from "../pages/IntakeDetailPage";
import AnalysisOverviewPage from "../pages/AnalysisOverviewPage";
import AnalysisReportPage from "../pages/AnalysisReportPage";
import ApplicationDetailPage from "../pages/ApplicationDetailPage";
import ApplicationReportPage from "../pages/ApplicationReportPage";
import FindingDetailPage from "../pages/FindingDetailPage";
import ReviewItemDetailPage from "../pages/ReviewItemDetailPage";
import AdminInspectionPage from "../pages/AdminInspectionPage";

export const router = createBrowserRouter([
    { path: "/login", element: <LoginPage /> },
    {
        element: <RequireAuth />,
        children: [
            { path: "/", element: <DashboardPage /> },
            { path: "/dashboard", element: <DashboardPage /> },
            {
                path: "/admin/inspection",
                element: (
                    <RequireRole allowedRoles={["ADMIN"]}>
                        <AdminInspectionPage />
                    </RequireRole>
                ),
            },
            {
                path: "/intakes/new",
                element: (
                    <RequireRole allowedRoles={["ANALYST", "ADMIN"]}>
                        <IntakeNewPage />
                    </RequireRole>
                ),
            },
            { path: "/intakes/:id", element: <IntakeDetailPage /> },
            { path: "/analyses/:id", element: <AnalysisOverviewPage /> },
            { path: "/analyses/:id/report", element: <AnalysisReportPage /> },
            {
                path: "/analyses/:id/applications/:applicationId",
                element: <ApplicationDetailPage />,
            },
            {
                path: "/analyses/:id/applications/:applicationId/report",
                element: <ApplicationReportPage />,
            },
            { path: "/findings/:id", element: <FindingDetailPage /> },
            { path: "/review-items/:id", element: <ReviewItemDetailPage /> },
            { path: "/review-queue", element: <ReviewQueuePage /> },
        ],
    },
]);