# UnifiedChatUI Component Testing

This document outlines the testing procedures for validating the UnifiedChatUI component implementation for Task #21.

## Bug Report Submission Workflow

### Test Case: Complete Bug Report Submission Flow

**Prerequisites:**
- Application running on localhost:3000
- Backend running on localhost:8001
- Network connectivity for S3/R2 file uploads

**Test Steps:**

1. **Initial Load**
   - Navigate to http://localhost:3000
   - Verify the UI loads with the Agno greeting
   - Expected: "Hi! I'm Agno, your AI assistant. How can I help you today? I can answer general questions or help you report bugs when needed."

2. **Initiate Bug Report**
   - Enter the message: "I want to report a bug"
   - Click Send
   - Expected: Agno acknowledges and offers to help with bug reporting or transfer to bug report agent

3. **Agent Handoff**
   - Wait for the message acknowledging the handoff to bug report agent
   - Expected: Message indicating handoff to bug report specialist

4. **Email Collection**
   - Verify email input field appears
   - Enter a valid email: "test@example.com"
   - Click Submit
   - Expected: Form collector agent acknowledges email and asks for bug details

5. **Bug Description**
   - Enter detailed bug description
   - Click Send
   - Expected: Agent responds and prompts for additional details or file attachments

6. **File Upload**
   - When prompted to upload files, verify the file upload section appears
   - Upload a test image file (use test-image.jpg from the test assets)
   - Verify upload progress indicators work
   - Verify scan status updates (Uploading → Scanning → Clean)
   - Expected: File successfully uploads and shows as "Clean (ready)"

7. **Final Submission**
   - After uploading files, verify the "Submit Report" button appears
   - Click "Submit Report"
   - Expected: Confirmation message that the report has been submitted successfully

8. **Verification**
   - Verify UI state resets after submission
   - Check that file upload UI is no longer visible
   - Expected: Chat returns to normal state, ready for new conversation

### Test Case: Bug Report Submission Without Attachments

**Test Steps:**

1. Follow steps 1-4 from previous test case
2. When prompted for file attachments, click "Skip"
3. Verify the ability to continue the conversation
4. Verify "Submit Report" button appears
5. Complete submission without attachments
6. Expected: Report submits successfully without requiring file attachments

### Test Case: Failed Upload Recovery

**Test Steps:**

1. Follow steps 1-4 from first test case
2. Upload a file with a simulated network failure (can be tested by disconnecting network during upload)
3. Verify error handling shows appropriate message
4. Attempt to retry the upload
5. Complete the submission
6. Expected: System recovers from failed upload and allows completion of report

## UI Instruction Protocol Integration

### Test Case: UI Instruction Sequence

**Test Steps:**

1. Navigate to http://localhost:3000/?ui_debug=true to enable debug mode
2. Start a conversation that triggers multiple UI instructions
3. Verify the instruction queue appears in debug mode
4. Verify instructions execute in correct priority order
5. Expected: Instructions queue and execute properly with visible debugging information

### Test Case: Form Display and Submission

**Test Steps:**

1. Trigger a conversation that results in a form being displayed
2. Verify all form fields render correctly
3. Fill out the form with test data
4. Submit the form
5. Verify the form data is sent correctly to the backend
6. Expected: Form displays, accepts input, and submits successfully

## Cross-Browser Testing

Test the unified interface on the following browsers:

1. Google Chrome (latest)
2. Firefox (latest)
3. Safari (if available)
4. Mobile browser (Chrome on Android or Safari on iOS)

Verify the UI renders correctly and all functionality works across browsers.

## Responsiveness Testing

Test the unified interface on the following screen sizes:

1. Desktop (1920x1080)
2. Laptop (1366x768)
3. Tablet (768x1024)
4. Mobile (375x667)

Verify the UI adapts correctly to different screen sizes and remains functional.

## Performance Testing

1. Test with a long conversation (20+ messages)
2. Verify scroll performance remains smooth
3. Verify state persistence works correctly with large conversation history
4. Expected: UI remains responsive and performant with extended use

## Accessibility Testing

1. Verify keyboard navigation works for all interactive elements
2. Check contrast ratios for text elements
3. Verify screen reader compatibility for key UI elements
4. Expected: Interface meets WCAG 2.1 AA standards

## Results Documentation

For each test case, document:
- Pass/Fail status
- Screenshots of key steps
- Any issues encountered
- Browser/device information

This comprehensive testing ensures the UnifiedChatUI component meets all requirements specified in Task #21.