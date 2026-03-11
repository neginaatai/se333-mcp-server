# SE333 Final Project — AI Test Coverage Agent

An autonomous AI agent that uses **Model Context Protocol (MCP)** to automatically generate, execute, and iterate on JUnit tests to maximize code coverage — and detect flaky tests for test suite reliability.

**Student:** Negina Atai  
**Course:** SE333 — Software Testing  
**University:** DePaul University  
**Submitted:** March 2026

---

## Project Overview

This project builds an intelligent testing agent powered by GitHub Copilot (GPT) and a custom MCP server. The agent autonomously:

1. Analyzes a Java Spring Boot project for coverage gaps using JaCoCo
2. Generates targeted JUnit tests to cover uncovered branches and methods
3. Iterates until coverage exceeds 95%
4. Detects flaky tests by running the test suite multiple times and flagging inconsistent results

### Results on Spring PetClinic

| Metric | Before | After |
|--------|--------|-------|
| Instructions | 90.58% | 99.27% |
| Branches | 84.09% | 93.18% |
| Lines | 94.26% | 98.97% |
| Methods | 89.81% | 98.11% |
| Classes | 95.45% | 100.00% |

---

## Architecture

```
GitHub Copilot (VS Code)
        ↓  MCP protocol
FastMCP Server (main.py) — http://127.0.0.1:8000/sse
        ↓  Python
Maven · JaCoCo · Git · File System
```

### MCP Tools Exposed

| Tool | Description |
|------|-------------|
| `run_maven_tests` | Runs `mvn package` to execute tests and generate JaCoCo report |
| `parse_jacoco` | Parses JaCoCo XML and returns per-class coverage summary |
| `write_test_file` | Writes a JUnit test file to the project |
| `git_commit` | Stages all changes and commits to git |
| `create_branch` | Creates and checks out a new git branch |
| `git_push` | Pushes branch to remote origin |
| `track_coverage_trend` | Logs coverage percentage with timestamp to JSON |
| `detect_flaky_tests` | Runs test suite N times and flags inconsistent tests |

---

## Project Structure

```
se333-mcp-server/          ← MCP server (this repo)
├── main.py                ← FastMCP server with all tools
├── pyproject.toml
├── uv.lock
└── .venv/

se333-demo/spring-petclinic/   ← Target Java project
├── .github/
│   └── prompts/
│       └── tester.prompt.md   ← Agent instructions
├── src/test/java/...          ← AI-generated test files
├── coverage-trend.json        ← Coverage history log
└── flaky-test-report.json     ← Flaky test detection report
```

---

## Setup Instructions

### Prerequisites

- Python 3.11+
- Java 17+
- Maven 3.9+
- VS Code with GitHub Copilot extension
- `uv` package manager

### 1. Clone the MCP Server

```bash
git clone https://github.com/neginaatai/se333-mcp-server
cd se333-mcp-server
```

### 2. Install Dependencies

```bash
uv venv
source .venv/bin/activate
uv pip install fastmcp
```

### 3. Start the MCP Server

```bash
python main.py
# Server starts at http://127.0.0.1:8000/sse
```

### 4. Connect VS Code to MCP Server

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "se333-mcp-server": {
      "type": "sse",
      "url": "http://127.0.0.1:8000/sse"
    }
  }
}
```

### 5. Clone the Target Project

```bash
git clone https://github.com/neginaatai/spring-petclinic
cd spring-petclinic
```

### 6. Run the Agent

In VS Code chat, type:

```
#file:.github/prompts/tester.prompt.md
```

The agent will autonomously run, generate tests, and improve coverage.

---

## Agent Prompt

The agent is driven by `.github/prompts/tester.prompt.md` which instructs GitHub Copilot to:

- Use the MCP tools listed above
- Iteratively improve coverage until it exceeds 95%
- Detect flaky tests after coverage goal is reached
- Commit all changes with descriptive messages

---

## Phase 5 — Creative Extension: Flaky Test Detector

The `detect_flaky_tests` MCP tool extends the agent beyond coverage improvement by validating **test suite reliability**.

**How it works:**
1. Runs `mvn surefire:test` N times (default: 5) with random test ordering
2. Parses surefire XML reports after each run
3. Tracks PASS/FAIL per test across all runs
4. Flags any test with inconsistent results as flaky
5. Diagnoses likely cause (timing, order dependency, shared state)
6. Saves full report to `flaky-test-report.json`
7. Automatically generates `flaky-test-report.html` — a self-contained visual report, open in any browser

**Results on Spring PetClinic:**
- 70 tests analyzed across 5 runs
- 0 flaky tests detected — confirming the AI-generated tests are stable and reliable

---

## Test Files Added by Agent

```
src/test/java/org/springframework/samples/petclinic/owner/
├── PetControllerTest.java
├── PetControllerMoreTest.java
├── VisitControllerTest.java
├── OwnerControllerMoreTest.java
└── system/CacheConfigurationTest.java
```

---

## GitHub Repository

- **MCP Server:** https://github.com/neginaatai/se333-mcp-server
- **Target Project (fork):** https://github.com/neginaatai/spring-petclinic
- **Pull Request:** https://github.com/neginaatai/spring-petclinic/pull/1

---

## Technologies Used

- **Python** — MCP server implementation
- **FastMCP** — MCP server framework
- **Java / Spring Boot** — Target project under test
- **JUnit 5** — Test framework
- **JaCoCo** — Code coverage tool
- **Maven** — Build and test runner
- **GitHub Copilot (GPT)** — AI agent
- **Model Context Protocol (MCP)** — Agent-tool communication protocol
