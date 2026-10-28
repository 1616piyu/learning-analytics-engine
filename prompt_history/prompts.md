# AI Prompt History

## Project

Learning Analytics Engine - YottaFlex AI Candidate Project

## Purpose

This document records the AI assistance used during the development of the Learning Analytics Engine. ChatGPT was my primary AI assistant. Claude was also used to analyze the assignment's design structure.

The prompts below summarize the project-related tasks based on the available conversation context. Where the original wording could not be recovered, the prompt is labelled as reconstructed rather than verbatim.

## 1. ChatGPT

### Prompt 1 - Assignment Understanding and Project Planning

- **Task:** Understand the assignment and plan the implementation.
- **Prompt:** Help me understand the Learning Analytics Engine assignment requirements. Break the problem into a practical implementation plan covering the business problem, data entities, relationships, synthetic data generation, validation, analytics, anomaly detection, exports, documentation, and testing. Prioritize the acceptance criteria and suggest a suitable project structure.
- **Record status:** Reconstructed from available project context.

### Prompt 2 - Database Schema and Relationships

- **Task:** Design the relational data model.
- **Prompt:** Help design a relational database schema for a learning analytics pipeline involving learners, courses, enrollments, content items, activity events, assessments, attempts, completion rules, cohorts, and course outcomes. Define primary keys, foreign keys, cardinality, optional relationships, lifecycle states, and appropriate integrity constraints.
- **Record status:** Reconstructed from available project context.

### Prompt 3 - Synthetic Dataset Generation

- **Task:** Plan deterministic synthetic data generation.
- **Prompt:** Help implement a reproducible synthetic data generator for the learning analytics project. Use a fixed random seed, deterministic IDs, configurable starter and full-scale modes, and realistic relationships between master data, enrollments, activity events, assessments, attempts, and course outcomes. Include inactive learners, repeated attempts, offline activity synchronization, and late-arriving events.
- **Record status:** Reconstructed from available project context.

### Prompt 4 - Data Validation and Anomaly Detection

- **Task:** Validate generated data and evaluate injected anomalies.
- **Prompt:** Help design validation checks for primary-key uniqueness, foreign-key integrity, allowed values, date ordering, completion rules, duplicate activity events, and data consistency. Explain how to inject labelled synthetic anomalies, keep ground-truth labels separate from input features, and evaluate anomaly detection results without treating uncertain timezone-boundary events as confirmed errors.
- **Record status:** Reconstructed from available project context.

### Prompt 5 - Analytics and Business Metrics

- **Task:** Define learning analytics metrics.
- **Prompt:** Help define clear business metrics for course participation, content usage, assessment performance, learner progress, completion rates, and cohort comparisons. Specify metric definitions, calculation logic, reporting windows, and how to derive metrics from the generated source data.
- **Record status:** Reconstructed from available project context.

### Prompt 6 - Testing and Reproducibility

- **Task:** Validate project behavior and deterministic generation.
- **Prompt:** Help plan tests for the learning analytics pipeline, including schema integrity, generated-data relationships, anomaly detection, business metrics, reporting, and reproducibility. Explain how to regenerate datasets using the same seed and compare row counts and checksums to verify deterministic outputs.
- **Record status:** Reconstructed from available project context.

### Prompt 7 - Documentation and Submission Readiness

- **Task:** Review project documentation and submission requirements.
- **Prompt:** Help organize the README and supporting documentation for a learning analytics project. Explain how to document setup, execution, data generation, schema, data dictionary, business rules, validation results, known limitations, and AI usage. Provide a final submission checklist for a public GitHub repository.
- **Record status:** Reconstructed from available project context.

## 2. Claude

### Prompt 1 - Assignment Design and Structure Analysis

- **Task:** Analyze the assignment requirements and understand its overall design structure.
- **Prompt:** Analyze the Learning Analytics Engine assignment and explain its overall design structure. Break down the business problem, required entities and their relationships, database schema, synthetic data generation pipeline, data validation, anomaly detection, analytics, and expected deliverables. Explain how the components should connect, identify the key requirements and acceptance criteria, and suggest a logical implementation structure.
- **Record status:** Reconstructed from my description of the task; not verified as the exact original prompt.

## 3. Completeness and Limitations

- **Primary AI tool:** ChatGPT.
- **Other AI tool:** Claude.
- **History coverage:** This document summarizes the main project-related AI tasks represented in the available project context.
- **Unavailable records:** The exact original wording of the prompts listed as reconstructed was not available when this document was prepared.
- **Accuracy:** The prompts above are reconstructed summaries, not a complete verbatim transcript of every interaction. They should not be interpreted as exact historical records.
- **Updates:** If additional original prompts are recovered from conversation histories, they should be added and labelled appropriately.

