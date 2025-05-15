// Zendesk API configuration
// These values should be set in environment variables for security

export const zendeskConfig = {
  // Zendesk subdomain (e.g., 'yourcompany' from yourcompany.zendesk.com)
  subdomain: process.env.ZENDESK_SUBDOMAIN || 'yourzendesksubdomain',
  
  // Zendesk API token (used for authentication)
  apiToken: process.env.ZENDESK_API_TOKEN || '',
  
  // Email address of the Zendesk agent account (required for API token auth)
  email: process.env.ZENDESK_EMAIL || 'your-email@example.com',
  
  // Default ticket fields
  defaultPriority: process.env.ZENDESK_DEFAULT_PRIORITY || 'normal',
  defaultType: process.env.ZENDESK_DEFAULT_TYPE || 'problem',
  defaultSource: process.env.ZENDESK_DEFAULT_SOURCE || 'web',
  
  // Group ID for ticket assignment (optional)
  groupId: process.env.ZENDESK_GROUP_ID || '',
  
  // Storage configuration for attachment handling
  // Check for AWS credentials first, then fall back to R2
  useAwsS3: Boolean(process.env.AWS_ACCESS_KEY_ID && process.env.AWS_SECRET_ACCESS_KEY),
  
  // AWS S3 configuration
  awsBucketName: process.env.AWS_BUCKET_NAME || 'agno-zendesk-uploads',
  awsAccessKeyId: process.env.AWS_ACCESS_KEY_ID || '',
  awsSecretAccessKey: process.env.AWS_SECRET_ACCESS_KEY || '',
  awsRegion: process.env.AWS_DEFAULT_REGION || 'ca-central-1',
  
  // R2 configuration (alternative to AWS S3)
  r2BucketName: process.env.R2_BUCKET_NAME || 'your-bucket-name',
  r2AccessKey: process.env.R2_ACCESS_KEY || '',
  r2SecretKey: process.env.R2_SECRET_KEY || '',
  r2Endpoint: process.env.R2_ENDPOINT || '',
};

// Helper to validate if the config has all required values set
export function isConfigValid(): boolean {
  return Boolean(
    zendeskConfig.subdomain && 
    zendeskConfig.apiToken && 
    zendeskConfig.email
  );
}

// Get the Zendesk API URL
export function getZendeskApiUrl(path: string): string {
  return `https://${zendeskConfig.subdomain}.zendesk.com/api/v2/${path}`;
}

// Get the authorization header for Zendesk API
export function getZendeskAuthHeader(): string {
  // Using API token authentication
  // Format: {email}/token:{api_token}
  const credentials = `${zendeskConfig.email}/token:${zendeskConfig.apiToken}`;
  const base64Credentials = Buffer.from(credentials).toString('base64');
  return `Basic ${base64Credentials}`;
}