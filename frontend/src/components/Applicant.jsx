import { useMemo, useState } from 'react';
import Accordion from './Accordion';

const RISK_LEVELS = ["red", "yellow", "green"];
const SORT_OPTIONS = {
  highestRisk: "Highest risk",
  lowestRisk: "Lowest risk",
  applicant: "Applicant ID",
};

function getRiskCounts(applicants) {
  return applicants.reduce(
    (counts, applicant) => {
      const level = applicant.risk_level?.toLowerCase();
      if (level in counts) counts[level] += 1;
      return counts;
    },
    { red: 0, yellow: 0, green: 0 },
  );
}

function getAverageScore(applicants) {
  if (applicants.length === 0) return 0;

  const total = applicants.reduce((sum, applicant) => sum + Number(applicant.risk_score ?? 0), 0);
  return Math.round(total / applicants.length);
}

function filterApplicants(applicants, riskFilter, reviewFilter, searchTerm) {
  const normalizedSearch = searchTerm.trim().toLowerCase();

  return applicants.filter((applicant) => {
    const riskMatches = riskFilter === "all" || applicant.risk_level?.toLowerCase() === riskFilter;
    const reviewMatches =
      reviewFilter === "all" ||
      (reviewFilter === "required" && applicant.human_review_required) ||
      (reviewFilter === "clear" && !applicant.human_review_required);
    const searchMatches =
      normalizedSearch.length === 0 ||
      applicant.applicant_id?.toLowerCase().includes(normalizedSearch) ||
      applicant.packet_id?.toLowerCase().includes(normalizedSearch);

    return riskMatches && reviewMatches && searchMatches;
  });
}

function sortApplicants(applicants, sortOption) {
  return [...applicants].sort((first, second) => {
    if (sortOption === "lowestRisk") {
      return Number(first.risk_score ?? 0) - Number(second.risk_score ?? 0);
    }

    if (sortOption === "applicant") {
      return String(first.applicant_id ?? "").localeCompare(String(second.applicant_id ?? ""));
    }

    return Number(second.risk_score ?? 0) - Number(first.risk_score ?? 0);
  });
}

function Applicant({ applicants = [], status = "ready" }) {
  const [riskFilter, setRiskFilter] = useState("all");
  const [reviewFilter, setReviewFilter] = useState("all");
  const [sortOption, setSortOption] = useState("highestRisk");
  const [searchTerm, setSearchTerm] = useState("");
  const riskCounts = getRiskCounts(applicants);
  const averageScore = getAverageScore(applicants);
  const needsReview = applicants.filter((applicant) => applicant.human_review_required).length;
  const reviewRate = applicants.length === 0 ? 0 : Math.round((needsReview / applicants.length) * 100);
  const highRiskShare = applicants.length === 0 ? 0 : Math.round((riskCounts.red / applicants.length) * 100);
  const visibleApplicants = useMemo(() => {
    const filteredApplicants = filterApplicants(applicants, riskFilter, reviewFilter, searchTerm);
    return sortApplicants(filteredApplicants, sortOption);
  }, [applicants, riskFilter, reviewFilter, searchTerm, sortOption]);

  return (
    <main className="dashboard">
      <section className="page-intro">
        <div>
          <p className="eyebrow">Decision assurance</p>
          <h1>AI hiring review workspace</h1>
          <p className="hero-copy">
            Triage automated hiring packets by transparency, evidence strength, and human oversight needs.
          </p>
        </div>

        <div className="intro-actions">
          <span>{status === "loading" ? "Syncing" : status === "error" ? "Offline" : "Ready"}</span>
          <strong>{visibleApplicants.length}</strong>
          <small>visible packets</small>
        </div>
      </section>

      <section className="metric-grid" aria-label="Audit summary">
        <div className="metric-card metric-card--primary">
          <span className="metric-label">Packets</span>
          <strong>{applicants.length}</strong>
          <small>Total reviewed in this queue</small>
        </div>
        <div className="metric-card metric-card--review">
          <span className="metric-label">Human review</span>
          <strong>{needsReview}</strong>
          <div className="metric-bar" aria-label={`${reviewRate}% require review`}>
            <span style={{ width: `${reviewRate}%` }} />
          </div>
        </div>
        {RISK_LEVELS.map((level) => (
          <div className={`metric-card metric-card--${level}`} key={level}>
            <span className="metric-label">{level}</span>
            <strong className={`metric-value metric-value--${level}`}>{riskCounts[level]}</strong>
            <small>{level === "red" ? "Escalate first" : level === "yellow" ? "Needs attention" : "Low concern"}</small>
          </div>
        ))}
      </section>

      <section className="workbench">
        <div className="review-panel">
          <div className="panel-header">
            <div>
              <h2>Applicant Decisions</h2>
              <p>Risk-ranked packet review queue</p>
            </div>
            <span className="panel-count">{visibleApplicants.length} shown</span>
          </div>

          <div className="toolbar" aria-label="Review queue controls">
            <label className="search-control">
              <span>Search</span>
              <input
                type="search"
                value={searchTerm}
                placeholder="Applicant or packet ID"
                onChange={(event) => setSearchTerm(event.target.value)}
              />
            </label>

            <label>
              <span>Risk</span>
              <select value={riskFilter} onChange={(event) => setRiskFilter(event.target.value)}>
                <option value="all">All risk</option>
                {RISK_LEVELS.map((level) => (
                  <option value={level} key={level}>
                    {level}
                  </option>
                ))}
              </select>
            </label>

            <label>
              <span>Review</span>
              <select value={reviewFilter} onChange={(event) => setReviewFilter(event.target.value)}>
                <option value="all">All packets</option>
                <option value="required">Required</option>
                <option value="clear">Auto-clear</option>
              </select>
            </label>

            <label>
              <span>Sort</span>
              <select value={sortOption} onChange={(event) => setSortOption(event.target.value)}>
                {Object.entries(SORT_OPTIONS).map(([value, label]) => (
                  <option value={value} key={value}>
                    {label}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <div className="accordion">
            {status === "loading" && <p className="empty-state">Loading applicant packets...</p>}
            {status === "error" && <p className="empty-state">Unable to load applicant packets.</p>}
            {status === "ready" && applicants.length === 0 && <p className="empty-state">No applicant packets found.</p>}
            {status === "ready" && applicants.length > 0 && visibleApplicants.length === 0 && (
              <p className="empty-state">No packets match the current filters.</p>
            )}
            {visibleApplicants.map((applicant) => (
              <Accordion
                key={applicant.client_id ?? applicant.source_file ?? `${applicant.packet_id}-${applicant.applicant_id}`}
                applicant={applicant}
              />
            ))}
          </div>
        </div>

        <aside className="insight-panel" aria-label="Queue insights">
          <div className="insight-card insight-card--dark">
            <span>Average risk</span>
            <strong>{averageScore}</strong>
            <div className="insight-meter">
              <span style={{ width: `${averageScore}%` }} />
            </div>
          </div>
          <div className="insight-card">
            <span>Review load</span>
            <strong>{reviewRate}%</strong>
            <p>{needsReview} packets currently require human review.</p>
          </div>
          <div className="insight-card">
            <span>High-risk share</span>
            <strong>{highRiskShare}%</strong>
            <p>{riskCounts.red} packets should be escalated before routine review.</p>
          </div>
        </aside>
      </section>
    </main>
  );
}

export default Applicant;
