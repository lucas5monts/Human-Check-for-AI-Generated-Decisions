import Accordion from './Accordion';

const RISK_LEVELS = ["red", "yellow", "green"];

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

function Applicant({ applicants = [], status = "ready" }) {
  const riskCounts = getRiskCounts(applicants);
  const averageScore = getAverageScore(applicants);
  const needsReview = applicants.filter((applicant) => applicant.human_review_required).length;

  return (
    <main className="dashboard">
      <section className="hero-panel">
        <div>
          <p className="eyebrow">Decision assurance</p>
          <h1>Second Look</h1>
          <p className="hero-copy">
            Review automated hiring decisions by risk, evidence quality, and human oversight needs.
          </p>
        </div>

        <div className="hero-score">
          <span>{averageScore}</span>
          <small>avg risk</small>
        </div>
      </section>

      <section className="metric-grid" aria-label="Audit summary">
        <div className="metric-card">
          <span className="metric-label">Packets</span>
          <strong>{applicants.length}</strong>
        </div>
        <div className="metric-card">
          <span className="metric-label">Human review</span>
          <strong>{needsReview}</strong>
        </div>
        {RISK_LEVELS.map((level) => (
          <div className="metric-card" key={level}>
            <span className="metric-label">{level}</span>
            <strong className={`metric-value metric-value--${level}`}>{riskCounts[level]}</strong>
          </div>
        ))}
      </section>

      <section className="review-panel">
        <div className="panel-header">
          <div>
            <h2>Applicant Decisions</h2>
            <p>Risk-ranked packet review queue</p>
          </div>
          <span className="panel-count">{applicants.length} total</span>
        </div>

        <div className="accordion">
          {status === "loading" && <p className="empty-state">Loading applicant packets...</p>}
          {status === "error" && <p className="empty-state">Unable to load applicant packets.</p>}
          {status === "ready" && applicants.length === 0 && <p className="empty-state">No applicant packets found.</p>}
          {applicants.map((applicant) => (
            <Accordion key={applicant.source_file ?? applicant.packet_id} applicant={applicant} />
          ))}
        </div>
      </section>
    </main>
  );
}

export default Applicant;
