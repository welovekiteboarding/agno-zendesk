# File Upload Functionality Testing

This document outlines the testing procedures for validating file upload functionality in the UnifiedChatUI component across different agent types.

## Testing Matrix

Test each scenario with the following agent types:
1. **Agno Agent** (Generic AI assistant)
2. **Bug Report Agent** (Form collector specialized agent)

## Test Cases

### Test Case FU-1: Basic File Upload Flow

**Description**: Verify the basic file upload functionality works correctly with valid files.

**Steps for Agno Agent:**
1. Navigate to http://localhost:3000 (main interface)
2. Start a conversation with "I want to upload a file"
3. Wait for the file upload UI to appear
4. Upload a valid image file (< 5MB)
5. Verify upload progress indicators function correctly
6. Verify scan status updates (Uploading → Scanning → Clean)
7. Verify success message appears with file information

**Steps for Bug Report Agent:**
1. Navigate to http://localhost:3000
2. Start a conversation with "I want to report a bug"
3. Complete the email collection step
4. When prompted about attachments, wait for file upload UI
5. Upload a valid image file (< 5MB)
6. Verify upload progress indicators function correctly
7. Verify scan status updates (Uploading → Scanning → Clean)
8. Verify the Submit button appears when files are ready

**Expected Results:**
- File upload UI appears correctly for both agent types
- Upload progress is displayed clearly
- Scanning status updates properly
- Success confirmation shows when file is ready
- File information is accessible to the agent for further processing

### Test Case FU-2: Multiple File Upload

**Description**: Verify support for uploading multiple files simultaneously.

**Steps:**
1. Follow initial steps from Test Case FU-1 for either agent type
2. When the file upload UI appears, select 3 different files simultaneously
   - Use a mix of file types (image, PDF, text file)
   - Ensure total size is under the limit (< 100MB total)
3. Verify upload progress for all files
4. Verify scan status updates for all files
5. Verify all files appear in the uploaded files list
6. Continue conversation after uploads complete

**Expected Results:**
- Multiple files upload correctly in parallel
- Individual progress and status indicators work for each file
- All files are properly processed
- Conversation can continue with references to all uploaded files

### Test Case FU-3: File Size Limits

**Description**: Verify file size validation functions correctly.

**Steps:**
1. Follow initial steps from Test Case FU-1 for either agent type
2. When the file upload UI appears, attempt to upload a file > 100MB
3. Verify size validation error appears
4. Try uploading a valid file after the error
5. Verify valid file uploads successfully despite previous error

**Expected Results:**
- Clear error message when file exceeds size limit
- No partial upload of oversized files
- System recovers gracefully after size validation error
- Valid files can be uploaded after error condition

### Test Case FU-4: File Type Validation

**Description**: Verify file type validation functions correctly.

**Steps:**
1. Follow initial steps from Test Case FU-1 for either agent type
2. When the file upload UI appears, attempt to upload unsupported file types
   (e.g., .exe, .zip if restricted)
3. Verify file type validation error appears
4. Try uploading a supported file type after the error
5. Verify valid file uploads successfully despite previous error

**Expected Results:**
- Clear error message for unsupported file types
- System recovers gracefully after type validation error
- Valid files can be uploaded after error condition

### Test Case FU-5: Upload Cancellation

**Description**: Verify ability to cancel uploads or remove files.

**Steps:**
1. Follow initial steps from Test Case FU-1 for either agent type
2. Start uploading a larger file (10-20MB)
3. During upload, click the cancel/remove button
4. Verify file is removed from the queue
5. Try uploading a different file after cancellation
6. Verify new file uploads successfully

**Expected Results:**
- Upload can be cancelled during progress
- UI updates correctly after cancellation
- System recovers gracefully for new uploads

### Test Case FU-6: Network Failure Recovery

**Description**: Verify system handles network interruptions gracefully.

**Steps:**
1. Follow initial steps from Test Case FU-1 for either agent type
2. Start uploading a file
3. Simulate network interruption (disconnect wifi/ethernet)
4. Verify error message appears
5. Reconnect network
6. Attempt to retry the upload
7. Verify upload completes successfully on retry

**Expected Results:**
- Clear error message for network failures
- Retry option available
- Successful recovery after network restoration

### Test Case FU-7: Virus Scan Detection (Simulated)

**Description**: Verify system handles infected files correctly (requires backend simulation).

**Steps:**
1. Follow initial steps from Test Case FU-1 for either agent type
2. Configure backend to simulate virus detection for specific test file
3. Upload the test file marked for simulation
4. Verify "Infected" status appears
5. Verify file is not available for further processing
6. Try uploading a clean file afterward
7. Verify clean file uploads successfully

**Expected Results:**
- Clear warning when file is marked as infected
- Infected files are quarantined/deleted
- System recovers for clean files

### Test Case FU-8: Skip Attachment Option

**Description**: Verify "Skip" functionality for optional file uploads.

**Steps for Bug Report Agent:**
1. Follow steps to initiate bug report and reach file upload prompt
2. When file upload UI appears, click "Skip" instead of uploading
3. Verify conversation continues appropriately
4. Verify Submit button appears even without uploads

**Expected Results:**
- Skip option works correctly
- Conversation flow continues without requiring attachments
- Report can be submitted without files

### Test Case FU-9: Drag-and-Drop Functionality

**Description**: Verify drag-and-drop support for file uploads.

**Steps:**
1. Follow initial steps from Test Case FU-1 for either agent type
2. When file upload UI appears, drag a file from desktop into the drop zone
3. Verify file is accepted and upload begins
4. Verify upload completes successfully

**Expected Results:**
- Drop zone visually responds to drag enter/leave events
- Files dropped are processed correctly
- Upload begins automatically after drop

### Test Case FU-10: Session Persistence

**Description**: Verify uploads persist through page refreshes.

**Steps:**
1. Start a conversation that reaches file upload step
2. Upload a file but don't complete the process
3. Refresh the page
4. Verify the conversation state is restored
5. Verify uploaded files are still available

**Expected Results:**
- Conversation state persists through refresh
- File upload status persists
- User can continue from previous state

## Documentation

For each test case, document:
- Test case ID and description
- Test date and tester name
- Environment (browser, OS)
- Pass/Fail status
- Screenshots of key steps
- Any issues encountered
- Notes on browser/device variations

This comprehensive testing ensures file upload functionality works correctly across all supported agent types and scenarios.