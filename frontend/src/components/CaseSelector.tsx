import type {CreditCase} from "../types";
import {StatusBadge} from "./StatusBadge";

export function CaseSelector({
  cases,
  selected,
  onSelect,
}: {
  cases: CreditCase[];
  selected: CreditCase | null;
  onSelect: (item: CreditCase) => void;
}) {
  if (!cases.length) return <p className="muted">No applications have been created.</p>;
  return <div className="case-grid">{cases.map(item => (
    <button className={`case-card ${selected?.id === item.id ? "selected" : ""}`} key={item.id} onClick={() => onSelect(item)}>
      <b>{item.borrower_name}</b>
      <span>${Number(item.requested_amount).toLocaleString()}</span>
      <StatusBadge status={item.status} />
    </button>
  ))}</div>;
}
