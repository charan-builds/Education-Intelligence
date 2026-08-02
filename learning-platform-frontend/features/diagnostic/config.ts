export const DIAGNOSTIC_TOTAL_QUESTIONS = 20;
export const DIAGNOSTIC_DURATION_SECONDS = 25 * 60;
export const DIAGNOSTIC_TRACK_ID = "python-track";
export const DIAGNOSTIC_TRACK_NAME = "Python Track";

export type DiagnosticStageSection = {
  level: string;
  title: string;
  topics: string[];
};

export const DIAGNOSTIC_SECTIONS: DiagnosticStageSection[] = [
  {
    level: "Level 0",
    title: "Python Core Test",
    topics: [
      "Variables",
      "Data Types",
      "Loops",
      "Functions",
      "Lists / Dicts",
      "Basic Problem Solving",
    ],
  },
  {
    level: "Level 1",
    title: "Data Analysis Foundation",
    topics: [
      "Understand Data",
      "Inspect Data",
      "Remove Irrelevant Columns",
      "Fix Data Issues",
      "Handle Missing Values",
      "Remove Duplicates",
      "Handle Outliers",
      "Transform Data",
      "Feature Creation",
      "Encode Categorical Data",
      "Scale Features",
      "Select Final Features",
    ],
  },
  {
    level: "Level 2",
    title: "Libraries Test",
    topics: ["NumPy", "Pandas", "Data Visualization (Matplotlib / Seaborn)"],
  },
  {
    level: "Level 3",
    title: "Machine Learning",
    topics: ["Regression", "Classification", "Model Evaluation", "Overfitting", "Feature Engineering"],
  },
];

export const STRICT_FLOW_STEPS = [
  "User Login",
  "Select Goal",
  "Select Learning Path",
  "Start Diagnostic Test",
] as const;

