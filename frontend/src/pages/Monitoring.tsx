import {useState} from "react";
import {api} from "../services/api";

export function Monitoring() {
  const [metrics, setMetrics] = useState(""), [error, setError] = useState("");
  const load = async () => { try { setMetrics(await api.getMetrics()); setError(""); } catch (caught) { setError(String(caught)); } };
  return <><h2>Monitoring</h2><p>Grafana is available on port 3000 in the Docker Compose stack. Local Prometheus exposition can be inspected below.</p><button onClick={load}>Load current metrics</button>{error && <div className="error">{error}</div>}{metrics && <pre>{metrics}</pre>}</>;
}
