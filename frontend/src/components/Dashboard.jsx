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
      <Header onApplicantAdded={addApplicant} />
      <Applicant applicants={applicants} status={status} />
    </div>
  );
}

export default Dashboard;
