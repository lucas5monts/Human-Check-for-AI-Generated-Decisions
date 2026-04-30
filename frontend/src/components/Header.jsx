import React, { useState } from 'react';
import { apiUrl } from '../lib/api';

const Header = ({ onApplicantAdded }) => {
  const [isUploading, setIsUploading] = useState(false);

  const handleFileUpload = async (event) => {
    const file = event.target.files[0];
    if (!file) return;

    setIsUploading(true);
    try {
      const fileText = await file.text();

      const response = await fetch(apiUrl('/api/audit'), {
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
      onApplicantAdded?.(newApplicant);
    } catch (error) {
      console.error("Failed to upload JSON:", error);
      alert("There was an error processing the upload.");
    } finally {
      setIsUploading(false);
      event.target.value = '';
    }
  };

  return (
    <header className="page-header">
      <div className="brand-lockup">
        <span className="brand-mark">SL</span>
        <div>
          <strong>Second Look</strong>
          <span>ATS audit console</span>
        </div>
      </div>

      <label className="upload-button" htmlFor="json-upload">
        {isUploading ? 'Uploading...' : 'Upload packet'}
      </label>
      <input
        id="json-upload"
        className="file-input"
        type="file"
        accept=".json"
        onChange={handleFileUpload}
        disabled={isUploading}
      />
    </header>
  );
};

export default Header;
