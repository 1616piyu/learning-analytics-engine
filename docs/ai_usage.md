# AI Usage and Development Disclosure

## Project

Learning Analytics Engine - YottaFlex AI Candidate Project

## AI Tools Used

- ChatGPT: Primary AI assistant for project planning, technical guidance, debugging, documentation, and validation planning.
- Claude: Used to analyze the assignment requirements and overall design structure.

## How AI Assisted Development

AI assistance supported the understanding of assignment requirements, planning the data pipeline, considering database relationships, exploring validation and anomaly-detection approaches, troubleshooting issues, and organizing project documentation.

The prompt-history document is available at `prompt_history/prompts.md`. Prompts reconstructed from available project context are explicitly labelled as reconstructed rather than verbatim.

## Implementation Decisions and Trade-offs

The project uses synthetic learning-platform data, Python, SQLite, SQL, and Streamlit. The generator supports starter and full-scale configurations with a fixed seed.

The anomaly detector uses deterministic rules rather than a trained machine-learning classifier. This provides explainable checks for the implemented anomaly types. Ground-truth labels are maintained separately for evaluating injected synthetic cases.

## Review and Verification

The project includes automated tests covering implemented functionality, including data integrity, business metrics, reporting, learner risk, anomaly evaluation, and reproducibility.

The last recorded test result was 33 passing tests. This result should be confirmed by running the test suite again before submission.

## Known Limitations

- Activity events without an enrollment association do not identify a separate actor learner ID in the current schema.
- Timezone-boundary findings are candidates for review and are not necessarily confirmed data errors.
- Evaluation against injected synthetic anomalies does not establish performance on all possible real-world anomalies.
- Synthetic data and rule-based learner risk scores do not establish real-world predictive performance.

## Personal Responsibility

I am responsible for understanding and explaining the submitted implementation, design decisions, dependencies, validation results, and limitations. AI assistance does not replace verification of the submitted work.





