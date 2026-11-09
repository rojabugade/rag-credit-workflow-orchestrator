import type {PageName} from "../types";

const navigation: Array<[PageName, string]> = [
  ["login", "Login / role"],
  ["dashboard", "Dashboard"],
  ["applications", "Applications"],
  ["new-application", "New application"],
  ["documents", "Documents"],
  ["analysis", "Credit analysis"],
  ["workflow", "Workflow monitor"],
  ["report", "Report viewer"],
  ["reviews", "Review queue"],
  ["assistant", "Evidence assistant"],
  ["audit", "Audit trail"],
  ["evaluation", "AI evaluation"],
  ["monitoring", "Monitoring"],
];

export function Layout({
  page,
  onNavigate,
  children,
}: {
  page: PageName;
  onNavigate: (page: PageName) => void;
  children: React.ReactNode;
}) {
  return (
    <>
      <header><h1>CreditRisk AI</h1><span>Human-supervised underwriting</span></header>
      <div className="shell">
        <nav aria-label="Primary navigation">
          {navigation.map(([value, label]) => (
            <button className={page === value ? "active" : ""} key={value} onClick={() => onNavigate(value)}>
              {label}
            </button>
          ))}
        </nav>
        <main className="page-content">{children}</main>
      </div>
    </>
  );
}
