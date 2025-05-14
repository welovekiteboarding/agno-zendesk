import { deserializeUIInstruction, UIInstructionValidationError } from "./uiInstruction.ts";
import examples from "../../schemas/ui_instruction_examples.json" with { type: "json" };

function testValidation() {
  let validPassed = 0;
  let validFailed = 0;
  let invalidPassed = 0;
  let invalidFailed = 0;

  for (const [i, ex] of examples.valid_examples.entries()) {
    try {
      deserializeUIInstruction(JSON.stringify(ex));
      console.log(`valid_examples[${i}] passed as expected`);
      validPassed++;
    } catch (e) {
      console.error(`valid_examples[${i}] failed:`, e);
      validFailed++;
    }
  }

  for (const [i, ex] of examples.invalid_examples.entries()) {
    try {
      deserializeUIInstruction(JSON.stringify(ex));
      console.error(`invalid_examples[${i}] should have failed but passed`);
      invalidPassed++;
    } catch (e) {
      console.log(`invalid_examples[${i}] correctly failed`);
      invalidFailed++;
    }
  }

  console.log("\nSummary:");
  console.log(`Valid examples passed: ${validPassed}`);
  console.log(`Valid examples failed: ${validFailed}`);
  console.log(`Invalid examples passed (should fail): ${invalidPassed}`);
  console.log(`Invalid examples failed (as expected): ${invalidFailed}`);
}

testValidation();