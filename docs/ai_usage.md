\# AI Usage and Development Disclosure



\## Project



Learning Analytics Engine — YottaFlex AI Candidate Project



\## AI tools used



ChatGpt, Claude



\## How AI assisted development



AI assistance was used for technical guidance, reviewing implementation choices, troubleshooting errors, improving documentation, and planning validation steps.



The prompt history is maintained separately in `prompt\_history/prompts.md`.



\## Areas personally reviewed and validated



The project was reviewed against the stated business workflow, entities, database relationships, data-generation requirements, anomaly scenarios, and acceptance criteria.



Validation included running the automated test suite, reviewing the database schema, inspecting anomaly injection and evaluation logic, and checking the repository state.



The latest recorded test run completed with 33 passing tests.



\## Design decisions and trade-offs



The project uses synthetic data, Python, SQLite, SQL, and Streamlit. The generator supports starter and full-scale configurations with a fixed seed.



The anomaly detector uses deterministic rules rather than a trained machine-learning classifier. This makes the implemented checks explainable and allows the known injected cases to be evaluated separately using ground-truth labels.



\## Known limitations



\- Activity events without an enrollment association do not identify a separate actor learner ID in the current schema.

\- Timezone-boundary findings require review and do not necessarily indicate confirmed data errors.

\- Evaluation on injected synthetic cases does not establish performance on every possible real-world anomaly.

\- Any remaining gaps in requirements or documentation should be stated explicitly here.



\## Verification



The latest recorded command was `python -m pytest -q`, which completed with 33 passing tests.



The project README documents setup, execution, data generation, anomaly evaluation, exports, and reproducibility checks.



\## Personal responsibility



I am responsible for understanding and explaining the project's implementation, design decisions, limitations, and test results. AI assistance does not replace verification of the submitted code.



