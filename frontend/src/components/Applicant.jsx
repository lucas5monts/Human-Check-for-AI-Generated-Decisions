import react from 'react';
import Accordion from './Accordion';

function Applicant({data}) {
    return (
        <div className='Card'>
            <div className="header">Second Look ATS Auditing Tool</div>
            <div className="accordion">
                {data?.data.map((item, index) => (
                    <Accordion key={index} data={item} />
                ))}
            </div>
        </div>
    )
}

export default Applicant;

