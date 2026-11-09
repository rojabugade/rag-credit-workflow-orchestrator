import {lazy, Suspense, useEffect, useState} from "react";
import {useLocation, useNavigate} from "react-router-dom";
import {Layout} from "./components/Layout";
import {useCases} from "./hooks/useCases";
import type {CreditCase, PageName} from "./types";

const Login = lazy(() => import("./pages/Login").then(module => ({default: module.Login})));
const Dashboard = lazy(() => import("./pages/Dashboard").then(module => ({default: module.Dashboard})));
const Applications = lazy(() => import("./pages/Applications").then(module => ({default: module.Applications})));
const NewApplication = lazy(() => import("./pages/NewApplication").then(module => ({default: module.NewApplication})));
const DocumentUpload = lazy(() => import("./pages/DocumentUpload").then(module => ({default: module.DocumentUpload})));
const CreditAnalysis = lazy(() => import("./pages/CreditAnalysis").then(module => ({default: module.CreditAnalysis})));
const AIAssistant = lazy(() => import("./pages/AIAssistant").then(module => ({default: module.AIAssistant})));
const WorkflowMonitor = lazy(() => import("./pages/WorkflowMonitor").then(module => ({default: module.WorkflowMonitor})));
const ReportViewer = lazy(() => import("./pages/ReportViewer").then(module => ({default: module.ReportViewer})));
const ReviewQueue = lazy(() => import("./pages/ReviewQueue").then(module => ({default: module.ReviewQueue})));
const AuditTrail = lazy(() => import("./pages/AuditTrail").then(module => ({default: module.AuditTrail})));
const EvaluationDashboard = lazy(() => import("./pages/EvaluationDashboard").then(module => ({default: module.EvaluationDashboard})));
const Monitoring = lazy(() => import("./pages/Monitoring").then(module => ({default: module.Monitoring})));

const pages: PageName[] = ["login", "dashboard", "applications", "new-application", "documents", "analysis", "assistant", "workflow", "report", "reviews", "audit", "evaluation", "monitoring"];

export function App() {
  const {cases, loading, error, refresh} = useCases();
  const location = useLocation(), navigate = useNavigate();
  const requestedPage = (location.pathname.slice(1) || "dashboard") as PageName;
  const page: PageName = pages.includes(requestedPage) ? requestedPage : "dashboard";
  const [selected, setSelected] = useState<CreditCase | null>(null);

  useEffect(() => {
    if (!selected && cases.length) setSelected(cases[0]);
    if (selected) { const fresh = cases.find(item => item.id === selected.id); if (fresh && fresh.version !== selected.version) setSelected(fresh); }
  }, [cases, selected]);

  const created = async (item: CreditCase) => { setSelected(item); await refresh(); navigate("/documents"); };
  const content: Record<PageName, React.ReactNode> = {
    login: <Login/>, dashboard: <Dashboard cases={cases}/>,
    applications: <Applications cases={cases} selected={selected} onSelect={setSelected} onRefresh={refresh}/>,
    "new-application": <NewApplication onCreated={created}/>,
    documents: <DocumentUpload selected={selected} onRefresh={refresh}/>,
    analysis: <CreditAnalysis selected={selected} onRefresh={refresh}/>,
    assistant: <AIAssistant selected={selected}/>, workflow: <WorkflowMonitor selected={selected}/>,
    report: <ReportViewer selected={selected}/>, reviews: <ReviewQueue selected={selected} onRefresh={refresh}/>,
    audit: <AuditTrail selected={selected}/>, evaluation: <EvaluationDashboard/>, monitoring: <Monitoring/>,
  };

  return <Layout page={page} onNavigate={next => navigate(`/${next}`)}>{error && <div className="error" role="alert">{error}</div>}{loading && <p>Loading applications…</p>}<Suspense fallback={<p>Loading page…</p>}>{content[page]}</Suspense></Layout>;
}
