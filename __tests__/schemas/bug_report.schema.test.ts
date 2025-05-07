import Ajv from "ajv";
import schema from "../../schemas/bug_report.schema.json";

const ajv = new Ajv();

describe("Bug Report Schema", () => {
  it("should validate a valid bug report payload", () => {
    const validPayload = {
      reporterName: "Alice Example",
      reporterEmail: "alice@example.com",
      appVersion: "1.2.3 (1234)",
      deviceOS: "iPad Pro 11\" M2, iPadOS 17.4",
      stepsToReproduce: "1. Open app\n2. Tap 'Observe'\n3. Crash occurs",
      expectedResult: "Star chart opens.",
      actualResult: "App quits to Home screen.",
      severity: "High",
      gdprConsent: true,
      attachments: ["screenshot.png", "log.txt"]
    };
    const validate = ajv.compile(schema);
    const valid = validate(validPayload);
    expect(valid).toBe(true);
  });

  it("should fail validation for missing required fields", () => {
    const invalidPayload = {
      reporterName: "Bob Example"
      // missing other required fields
    };
    const validate = ajv.compile(schema);
    const valid = validate(invalidPayload);
    expect(valid).toBe(false);
  });
});
