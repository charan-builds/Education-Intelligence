from __future__ import annotations

from dataclasses import dataclass
from random import Random

from app.domain.models.tenant import TenantType
from app.domain.models.user import UserRole


@dataclass(frozen=True)
class TopicDescriptor:
    name: str
    description: str
    concept: str
    artifact: str
    pitfall: str
    metric: str


def _question_pack(topic: TopicDescriptor) -> list[dict]:
    return [
        {
            "difficulty": 1,
            "question_type": "multiple_choice",
            "question_text": f"What is the primary focus of {topic.name}?",
            "correct_answer": topic.concept,
            "accepted_answers": [topic.concept.lower()],
            "answer_options": [topic.concept, topic.artifact, topic.pitfall, topic.metric],
        },
        {
            "difficulty": 2,
            "question_type": "multiple_choice",
            "question_text": f"Which deliverable is most closely associated with {topic.name}?",
            "correct_answer": topic.artifact,
            "accepted_answers": [topic.artifact.lower()],
            "answer_options": [topic.metric, topic.artifact, topic.pitfall, topic.concept],
        },
        {
            "difficulty": 2,
            "question_type": "multiple_choice",
            "question_text": f"When working on {topic.name}, which mistake should a learner avoid first?",
            "correct_answer": topic.pitfall,
            "accepted_answers": [topic.pitfall.lower()],
            "answer_options": [topic.pitfall, topic.metric, topic.artifact, topic.concept],
        },
        {
            "difficulty": 3,
            "question_type": "multiple_choice",
            "question_text": f"Which signal best indicates progress in {topic.name}?",
            "correct_answer": topic.metric,
            "accepted_answers": [topic.metric.lower()],
            "answer_options": [topic.metric, topic.concept, topic.artifact, topic.pitfall],
        },
    ]


def _topic(name: str, description: str, concept: str, artifact: str, pitfall: str, metric: str) -> dict:
    descriptor = TopicDescriptor(
        name=name,
        description=description,
        concept=concept,
        artifact=artifact,
        pitfall=pitfall,
        metric=metric,
    )
    return {
        "name": descriptor.name,
        "description": descriptor.description,
        "questions": _question_pack(descriptor),
    }


def build_demo_tenants() -> list[dict]:
    return [
        {
            "name": "Demo University",
            "slug": "demo",
            "type": TenantType.college,
            "panel_users": [
                {"label": "Admin Panel", "email": "admin@demo.learnova.ai", "password": "admin123", "role": UserRole.admin},
                {"label": "Teacher Panel", "email": "teacher@demo.learnova.ai", "password": "Teacher123!", "role": UserRole.teacher},
                {"label": "Mentor Panel", "email": "mentor@demo.learnova.ai", "password": "Mentor123!", "role": UserRole.mentor},
            ],
            "students": [
                {"display_name": "Maya Chen", "email": "maya.chen@demo.learnova.ai", "password": "Student123!"},
                {"display_name": "Jordan Rivera", "email": "jordan.rivera@demo.learnova.ai", "password": "Student123!"},
                {"display_name": "Aisha Patel", "email": "aisha.patel@demo.learnova.ai", "password": "Student123!"},
            ],
            "topics": [
                _topic("Linear Algebra", "Vectors, matrices, and transformations for intelligent systems.", "matrix operations", "matrix decomposition notebook", "treating vectors as scalars", "projection accuracy"),
                _topic("Statistics", "Probability, distributions, and inference for machine learning.", "statistical inference", "confidence interval report", "ignoring variance", "estimation accuracy"),
                _topic("Python Foundations", "Core Python fluency for data workflows and backend tooling.", "control flow", "clean utility module", "copy-paste scripting", "runtime correctness"),
                _topic("SQL Analytics", "Query relational datasets and build repeatable analysis workflows.", "grouping and joins", "validated SQL workbook", "missing join conditions", "query accuracy"),
                _topic("Data Visualization", "Choose charts and tell clear stories from metrics.", "visual storytelling", "executive dashboard", "chart clutter", "insight clarity"),
                _topic("Machine Learning", "Train, evaluate, and compare predictive models.", "supervised learning", "baseline model experiment", "overfitting", "validation performance"),
                _topic("Feature Engineering", "Transform raw data into stronger model inputs.", "feature construction", "feature table", "leaking target data", "model lift"),
                _topic("Model Evaluation", "Measure model quality with the right business-aware metrics.", "evaluation metrics", "model scorecard", "optimizing one metric blindly", "holdout quality"),
                _topic("Experiment Design", "Plan A/B tests and causal measurements for product learning.", "controlled experimentation", "experiment brief", "sample-size neglect", "decision confidence"),
                _topic("Data Ethics", "Work with learner data responsibly and transparently.", "ethical tradeoffs", "risk checklist", "ignoring bias", "policy compliance"),
                _topic("APIs for AI", "Integrate model-backed services with application logic.", "API integration", "service contract", "unbounded payloads", "latency stability"),
                _topic("Prompt Design", "Shape reliable prompts for structured and learner-safe outputs.", "instruction design", "prompt template", "underspecified constraints", "response consistency"),
                _topic("RAG Basics", "Ground generation with retrieved knowledge and citations.", "retrieval augmentation", "context pipeline", "irrelevant retrieval", "answer grounding"),
                _topic("MLOps Foundations", "Operationalize training, deployment, and monitoring loops.", "deployment workflow", "release checklist", "training-production drift", "deployment reliability"),
                _topic("Learning Analytics", "Turn educational data into actionable signals.", "learner signal analysis", "insight memo", "tracking vanity metrics", "intervention precision"),
                _topic("Probability Modeling", "Represent uncertainty in a principled way.", "probabilistic reasoning", "probability worksheet", "confusing odds and probability", "forecast calibration"),
                _topic("Optimization Basics", "Improve objectives using gradients and iterative search.", "iterative optimization", "loss curve analysis", "overshooting minima", "convergence rate"),
                _topic("Capstone Communication", "Present technical recommendations to mixed audiences.", "decision communication", "capstone presentation", "jargon overload", "stakeholder alignment"),
            ],
            "goals": [
                {"name": "AI/ML Engineer", "description": "Build and ship machine learning systems responsibly."},
                {"name": "Data Analyst", "description": "Turn data into dashboards, experiments, and recommendations."},
                {"name": "Applied AI Researcher", "description": "Explore models, evaluation, and grounded AI workflows."},
            ],
            "communities": [
                {"name": "AI & Data Studio", "topic_name": "Machine Learning", "description": "Project critiques, diagnostic recovery, and portfolio support."},
                {"name": "Quant Foundations Lab", "topic_name": "Statistics", "description": "Probability, algebra, and model-evaluation study circles."},
            ],
        },
        {
            "name": "Acme Learning Co",
            "slug": "acme",
            "type": TenantType.company,
            "panel_users": [
                {"label": "Admin Panel", "email": "admin@acme.learnova.ai", "password": "admin123", "role": UserRole.admin},
                {"label": "Teacher Panel", "email": "teacher@acme.learnova.ai", "password": "Teacher123!", "role": UserRole.teacher},
                {"label": "Mentor Panel", "email": "mentor@acme.learnova.ai", "password": "Mentor123!", "role": UserRole.mentor},
            ],
            "students": [
                {"display_name": "Noah Brooks", "email": "noah.brooks@acme.learnova.ai", "password": "Student123!"},
                {"display_name": "Sofia Kim", "email": "sofia.kim@acme.learnova.ai", "password": "Student123!"},
                {"display_name": "Priya Shah", "email": "priya.shah@acme.learnova.ai", "password": "Student123!"},
            ],
            "topics": [
                _topic("Product Analytics", "Use events, funnels, and cohorts to understand product behavior.", "behavior analysis", "funnel dashboard", "confusing correlation with causation", "funnel conversion"),
                _topic("Experiment Design", "Run controlled experiments with strong decision hygiene.", "causal testing", "A/B test plan", "peeking too early", "experiment confidence"),
                _topic("Retention Analytics", "Measure activation, churn, and long-term engagement.", "retention measurement", "cohort retention report", "mixing cohorts", "retention lift"),
                _topic("North Star Metrics", "Align teams around meaningful product outcomes.", "value-centric metrics", "metric tree", "optimizing proxy metrics", "north star movement"),
                _topic("Dashboard Design", "Design decision-ready dashboards for product teams.", "dashboard architecture", "ops dashboard", "metric overload", "decision speed"),
                _topic("User Research Synthesis", "Turn interviews into clear themes and product hypotheses.", "qualitative synthesis", "insight synthesis board", "overgeneralizing anecdotes", "theme confidence"),
                _topic("SQL for Product", "Write reliable queries for experimentation and lifecycle analysis.", "analytical SQL", "query library", "duplicate counting", "query trust"),
                _topic("Feature Flag Operations", "Roll out changes safely with measurement hooks.", "controlled rollout", "release plan", "global blast radius", "rollback readiness"),
                _topic("Segmentation Strategy", "Group users in ways that drive better decisions.", "user segmentation", "segment definition sheet", "arbitrary segment splits", "segment usefulness"),
                _topic("Monetization Analysis", "Understand pricing, conversion, and expansion signals.", "revenue analysis", "pricing readout", "blending plan types", "revenue efficiency"),
                _topic("Customer Journey Mapping", "Model the sequence from awareness to retention.", "journey analysis", "journey map", "missing friction points", "handoff clarity"),
                _topic("Narrative Reporting", "Communicate findings with structure and confidence.", "story framing", "weekly business review", "burying the insight", "executive clarity"),
                _topic("Forecasting Basics", "Project demand and business outcomes with uncertainty.", "trend forecasting", "forecast workbook", "false precision", "forecast error"),
                _topic("Attribution Models", "Estimate which channels drive impact.", "channel attribution", "attribution memo", "crediting last touch only", "channel confidence"),
                _topic("Behavioral Cohorts", "Compare lifecycle patterns across user groups.", "cohort comparison", "cohort matrix", "time-window mismatch", "cohort stability"),
                _topic("Lifecycle Messaging", "Improve reactivation and activation through targeted communications.", "message optimization", "campaign brief", "untimed outreach", "reactivation rate"),
                _topic("Operational Metrics", "Track service reliability and team performance with context.", "operational measurement", "health scorecard", "vanity uptime reporting", "incident response time"),
                _topic("Insight Prioritization", "Decide which findings deserve action first.", "impact prioritization", "decision backlog", "equal-weighting all findings", "decision throughput"),
            ],
            "goals": [
                {"name": "Product Analyst", "description": "Analyze product behavior, experiments, and retention patterns."},
                {"name": "Growth Analyst", "description": "Drive activation, retention, and monetization decisions."},
                {"name": "Analytics Manager", "description": "Lead metric strategy and stakeholder storytelling."},
            ],
            "communities": [
                {"name": "Growth Council", "topic_name": "Retention Analytics", "description": "Retention experiments, messaging reviews, and forecast discussions."},
                {"name": "Product Signals Hub", "topic_name": "Product Analytics", "description": "Funnels, dashboards, and weekly business review support."},
            ],
        },
        {
            "name": "Northwind Academy",
            "slug": "northwind",
            "type": TenantType.school,
            "panel_users": [
                {"label": "Admin Panel", "email": "admin@northwind.learnova.ai", "password": "admin123", "role": UserRole.admin},
                {"label": "Teacher Panel", "email": "teacher@northwind.learnova.ai", "password": "Teacher123!", "role": UserRole.teacher},
                {"label": "Mentor Panel", "email": "mentor@northwind.learnova.ai", "password": "Mentor123!", "role": UserRole.mentor},
            ],
            "students": [
                {"display_name": "Ethan Cole", "email": "ethan.cole@northwind.learnova.ai", "password": "Student123!"},
                {"display_name": "Lina Gomez", "email": "lina.gomez@northwind.learnova.ai", "password": "Student123!"},
                {"display_name": "Marcus Reed", "email": "marcus.reed@northwind.learnova.ai", "password": "Student123!"},
            ],
            "topics": [
                _topic("Reading Comprehension", "Understand, summarize, and compare written passages.", "main idea analysis", "passage summary", "missing textual evidence", "summary accuracy"),
                _topic("Basic Algebra", "Work with variables, equations, and simple functions.", "equation solving", "worked equation set", "sign errors", "problem accuracy"),
                _topic("Geometry Foundations", "Reason with shapes, area, and spatial relationships.", "spatial reasoning", "geometry notes", "formula confusion", "solution accuracy"),
                _topic("Applied Fractions", "Use fractions in practical contexts and comparisons.", "fraction operations", "fraction worksheet", "common denominator mistakes", "calculation accuracy"),
                _topic("Writing Structure", "Organize clear paragraphs, transitions, and arguments.", "written organization", "structured paragraph draft", "weak transitions", "writing clarity"),
                _topic("Scientific Reasoning", "Interpret evidence and connect claims to data.", "evidence-based reasoning", "lab explanation", "unsupported claims", "claim accuracy"),
                _topic("Study Planning", "Build repeatable routines and realistic weekly plans.", "study organization", "study calendar", "overcommitting sessions", "plan consistency"),
                _topic("Digital Literacy", "Use online tools, research workflows, and safe practices.", "digital workflow", "research checklist", "unverified sources", "task completion"),
                _topic("Presentation Skills", "Share ideas clearly in spoken and visual form.", "clear presentation", "short presentation deck", "reading slides verbatim", "audience engagement"),
                _topic("Critical Thinking", "Evaluate arguments and evidence with care.", "argument evaluation", "claim comparison sheet", "jumping to conclusions", "reasoning quality"),
                _topic("Time Management", "Allocate energy across goals, deadlines, and review cycles.", "time budgeting", "weekly schedule", "reactive planning", "on-time completion"),
                _topic("Note Taking Systems", "Capture knowledge in ways that improve recall.", "knowledge capture", "structured notes", "transcribing without synthesis", "recall rate"),
                _topic("Vocabulary Growth", "Build precise language for reading and writing.", "context vocabulary", "vocabulary tracker", "memorizing without usage", "word retention"),
                _topic("Data Literacy", "Read basic charts, summaries, and quantitative claims.", "chart interpretation", "data reflection journal", "misreading scales", "interpretation accuracy"),
                _topic("Goal Setting", "Define measurable and motivating learning targets.", "goal framing", "goal tracker", "vague objectives", "goal completion"),
                _topic("Revision Strategy", "Improve work through deliberate review cycles.", "iterative revision", "revision checklist", "editing too late", "improvement rate"),
                _topic("Independent Research", "Gather and evaluate sources for self-directed learning.", "source evaluation", "research notes", "trusting weak sources", "source quality"),
                _topic("Reflection Practice", "Turn recent learning into better future habits.", "self-reflection", "reflection journal", "generic takeaways", "habit improvement"),
            ],
            "goals": [
                {"name": "STEM Foundations", "description": "Strengthen core quantitative and scientific reasoning skills."},
                {"name": "Academic Momentum", "description": "Build durable learning habits and self-management skills."},
                {"name": "Communication Builder", "description": "Improve writing, reading, and presentation confidence."},
            ],
            "communities": [
                {"name": "Study Hall", "topic_name": "Study Planning", "description": "Peer accountability, planning templates, and study streak encouragement."},
                {"name": "Foundations Forum", "topic_name": "Reading Comprehension", "description": "Reading, writing, and math support for school learners."},
            ],
        },
    ]


def build_demo_personal_workspaces() -> list[dict]:
    return [
        {
            "name": "Ava Martinez Workspace",
            "slug": "ava-martinez",
            "type": TenantType.personal,
            "learners": [
                {
                    "display_name": "Ava Martinez",
                    "email": "ava.martinez@workspace.learnova.ai",
                    "password": "Student123!",
                    "role": UserRole.independent_learner,
                    "organization_name": "Independent learner workspace",
                }
            ],
            "topics": [
                _topic("Python Foundations", "Core Python fluency for automation and data workflows.", "control flow", "clean utility module", "copy-paste scripting", "runtime correctness"),
                _topic("SQL Analytics", "Query relational datasets and validate decisions with data.", "grouping and joins", "validated SQL workbook", "missing join conditions", "query accuracy"),
                _topic("Data Visualization", "Turn metrics into clear dashboards and narratives.", "visual storytelling", "executive dashboard", "chart clutter", "insight clarity"),
                _topic("APIs for AI", "Integrate model-backed services into product experiences safely.", "API integration", "service contract", "unbounded payloads", "latency stability"),
                _topic("Prompt Design", "Create reliable prompts for structured and useful outputs.", "instruction design", "prompt template", "underspecified constraints", "response consistency"),
                _topic("RAG Basics", "Ground answers in retrieved knowledge and source-aware workflows.", "retrieval augmentation", "context pipeline", "irrelevant retrieval", "answer grounding"),
                _topic("Learning Analytics", "Turn learning signals into next-step decisions.", "learner signal analysis", "insight memo", "tracking vanity metrics", "intervention precision"),
                _topic("Capstone Communication", "Present technical recommendations to mixed audiences.", "decision communication", "capstone presentation", "jargon overload", "stakeholder alignment"),
            ],
            "goals": [
                {"name": "AI Product Builder", "description": "Build grounded AI experiences and communicate the outcome clearly."},
                {"name": "Career Switch to Data", "description": "Build a portfolio around SQL, dashboards, and analytical reasoning."},
                {"name": "Independent Learner Operating System", "description": "Develop repeatable self-directed learning habits and review loops."},
            ],
            "communities": [
                {"name": "Solo Builder Circle", "topic_name": "APIs for AI", "description": "Feedback and accountability for self-directed AI product work."},
                {"name": "Momentum Reviews", "topic_name": "Learning Analytics", "description": "Weekly reflection, planning, and roadmap review rituals."},
            ],
        },
        {
            "name": "Leo Kim Workspace",
            "slug": "leo-kim",
            "type": TenantType.personal,
            "learners": [
                {
                    "display_name": "Leo Kim",
                    "email": "leo.kim@workspace.learnova.ai",
                    "password": "Student123!",
                    "role": UserRole.independent_learner,
                    "organization_name": "Independent learner workspace",
                }
            ],
            "topics": [
                _topic("Reading Comprehension", "Understand, summarize, and compare written passages.", "main idea analysis", "passage summary", "missing textual evidence", "summary accuracy"),
                _topic("Critical Thinking", "Evaluate arguments and evidence with care.", "argument evaluation", "claim comparison sheet", "jumping to conclusions", "reasoning quality"),
                _topic("Digital Literacy", "Use online tools, research workflows, and safe practices.", "digital workflow", "research checklist", "unverified sources", "task completion"),
                _topic("Study Planning", "Build repeatable routines and realistic weekly plans.", "study organization", "study calendar", "overcommitting sessions", "plan consistency"),
                _topic("Goal Setting", "Define measurable and motivating learning targets.", "goal framing", "goal tracker", "vague objectives", "goal completion"),
                _topic("Independent Research", "Gather and evaluate sources for self-directed learning.", "source evaluation", "research notes", "trusting weak sources", "source quality"),
                _topic("Reflection Practice", "Turn recent learning into better future habits.", "self-reflection", "reflection journal", "generic takeaways", "habit improvement"),
                _topic("Revision Strategy", "Improve work through deliberate review cycles.", "iterative revision", "revision checklist", "editing too late", "improvement rate"),
            ],
            "goals": [
                {"name": "Self-Directed Foundations", "description": "Build core reading, research, and planning habits for independent growth."},
                {"name": "Communication Confidence", "description": "Strengthen writing, reflection, and presentation routines."},
                {"name": "Learning Habit Reset", "description": "Recover consistency with a simple roadmap and regular reviews."},
            ],
            "communities": [
                {"name": "Independent Research Circle", "topic_name": "Independent Research", "description": "Source review, reflection prompts, and progress accountability."},
                {"name": "Habit Builders", "topic_name": "Study Planning", "description": "Planning templates, streak support, and practical next-step coaching."},
            ],
        },
    ]


def build_goal_topic_names(topic_names: list[str], goal_count: int, *, rng: Random) -> list[list[str]]:
    packs: list[list[str]] = []
    stride = max(5, len(topic_names) // max(goal_count, 1))
    for goal_index in range(goal_count):
        start = (goal_index * stride) % len(topic_names)
        names = topic_names[start : start + 7]
        if len(names) < 7:
            names.extend(topic_names[: 7 - len(names)])
        packs.append(sorted(set(names)))
    rng.shuffle(packs)
    return packs
