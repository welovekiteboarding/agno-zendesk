import React from 'react';

const BugReportForm: React.FC = () => {
  return (
    <form>
      <h2>Bug Report</h2>
      <input type="text" name="reporterName" placeholder="Your Name" required />
      <button type="submit">Submit</button>
    </form>
  );
};

export default BugReportForm;
