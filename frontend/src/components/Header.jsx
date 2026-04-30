import React, { useState } from 'react';

const Header = ({ onApplicantAdded }) => {
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    try {
      // Read the uploaded file text (assuming it's formatted as JSON)
      const fileText = await file.text();
      
      // Send the JSON payload off to the endpoint
      const response = await fetch('/api/audit', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: fileText,
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const newApplicant = await response.json();
      
      // Pass the new applicant up to the parent component to update the UI
      if (onApplicantAdded) {
        onApplicantAdded(newApplicant);
      }
    } catch (error) {
      console.error("Failed to upload JSON:", error);
      alert("There was an error processing the upload.");
    } finally {
      setIsUploading(false);
      // Reset the file input so the same file could be selected again
      event.target.value = '';
    }
  };

  return (
    <header className="page-header" style={{ display: 'flex', justifyContent: 'space-between', padding: '1rem' }}>
      <div>
        <label htmlFor="json-upload" style={{ cursor: 'pointer', padding: '8px 16px', backgroundColor: '#007bff', color: '#fff', borderRadius: '4px' }}>
          {isUploading ? 'Uploading...' : 'Upload JSON'}
        </label>
        <input
          id="json-upload"
          type="file"
          accept=".json"
          onChange={handleFileUpload}
          style={{ display: 'none' }}
          disabled={isUploading}
        />
      </div>
    </header>
  );
};

export default Header;