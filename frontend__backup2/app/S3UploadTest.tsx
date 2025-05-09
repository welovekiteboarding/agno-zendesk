import React, { useState } from 'react';

export default function S3UploadTest() {
  const [file, setFile] = useState<File | null>(null);
  const [status, setStatus] = useState('');

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (!selected) return;
    setFile(selected);
    setStatus('Requesting presigned URL...');
    // 1. Request presigned URL
    const meta = {
      name: selected.name,
      type: selected.type,
      size: selected.size,
    };
    const res = await fetch('http://localhost:8001/generate-presigned-url', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(meta),
    });
    if (!res.ok) {
      setStatus('Failed to get presigned URL');
      return;
    }
    const { url, key } = await res.json();
    setStatus('Uploading to S3...');
    // 2. Upload file to S3
    const uploadRes = await fetch(url, {
      method: 'PUT',
      body: selected,
      headers: { 'Content-Type': selected.type },
    });
    if (!uploadRes.ok) {
      setStatus('Failed to upload to S3');
      return;
    }
    setStatus(`Upload successful! S3 key: ${key}`);
  };

  return (
    <div>
      <h2>S3 Upload Test</h2>
      <input type="file" onChange={handleFileChange} />
      <p>{status}</p>
    </div>
  );
}
