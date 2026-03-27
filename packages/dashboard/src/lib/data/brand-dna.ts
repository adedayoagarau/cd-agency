export const voicePatterns = [
  { id: 1, dimension: "Formality", value: "Professional casual", confidence: 0.92, source: "Brand Guide v3.pdf" },
  { id: 2, dimension: "Sentence length", value: "Short to medium (8-18 words)", confidence: 0.88, source: "Marketing site copy" },
  { id: 3, dimension: "Person", value: "Second person (you/your)", confidence: 0.95, source: "Brand Guide v3.pdf" },
  { id: 4, dimension: "Active voice", value: "Preferred (85%+ target)", confidence: 0.91, source: "Style analysis" },
  { id: 5, dimension: "Contractions", value: "Yes — makes copy feel human", confidence: 0.87, source: "Brand Guide v3.pdf" },
  { id: 6, dimension: "Humor", value: "Light, never sarcastic", confidence: 0.79, source: "Content audit Q2" },
  { id: 7, dimension: "Technical language", value: "Explain jargon on first use", confidence: 0.84, source: "Help docs analysis" },
];

export const terminology = [
  { id: 1, term: "Sign up", preferred: "Sign up", avoid: "Register, Create account, Join", severity: "required" as const },
  { id: 2, term: "Log in", preferred: "Log in (two words)", avoid: "Login, Sign in, Signin", severity: "required" as const },
  { id: 3, term: "Workspace", preferred: "Workspace", avoid: "Project, Account, Environment", severity: "required" as const },
  { id: 4, term: "Team member", preferred: "Team member", avoid: "User, Collaborator, Seat", severity: "preferred" as const },
  { id: 5, term: "Content", preferred: "Content", avoid: "Copy, Text, String", severity: "preferred" as const },
  { id: 6, term: "Agent", preferred: "Agent", avoid: "Bot, AI, Tool, Assistant", severity: "required" as const },
  { id: 7, term: "Run", preferred: "Run (an agent)", avoid: "Execute, Trigger, Launch", severity: "preferred" as const },
  { id: 8, term: "Brand DNA", preferred: "Brand DNA", avoid: "Brand guidelines, Voice settings, Style config", severity: "required" as const },
];

export const styleRules = [
  { id: 1, rule: "Always use sentence case for headings", severity: "required" as const, category: "Capitalization" },
  { id: 2, rule: "No exclamation marks in error messages", severity: "required" as const, category: "Punctuation" },
  { id: 3, rule: "Use numerals for numbers 10 and above, words for 1-9", severity: "preferred" as const, category: "Numbers" },
  { id: 4, rule: "Oxford comma in lists of 3+", severity: "required" as const, category: "Punctuation" },
  { id: 5, rule: "Maximum 25 words per sentence in UI copy", severity: "preferred" as const, category: "Readability" },
  { id: 6, rule: "Lead with the benefit, not the feature", severity: "preferred" as const, category: "Messaging" },
  { id: 7, rule: "Use 'we' sparingly — focus on 'you'", severity: "preferred" as const, category: "Tone" },
];

export const sources = [
  { id: 1, filename: "Brand Guide v3.pdf", type: "PDF", extractedDate: "Mar 15, 2026", patternsExtracted: 23 },
  { id: 2, filename: "Marketing site copy", type: "URL", extractedDate: "Mar 10, 2026", patternsExtracted: 12 },
  { id: 3, filename: "Help docs analysis", type: "URL", extractedDate: "Feb 28, 2026", patternsExtracted: 8 },
  { id: 4, filename: "Content audit Q2.docx", type: "Doc", extractedDate: "Feb 15, 2026", patternsExtracted: 15 },
  { id: 5, filename: "Style analysis", type: "Doc", extractedDate: "Jan 20, 2026", patternsExtracted: 6 },
];
