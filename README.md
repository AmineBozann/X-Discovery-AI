# 🚀 X-Discovery AI

### MCDA-Based Decision Support System for GitHub Repository Discovery

> Graduation Project | Computer Engineering | Flask | Python | GitHub API | Explainable AI


## MCDA-Based Decision Support System for Open-Source Software Discovery

X-Discovery AI is a decision support platform developed to assist software developers, researchers, and engineering teams in discovering high-quality and sustainable open-source projects on GitHub.

Unlike traditional repository search approaches that primarily rely on popularity indicators such as star counts, X-Discovery AI evaluates repositories using a multi-criteria framework that incorporates quality, activity, maintainability, and sustainability metrics.

The project was developed as a Computer Engineering Graduation Project.

---

## Problem Statement

GitHub hosts millions of open-source repositories. Although popularity metrics such as stars and forks provide useful insights, they do not necessarily reflect the long-term sustainability, maintenance quality, or engineering value of a project.

As a result, developers often struggle to identify repositories that are not only popular but also actively maintained and technically reliable.

X-Discovery AI addresses this challenge by introducing an explainable and data-driven repository evaluation framework.

---

## Objectives

* Evaluate GitHub repositories using multiple engineering criteria.
* Reduce dependency on popularity-based ranking mechanisms.
* Support data-driven repository selection decisions.
* Improve transparency through Explainable AI (XAI) principles.
* Identify sustainable and actively maintained projects.

---

## Methodology

The proposed system employs a Multi-Criteria Decision Analysis (MCDA) framework.

Repository evaluation incorporates:

* GitHub Stars
* Fork Count
* Watcher Count
* Open Issues
* Repository Activity
* Last Update Information
* Sustainability Indicators
* Engineering Quality Metrics

A Time-Sensitive Decay Mechanism is applied to penalize inactive repositories and prioritize actively maintained projects.

The final Engineering Score is generated through weighted aggregation and normalization procedures.

---

## Key Features

### Repository Discovery

Search repositories across GitHub using real-time GitHub REST API integration.

### Engineering Score

Generate a custom Engineering Score for each repository based on multiple evaluation criteria.

### Explainable Recommendations

Provide transparency regarding how repository rankings are calculated.

### Sustainability Analysis

Evaluate repository maintenance status and long-term viability.

### Ranking Dashboard

Display repositories according to calculated engineering scores.

---

## Technologies

* Python
* Flask
* SQLite
* GitHub REST API
* HTML
* CSS
* JavaScript
* Multi-Criteria Decision Analysis (MCDA)
* Explainable AI (XAI)

---

## System Architecture

1. Data Collection Layer
2. Data Processing Layer
3. Scoring Engine
4. Explainability Module
5. User Interface Layer

---

## Evaluation Results

The system was evaluated using manually constructed ground-truth datasets.

Performance metrics:

| Metric    | Value  |
| --------- | ------ |
| Precision | 100.0% |
| Recall    | 85.0%  |
| F1-Score  | 91.9%  |

The results demonstrate the effectiveness of the proposed repository evaluation framework.

---

## Screenshots

### Main Interface

(Add screenshot here)

### Repository Ranking Dashboard

(Add screenshot here)

### Engineering Score Visualization

(Add screenshot here)

---

## Future Work

Potential future improvements include:

* Machine Learning-based repository recommendation models
* Advanced repository quality metrics
* Repository similarity analysis
* Contributor behavior analytics
* Automated software quality assessment

---

## Academic Context

This project was developed as a graduation project in the Department of Computer Engineering.

The study investigates how Multi-Criteria Decision Analysis and Explainable AI concepts can be integrated into open-source software discovery and evaluation processes.

---
## 🔗 Live Demo

https://x-discovery-ai.onrender.com

## 📄 Academic Paper

Coming Soon

## 💻 Source Code

https://github.com/AmineBozann/X-Discovery-AI
## Author

Amine Bozan

Computer Engineer

GitHub: https://github.com/AmineBozann

LinkedIn: (www.linkedin.com/in/amine-bozan)

## Academic Paper

The academic paper associated with this project can be found in:

/ [text](../../bitirme/Elsevier_Rapor_Final10haziran.pdf)
