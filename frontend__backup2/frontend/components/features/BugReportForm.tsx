import React, { useState } from 'react';

interface UploadedFile {
  name: string;
  type: string;
  size: number;
  file: File;
  s3Key?: string;
}

const BugReportForm: React.FC = () => {
  const [files, setFiles] = useState<UploadedFile[]>([]);
  const [formData, setFormData] = useState({
    reporterName: '',
    reporterEmail: '',
    appVersion: '',
    deviceOS: '',
    stepsToReproduce: '',
    expectedResult: '',
    actualResult: '',
    severity: '',
    gdprConsent: false,
    attachments: [] as string[],
  });
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files) return;
    const file = e.target.files[0];
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      // 1. Request presigned URL from backend
      const meta = { name: file.name, type: file.type, size: file.size };
      const res = await fetch('/api/generate-presigned-url', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(meta),
      });
      if (!res.ok) throw new Error('Failed to get presigned URL');
      const { url, key } = await res.json();
      // 2. Upload file to S3
      const uploadRes = await fetch(url, {
        method: 'PUT',
        headers: { 'Content-Type': file.type },
        body: file,
      });
      if (!uploadRes.ok) throw new Error('Failed to upload file');
      // 3. Store S3 key
      setFiles((prev: UploadedFile[]) => [...prev, { name: file.name, type: file.type, size: file.size, file, s3Key: key }]);
      setFormData((prev: typeof formData) => ({ ...prev, attachments: [...prev.attachments, key] }));
    } catch (err: any) {
      setError(err.message || 'Upload error');
    } finally {
      setUploading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData((prev: typeof formData) => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value,
    }));
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(false);
    try {
      const res = await fetch('/api/submit-bug', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(formData),
      });
      if (!res.ok) throw new Error('Failed to submit bug report');
      setSuccess(true);
      setFormData({
        reporterName: '',
        reporterEmail: '',
        appVersion: '',
        deviceOS: '',
        stepsToReproduce: '',
        expectedResult: '',
        actualResult: '',
        severity: '',
        gdprConsent: false,
        attachments: [],
      });
      setFiles([]);
    } catch (err: any) {
      setError(err.message || 'Submission error');
    }
  };

  return (
    <form onSubmit={handleSubmit} className="max-w-lg w-full space-y-4">
      <h2 className="text-xl font-semibold">Bug Report</h2>
      <input
        type="text"
        name="reporterName"
        value={formData.reporterName}
        onChange={handleChange}
        placeholder="Your Name"
        required
        className="w-full border rounded p-2"
      />
      <input
        type="email"
        name="reporterEmail"
        value={formData.reporterEmail}
        onChange={handleChange}
        placeholder="Your Email"
        required
        className="w-full border rounded p-2"
        pattern="^(?:[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+(?:\\.[a-zA-Z0-9!#$%&'*+/=?^_`{|}~-]+)*|\"(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21\\x23-\\x5b\\x5d-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])\")@(?:(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?\\.)+[a-zA-Z0-9](?:[a-zA-Z0-9-]*[a-zA-Z0-9])?|\\[(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?|[a-zA-Z0-9-]*[a-zA-Z0-9]:(?:[\\x01-\\x08\\x0b\\x0c\\x0e-\\x1f\\x21-\\x5a\\x53-\\x7f]|\\\\[\\x01-\\x09\\x0b\\x0c\\x0e-\\x7f])+)\\])$"
      />
      <input
        type="text"
        name="appVersion"
        value={formData.appVersion}
        onChange={handleChange}
        placeholder="App Version (e.g. 1.2.3 (1234))"
        required
        className="w-full border rounded p-2"
        pattern="^\\d+\\.\\d+\\.\\d+\\s\\(\\d+\\)$"
      />
      <input
        type="text"
        name="deviceOS"
        value={formData.deviceOS}
        onChange={handleChange}
        placeholder="Device/OS (e.g. iPad Pro 11\" M2, iPadOS 17.4)"
        required
        className="w-full border rounded p-2"
      />
      <textarea
        name="stepsToReproduce"
        value={formData.stepsToReproduce}
        onChange={handleChange}
        placeholder="Steps to Reproduce (at least 3 lines)"
        required
        className="w-full border rounded p-2"
        rows={4}
      />
      <textarea
        name="expectedResult"
        value={formData.expectedResult}
        onChange={handleChange}
        placeholder="Expected Result"
        required
        className="w-full border rounded p-2"
        rows={2}
      />
      <textarea
        name="actualResult"
        value={formData.actualResult}
        onChange={handleChange}
        placeholder="Actual Result"
        required
        className="w-full border rounded p-2"
        rows={2}
      />
      <select
        name="severity"
        value={formData.severity}
        onChange={handleChange}
        required
        className="w-full border rounded p-2"
      >
        <option value="">Select Severity</option>
        <option value="Critical">Critical</option>
        <option value="High">High</option>
        <option value="Medium">Medium</option>
        <option value="Low">Low</option>
      </select>
      <label className="flex items-center gap-2">
        <input
          type="checkbox"
          name="gdprConsent"
          checked={formData.gdprConsent}
          onChange={handleChange}
          required
        />
        I consent to storage of diagnostic data (GDPR)
      </label>
      <input type="file" onChange={handleFileChange} disabled={uploading} />
      <ul>
        {files.map((f: UploadedFile, i: number) => (
          <li key={i}>{f.name} {f.s3Key ? '✅' : '❌'}</li>
        ))}
      </ul>
      {error && <div style={{ color: 'red' }}>{error}</div>}
      {success && <div style={{ color: 'green' }}>Bug report submitted!</div>}
      <button type="submit" disabled={uploading} className="bg-blue-600 text-white rounded px-4 py-2">Submit</button>
    </form>
  );
};

export default BugReportForm;
