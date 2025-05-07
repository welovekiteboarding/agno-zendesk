import { validateConfig } from '../../utils/config';

describe('Config Validation', () => {
  const originalEnv = process.env;

  beforeEach(() => {
    jest.resetModules();
    process.env = { ...originalEnv };
  });

  afterAll(() => {
    process.env = originalEnv;
  });

  (process.env.CI ? test.skip : test)('should throw error when required env vars are missing', () => {
    // Mock process.exit
    const mockExit = jest.spyOn(process, 'exit').mockImplementation((code) => {
      throw new Error(`Process exit with code: ${code}`);
    });

    expect(() => validateConfig()).toThrow();
    expect(mockExit).toHaveBeenCalledWith(1);

    mockExit.mockRestore();
  });

  test('should validate complete configuration', () => {
    // Set all required environment variables
    process.env.ZENDESK_CLIENT_ID = 'test-id';
    process.env.ZENDESK_CLIENT_SECRET = 'test-secret';
    process.env.ZENDESK_REDIRECT_URI = 'https://example.com/callback';
    process.env.STORAGE_BUCKET_NAME = 'test-bucket';
    process.env.STORAGE_REGION = 'us-east-1';
    process.env.STORAGE_ACCESS_KEY = 'test-access';
    process.env.STORAGE_SECRET_KEY = 'test-secret';
    process.env.AGNO_API_KEY = 'test-agno-key';
    process.env.AGNO_PROJECT_ID = 'test-project-id';

    const config = validateConfig();
    expect(config).toBeDefined();
    expect(config.ZENDESK_CLIENT_ID).toBe('test-id');
    expect(config.PORT).toBe(3000); // Default value
  });
});
