from fastmcp import FastMCP
import xml.etree.ElementTree as ET
import subprocess
import os
import json
import datetime

mcp = FastMCP("SE333")


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


@mcp.tool
def parse_jacoco(xml_path: str) -> str:
    """Parse JaCoCo XML report and return coverage summary"""
    tree = ET.parse(xml_path)
    root = tree.getroot()
    results = []
    for package in root.findall('package'):
        for cls in package.findall('class'):
            name = cls.get('name')
            for counter in cls.findall('counter'):
                if counter.get('type') == 'LINE':
                    missed = int(counter.get('missed'))
                    covered = int(counter.get('covered'))
                    total = missed + covered
                    pct = round((covered / total) * 100, 1) if total > 0 else 0
                    results.append(f"{name}: {pct}% ({covered}/{total} lines)")
    return "\n".join(results)


@mcp.tool
def run_maven_tests(project_path: str) -> str:
    """Run mvn package to execute tests and generate JaCoCo report"""
    result = subprocess.run(
        ["mvn", "package", "-DskipTests=false"],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.stdout[-3000:]


@mcp.tool
def write_test_file(file_path: str, content: str) -> str:
    """Write a Java test file to the project"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w') as f:
        f.write(content)
    return f"Written to {file_path}"


@mcp.tool
def git_commit(project_path: str, message: str) -> str:
    """Stage all changes and commit to git"""
    subprocess.run(["git", "add", "."], cwd=project_path)
    result = subprocess.run(
        ["git", "commit", "-m", message],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr


@mcp.tool
def create_branch(project_path: str, branch_name: str) -> str:
    """Create and checkout a new git branch"""
    result = subprocess.run(
        ["git", "checkout", "-b", branch_name],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr


@mcp.tool
def git_push(project_path: str, branch_name: str) -> str:
    """Push branch to remote origin"""
    result = subprocess.run(
        ["git", "push", "-u", "origin", branch_name],
        cwd=project_path,
        capture_output=True,
        text=True
    )
    return result.stdout + result.stderr


@mcp.tool
def track_coverage_trend(project_path: str, coverage_pct: float) -> str:
    """Log coverage percentage with timestamp to track improvement trend"""
    log_file = f"{project_path}/coverage-trend.json"
    try:
        with open(log_file) as f:
            history = json.load(f)
    except:
        history = []
    history.append({
        "timestamp": datetime.datetime.now().isoformat(),
        "coverage": coverage_pct
    })
    with open(log_file, "w") as f:
        json.dump(history, f, indent=2)
    return f"Logged {coverage_pct}% coverage. Total runs: {len(history)}"


@mcp.tool
def detect_flaky_tests(project_path: str, runs: int = 5) -> str:
    """
    Run the Maven test suite multiple times and detect flaky tests.
    A flaky test is one that does not produce a consistent pass/fail
    result across all runs. Returns a JSON report listing each flaky
    test with its pass rate and a suggested cause.
    """
    # track results per test: { "ClassName#methodName": [True, False, ...] }
    test_results: dict[str, list[bool]] = {}

    for run_index in range(runs):
        # Run tests with a random seed so ordering can vary between runs
        result = subprocess.run(
            [
                "mvn", "surefire:test",
                "-DskipTests=false",
                f"-Dsurefire.runOrder=random",
                f"-Dsurefire.randomizeOrder=true",
            ],
            cwd=project_path,
            capture_output=True,
            text=True
        )

        # Parse surefire XML reports
        surefire_dir = os.path.join(project_path, "target", "surefire-reports")
        if not os.path.exists(surefire_dir):
            return "No surefire-reports directory found. Run mvn test at least once first."

        for report_file in os.listdir(surefire_dir):
            if not report_file.endswith(".xml") or not report_file.startswith("TEST-"):
                continue

            report_path = os.path.join(surefire_dir, report_file)
            try:
                tree = ET.parse(report_path)
                root = tree.getroot()
                classname = root.get("name", "Unknown")

                for testcase in root.findall("testcase"):
                    method = testcase.get("name", "unknown")
                    test_id = f"{classname}#{method}"

                    # A test is failed if it has a <failure> or <error> child
                    failed = (
                        testcase.find("failure") is not None
                        or testcase.find("error") is not None
                    )
                    passed = not failed

                    if test_id not in test_results:
                        test_results[test_id] = []
                    test_results[test_id].append(passed)

            except ET.ParseError:
                continue

    # Identify flaky tests: results are not all True or all False
    flaky = []
    stable_pass = []
    stable_fail = []

    for test_id, outcomes in test_results.items():
        pass_count = sum(outcomes)
        total = len(outcomes)
        pass_rate = round((pass_count / total) * 100, 1)

        if pass_count == total:
            stable_pass.append(test_id)
        elif pass_count == 0:
            stable_fail.append(test_id)
        else:
            # Guess likely cause based on pass rate pattern
            if pass_rate >= 80:
                likely_cause = "Timing sensitivity or race condition (passes most of the time)"
            elif pass_rate <= 20:
                likely_cause = "Order dependency — likely relies on state set by another test"
            else:
                likely_cause = "Non-deterministic behavior — possible shared mutable state or random data"

            flaky.append({
                "test": test_id,
                "pass_rate": f"{pass_count}/{total} runs ({pass_rate}%)",
                "likely_cause": likely_cause,
                "outcomes": ["PASS" if o else "FAIL" for o in outcomes],
            })

    report = {
        "summary": {
            "total_tests": len(test_results),
            "flaky_count": len(flaky),
            "stable_passing": len(stable_pass),
            "stable_failing": len(stable_fail),
            "runs_performed": runs,
        },
        "flaky_tests": flaky,
        "stable_failing_tests": stable_fail,
    }

    # Save report to file
    report_path = os.path.join(project_path, "flaky-test-report.json")
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)

    # Return a human-readable summary
    lines = [
        f"=== Flaky Test Detection Report ===",
        f"Runs performed : {runs}",
        f"Total tests    : {report['summary']['total_tests']}",
        f"Flaky tests    : {len(flaky)}",
        f"Stable passing : {len(stable_pass)}",
        f"Stable failing : {len(stable_fail)}",
        f"Full report saved to: {report_path}",
        "",
    ]

    if flaky:
        lines.append("FLAKY TESTS:")
        for ft in flaky:
            lines.append(f"  • {ft['test']}")
            lines.append(f"    Pass rate  : {ft['pass_rate']}")
            lines.append(f"    Likely cause: {ft['likely_cause']}")
            lines.append(f"    Outcomes   : {' → '.join(ft['outcomes'])}")
            lines.append("")
    else:
        lines.append("No flaky tests detected across all runs.")

    if stable_fail:
        lines.append("CONSISTENTLY FAILING TESTS (not flaky, just broken):")
        for t in stable_fail:
            lines.append(f"  • {t}")

    return "\n".join(lines)


if __name__ == "__main__":
    mcp.run(transport="sse")