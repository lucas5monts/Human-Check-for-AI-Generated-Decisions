import React, { useState } from 'react';

const RISK_LEVELS = new Set(["green", "yellow", "red"]);

function getRiskLevel(level) {
  const normalizedLevel = level?.toLowerCase();
  return RISK_LEVELS.has(normalizedLevel) ? normalizedLevel : "unknown";
}

const Accordion = ({ applicant }) => {
  const [isActive, setIsActive] = useState(false);
  const riskLevel = getRiskLevel(applicant?.risk_level);
  const triggeredRules = applicant?.triggered_rules ?? [];
  const reviewLabel = applicant?.human_review_required ? "Review required" : "Auto-clear";
  const riskScore = Number(applicant?.risk_score ?? 0);

  return (
    <div className={`accordion-item accordion-item--${riskLevel}`}>
      <button
        className="accordion-title"
        type="button"
        aria-expanded={isActive}
        onClick={() => setIsActive((currentValue) => !currentValue)}
      >
        <div className="title-right">
          <span className="applicant-avatar">{applicant?.applicant_id?.slice(0, 2) ?? "NA"}</span>
          <div>
            <span className="applicant-name">Applicant {applicant?.applicant_id}</span>
            <span className="packet-meta">{applicant?.packet_id}</span>
          </div>
        </div>
        <div className="title-left">
          <span className={`review-pill review-pill--${riskLevel}`}>{riskLevel}</span>
          <span className="accordion-score">{riskScore}%</span>
          <span className="row-chevron" aria-hidden="true">{isActive ? "-" : "+"}</span>
        </div>
      </button>

      {isActive && (
        <div className="accordion-content">
          <div className="risk-meter" aria-label={`${riskScore}% risk score`}>
            <span style={{ width: `${riskScore}%` }} />
          </div>

          <div className="detail-grid">
            <div>
              <span>Packet ID</span>
              <strong>{applicant?.packet_id}</strong>
            </div>
            <div>
              <span>Status</span>
              <strong>{reviewLabel}</strong>
            </div>
            <div>
              <span>Rules triggered</span>
              <strong>{triggeredRules.length}</strong>
            </div>
          </div>

          <div className="rule-list" aria-label="Triggered rules">
            {triggeredRules.length > 0 ? (
              triggeredRules.map((rule) => (
                <div className="rule-row" key={rule.name}>
                  <div>
                    <span>{rule.name}</span>
                    <div className="sub-field">{rule.reason}</div>
                  </div>
                  <span>{rule.points}</span>
                </div>
              ))
            ) : (
              <p className="empty-state">No rules triggered.</p>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default Accordion;
