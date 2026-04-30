import { useEffect, useState } from "react";
import Applicant from "./Applicant";
import Header from "./Header";
import { apiUrl } from "../lib/api";

function Dashboard() {
  const [applicants, setApplicants] = useState([]);
  const [status, setStatus] = useState("loading");

  useEffect(() => {
    let isMounted = true;

    async function loadApplicants() {
      try {
        setStatus("loading");
        const response = await fetch(apiUrl("/api/test-data"), {
          method: "GET",
          headers: {
            accept: "application/json",
          },
        });

        if (!response.ok) throw new Error(`HTTP error: ${response.status}`);

        const payload = await response.json();
        if (isMounted && Array.isArray(payload?.data)) {
          setApplicants(payload.data);
          setStatus("ready");
        }
      } catch (error) {
        console.error("Request failed:", error);
        if (isMounted) setStatus("error");
      }
    }

    loadApplicants();

    return () => {
      isMounted = false;
    };
  }, []);

  const addApplicant = (applicant) => {
    setApplicants((currentApplicants) => [applicant, ...currentApplicants]);
    setStatus("ready");
  };

  return (
    <div className="app-shell">
      <aside className="side-rail" aria-label="Primary navigation">
        <div className="rail-brand">
          <div className="rail-logo">SL</div>
          <div>
            <strong>Second Look</strong>
            <span>Audit OS</span>
          </div>
        </div>
        <nav className="rail-nav">
          <span className="rail-section">Workspace</span>
          <a className="rail-link rail-link--active" href="/">
            <span className="rail-icon">01</span>
            <span>Review queue</span>
          </a>
          <a className="rail-link" href={apiUrl("/api/docs")}>
            <span className="rail-icon">02</span>
            <span>Scoring API</span>
          </a>
          <a className="rail-link" href={apiUrl("/api/test-data")}>
            <span className="rail-icon">03</span>
            <span>Test data</span>
          </a>
        </nav>
        <div className="rail-footer">
          <span>Rule engine</span>
          <strong>v1 review model</strong>
        </div>
      </aside>
      <div className="workspace">
        <Header onApplicantAdded={addApplicant} />
        <Applicant applicants={applicants} status={status} />
      </div>
    </div>
  );
}

export default Dashboard;
