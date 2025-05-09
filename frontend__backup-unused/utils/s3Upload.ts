// Utility to upload a file to S3 using a presigned URL from the backend

export async function uploadFileToS3({
  file,
  backendUrl = '/api/generate-presigned-url',
}: {
  file: File;
  backendUrl?: string;
}): Promise<{ key: string; url: string }> {
  // 1. Request a presigned URL from the backend
  const meta = {
    name: file.name,
    type: file.type,
    size: file.size,
  };
  const res = await fetch(backendUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(meta),
  });
  if (!res.ok) throw new Error('Failed to get presigned URL');
  const { url, key } = await res.json();

  // 2. Upload the file to S3
  const uploadRes = await fetch(url, {
    method: 'PUT',
    headers: { 'Content-Type': file.type },
    body: file,
  });
  if (!uploadRes.ok) throw new Error('Failed to upload file to S3');

  // 3. Return the S3 key for use in the bug report
  return { key, url };
}
