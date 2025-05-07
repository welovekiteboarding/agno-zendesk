import * as dotenv from 'dotenv';
import { z } from 'zod';

// Load environment variables
dotenv.config();

// Define environment schema with validation
const envSchema = z.object({
  // Zendesk
  ZENDESK_CLIENT_ID: z.string().min(1),
  ZENDESK_CLIENT_SECRET: z.string().min(1),
  ZENDESK_REDIRECT_URI: z.string().url(),

  // Storage
  STORAGE_BUCKET_NAME: z.string().min(1),
  STORAGE_REGION: z.string().min(1),
  STORAGE_ACCESS_KEY: z.string().min(1),
  STORAGE_SECRET_KEY: z.string().min(1),

  // AGNO
  AGNO_API_KEY: z.string().min(1),
  AGNO_PROJECT_ID: z.string().min(1),

  // Analytics
  ANALYTICS_KEY: z.string().optional(),

  // App
  NODE_ENV: z.enum(['development', 'test', 'production']).default('development'),
  PORT: z.string().transform(val => parseInt(val, 10)).default('3000')
});

// Validate and export config
export function validateConfig() {
  try {
    return envSchema.parse(process.env);
  } catch (error: any) {
    console.error('❌ Invalid environment variables:', error.format());
    process.exit(1);
  }
}

export const config = validateConfig();
