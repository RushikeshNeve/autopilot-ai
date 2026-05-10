import assert from "node:assert/strict";

import { parsePlanningCritiqueIssues, parsePlanningCritiqueSummary } from "./critique-parser.js";

function run() {
  const normalizedIssues = parsePlanningCritiqueIssues([
    {
      issue_type: "missing_dependency",
      severity: "high",
      description: "Task B does not depend on Task A.",
      recommendation: "Add the missing dependency.",
    },
  ]);

  assert.equal(normalizedIssues.length, 1);
  assert.deepEqual(normalizedIssues[0], {
    issue_type: "missing_dependency",
    severity: "high",
    description: "Task B does not depend on Task A.",
    recommendation: "Add the missing dependency.",
  });

  const repairedIssues = parsePlanningCritiqueIssues([
    {},
    {
      issue_type: "vague_task",
      description: "Task is too broad.",
    },
  ]);

  assert.equal(repairedIssues.length, 1);
  assert.equal(repairedIssues[0].issue_type, "vague_task");
  assert.equal(repairedIssues[0].severity, "low");
  assert.equal(repairedIssues[0].recommendation, "Review and refine the plan.");

  const textSummary = parsePlanningCritiqueSummary("Plan needs clearer dependencies.");
  assert.deepEqual(textSummary, {
    overall_score: null,
    summary: "Plan needs clearer dependencies.",
    strengths: [],
    issues: [],
    recommendation: null,
  });

  const structured = parsePlanningCritiqueSummary({
    overall_score: 0.72,
    summary: "Strong draft.",
    strengths: ["clear milestone ordering"],
    issues: [
      {
        issue_type: "estimate",
        severity: "medium",
        description: "Some estimates are optimistic.",
        recommendation: "Increase the durations for implementation tasks.",
      },
    ],
    recommendation: "Tighten estimates before execution.",
  });

  assert.equal(structured?.overall_score, 0.72);
  assert.equal(structured?.strengths?.length, 1);
  assert.equal(structured?.issues?.[0].issue_type, "estimate");
  assert.equal(structured?.recommendation, "Tighten estimates before execution.");
}

try {
  run();
  console.log("critique parser tests passed");
} catch (error) {
  console.error("critique parser tests failed");
  console.error(error);
  process.exitCode = 1;
}
