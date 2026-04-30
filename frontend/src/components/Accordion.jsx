import React, { useState } from 'react';

const styles = {
  redColor: {
    backgroundColor: 'red'
  },
  yellowColor: {
    backgroundColor: 'yellow'
  },
  greenColor: {
    backgroundColor: 'green'
  },
};

function getLevelStyle(level) {
  switch (level?.toLowerCase()) {
    case "green":  return styles.greenColor;
    case "yellow": return styles.yellowColor;
    case "red":    return styles.redColor;
    default:       return {};
  }
}

const Accordion = ({ data }) => {
  const [isActive, setIsActive] = useState(false);

  return (
    <div className="accordion-item">
      <div className="accordion-title" onClick={() => setIsActive(!isActive)}>
        <div className="title-right">
          <div></div>
          <div>Applicant: {data?.applicant_id}</div>
        </div>
        <div className='title-left'>
          <div className="accordion-score">{data?.risk_score}%</div>
          <div className="accordion-level" style={getLevelStyle(data?.risk_level)}>
            
          </div>
        </div>
      </div>
        {isActive && <div className="accordion-content">
          <ul>
            <li><span>PacketID:</span> <span>{data?.packet_id}</span></li>
            <li>Triggered Rules:</li>
            <ul>
              {data?.triggered_rules.map((item, index) => (
                <li key={index}>
                  <div>
                    <span>{item.name}</span>
                    <div className="sub-field">{item.reason}</div>
                  </div>
                  <span>{item.points}</span>
                </li>
              ))}
            </ul>
          </ul>
          
        </div>}
    </div>
  );
};

export default Accordion;