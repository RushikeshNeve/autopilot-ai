export function parsePlanningCritiqueIssues(value) {
  if (!Array.isArray(value)) {
    return [];
  }

  return value.flatMap((item) => {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      return [];
    }

    const record = item;
    const issueType = typeof record.issue_type === "string" ? record.issue_type : "";
    const severity = typeof record.severity === "string" ? record.severity : "low";
    const description = typeof record.description === "string" ? record.description : "";
    const recommendation = typeof record.recommendation === "string" ? record.recommendation : "";

    if (!issueType && !description && !recommendation) {
      return [];
    }

    return [
      {
        issue_type: issueType || "general",
        severity,
        description: description || "No description provided.",
        recommendation: recommendation || "Review and refine the plan.",
      },
    ];
  });
}

export function parsePlanningCritiqueSummary(value) {
  if (typeof value === "string" && value.trim().length > 0) {
    return {
      overall_score: null,
      summary: value,
      strengths: [],
      issues: [],
      recommendation: null,
    };
  }

  if (!value || typeof value !== "object" || Array.isArray(value)) {
    return null;
  }

  const record = value;
  return {
    overall_score: typeof record.overall_score === "number" ? record.overall_score : null,
    summary: typeof record.summary === "string" ? record.summary : null,
    strengths: Array.isArray(record.strengths) ? record.strengths.filter((item) => typeof item === "string") : [],
    issues: parsePlanningCritiqueIssues(record.issues),
    recommendation: typeof record.recommendation === "string" ? record.recommendation : null,
  };
}
