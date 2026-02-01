import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import httpx
from application_sdk.activities import ActivitiesInterface
from application_sdk.observability.logger_adaptor import get_logger
from temporalio import activity

logger = get_logger(__name__)
activity.logger = logger

# WCAG 2.1 tag mappings for axe-core
WCAG_TAGS = {
    "A": ["wcag2a", "wcag21a"],
    "AA": ["wcag2a", "wcag2aa", "wcag21a", "wcag21aa"],
    "AAA": ["wcag2a", "wcag2aa", "wcag2aaa", "wcag21a", "wcag21aa", "wcag21aaa"],
}


class AccessibilityAuditActivities(ActivitiesInterface):
    @activity.defn
    async def run_axe_audit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run accessibility audit using axe-core via Playwright.

        Args:
            params: Dictionary containing:
                - url: The URL to audit
                - wcag_level: WCAG conformance level (A, AA, or AAA)

        Returns:
            Dictionary containing axe-core audit results
        """
        url = params.get("url", "")
        wcag_level = params.get("wcag_level", "AA")

        logger.info(f"Running axe-core audit for {url} at WCAG {wcag_level} level")

        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed. Please install playwright.")
            return {
                "success": False,
                "error": "Playwright not installed",
                "violations": [],
                "passes": [],
            }

        results = {
            "success": False,
            "url": url,
            "wcag_level": wcag_level,
            "violations": [],
            "passes": [],
            "incomplete": [],
            "inapplicable": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context()
                page = await context.new_page()

                # Navigate to the target URL
                await page.goto(url, wait_until="networkidle", timeout=60000)

                # Inject axe-core
                await page.add_script_tag(
                    url="https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.8.3/axe.min.js"
                )

                # Configure and run axe-core
                wcag_tags = WCAG_TAGS.get(wcag_level, WCAG_TAGS["AA"])

                axe_results = await page.evaluate(
                    f"""
                    async () => {{
                        const results = await axe.run(document, {{
                            runOnly: {{
                                type: 'tag',
                                values: {json.dumps(wcag_tags)}
                            }}
                        }});
                        return results;
                    }}
                """
                )

                await browser.close()

                # Process results
                results["success"] = True
                results["violations"] = _process_axe_violations(
                    axe_results.get("violations", [])
                )
                results["passes"] = len(axe_results.get("passes", []))
                results["incomplete"] = len(axe_results.get("incomplete", []))
                results["inapplicable"] = len(axe_results.get("inapplicable", []))
                results["summary"] = {
                    "total_violations": len(results["violations"]),
                    "critical": sum(
                        1 for v in results["violations"] if v["impact"] == "critical"
                    ),
                    "serious": sum(
                        1 for v in results["violations"] if v["impact"] == "serious"
                    ),
                    "moderate": sum(
                        1 for v in results["violations"] if v["impact"] == "moderate"
                    ),
                    "minor": sum(
                        1 for v in results["violations"] if v["impact"] == "minor"
                    ),
                }

                logger.info(
                    f"Axe audit completed: {results['summary']['total_violations']} violations found"
                )

        except Exception as e:
            logger.error(f"Error running axe-core audit: {str(e)}")
            results["error"] = str(e)

        return results

    @activity.defn
    async def run_wave_audit(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Run accessibility audit using WAVE API.

        Args:
            params: Dictionary containing:
                - url: The URL to audit
                - api_key: WAVE API key

        Returns:
            Dictionary containing WAVE audit results
        """
        url = params.get("url", "")
        api_key = params.get("api_key", "")

        logger.info(f"Running WAVE audit for {url}")

        results = {
            "success": False,
            "url": url,
            "errors": [],
            "alerts": [],
            "features": [],
            "structure": [],
            "aria": [],
            "contrast": [],
            "timestamp": datetime.utcnow().isoformat(),
        }

        if not api_key:
            logger.warning("No WAVE API key provided, skipping WAVE audit")
            results["error"] = "No API key provided"
            return results

        try:
            # WAVE API endpoint
            wave_api_url = "https://wave.webaim.org/api/request"

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    wave_api_url,
                    params={
                        "key": api_key,
                        "url": url,
                        "reporttype": "4",  # JSON report with details
                    },
                )

                if response.status_code == 200:
                    wave_data = response.json()

                    # Check for API errors
                    if "error" in wave_data:
                        results["error"] = wave_data["error"]
                        logger.error(f"WAVE API error: {wave_data['error']}")
                        return results

                    # Process WAVE results
                    categories = wave_data.get("categories", {})

                    results["success"] = True
                    results["errors"] = _process_wave_category(
                        categories.get("error", {}), "error"
                    )
                    results["alerts"] = _process_wave_category(
                        categories.get("alert", {}), "alert"
                    )
                    results["features"] = _process_wave_category(
                        categories.get("feature", {}), "feature"
                    )
                    results["structure"] = _process_wave_category(
                        categories.get("structure", {}), "structure"
                    )
                    results["aria"] = _process_wave_category(
                        categories.get("aria", {}), "aria"
                    )
                    results["contrast"] = _process_wave_category(
                        categories.get("contrast", {}), "contrast"
                    )

                    results["summary"] = {
                        "total_errors": categories.get("error", {}).get("count", 0),
                        "total_alerts": categories.get("alert", {}).get("count", 0),
                        "total_features": categories.get("feature", {}).get("count", 0),
                        "total_structure": categories.get("structure", {}).get(
                            "count", 0
                        ),
                        "total_aria": categories.get("aria", {}).get("count", 0),
                        "total_contrast": categories.get("contrast", {}).get("count", 0),
                    }

                    logger.info(
                        f"WAVE audit completed: {results['summary']['total_errors']} errors, "
                        f"{results['summary']['total_alerts']} alerts found"
                    )
                else:
                    results["error"] = f"WAVE API returned status {response.status_code}"
                    logger.error(results["error"])

        except Exception as e:
            logger.error(f"Error running WAVE audit: {str(e)}")
            results["error"] = str(e)

        return results

    @activity.defn
    async def generate_report(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a combined accessibility audit report.

        Args:
            params: Dictionary containing:
                - url: The audited URL
                - axe_results: Results from axe-core audit
                - wave_results: Results from WAVE audit (optional)
                - wcag_level: WCAG conformance level

        Returns:
            Dictionary containing the combined report
        """
        url = params.get("url", "")
        axe_results = params.get("axe_results", {})
        wave_results = params.get("wave_results")
        wcag_level = params.get("wcag_level", "AA")

        logger.info(f"Generating accessibility report for {url}")

        report = {
            "url": url,
            "wcag_level": wcag_level,
            "generated_at": datetime.utcnow().isoformat(),
            "tools_used": ["axe-core"],
            "overall_score": 0,
            "axe_summary": {},
            "wave_summary": {},
            "all_violations": [],
            "recommendations": [],
        }

        # Process axe-core results
        if axe_results.get("success"):
            report["axe_summary"] = axe_results.get("summary", {})
            report["all_violations"].extend(
                [
                    {**v, "source": "axe-core"}
                    for v in axe_results.get("violations", [])
                ]
            )

        # Process WAVE results if available
        if wave_results and wave_results.get("success"):
            report["tools_used"].append("WAVE")
            report["wave_summary"] = wave_results.get("summary", {})

            # Add WAVE errors as violations
            for error in wave_results.get("errors", []):
                report["all_violations"].append(
                    {
                        "id": error.get("id", ""),
                        "description": error.get("description", ""),
                        "impact": "serious",  # WAVE errors are generally serious
                        "count": error.get("count", 1),
                        "source": "WAVE",
                    }
                )

        # Calculate overall score (simplified scoring)
        total_issues = len(report["all_violations"])
        critical_count = sum(
            1 for v in report["all_violations"] if v.get("impact") == "critical"
        )
        serious_count = sum(
            1 for v in report["all_violations"] if v.get("impact") == "serious"
        )

        # Score calculation: start at 100, deduct for issues
        score = 100
        score -= critical_count * 15
        score -= serious_count * 10
        score -= (total_issues - critical_count - serious_count) * 5
        report["overall_score"] = max(0, min(100, score))

        # Generate recommendations
        report["recommendations"] = _generate_recommendations(report["all_violations"])

        # Sort violations by impact
        impact_order = {"critical": 0, "serious": 1, "moderate": 2, "minor": 3}
        report["all_violations"].sort(
            key=lambda x: impact_order.get(x.get("impact", "minor"), 4)
        )

        logger.info(
            f"Report generated: Score {report['overall_score']}/100, "
            f"{total_issues} total issues"
        )

        return report


def _process_axe_violations(violations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process axe-core violations into a simplified format."""
    processed = []
    for v in violations:
        processed.append(
            {
                "id": v.get("id", ""),
                "impact": v.get("impact", "minor"),
                "description": v.get("description", ""),
                "help": v.get("help", ""),
                "help_url": v.get("helpUrl", ""),
                "tags": v.get("tags", []),
                "nodes_affected": len(v.get("nodes", [])),
                "nodes": [
                    {
                        "html": node.get("html", "")[:200],  # Truncate long HTML
                        "target": node.get("target", []),
                        "failure_summary": node.get("failureSummary", ""),
                    }
                    for node in v.get("nodes", [])[:5]  # Limit to first 5 nodes
                ],
            }
        )
    return processed


def _process_wave_category(
    category: Dict[str, Any], category_type: str
) -> List[Dict[str, Any]]:
    """Process a WAVE category into a list of items."""
    items = []
    for item_id, item_data in category.get("items", {}).items():
        items.append(
            {
                "id": item_id,
                "type": category_type,
                "description": item_data.get("description", ""),
                "count": item_data.get("count", 1),
            }
        )
    return items


def _generate_recommendations(violations: List[Dict[str, Any]]) -> List[str]:
    """Generate recommendations based on violations."""
    recommendations = []
    violation_ids = {v.get("id", "") for v in violations}

    # Common recommendations based on violation types
    recommendation_map = {
        "color-contrast": "Ensure sufficient color contrast between text and backgrounds (minimum 4.5:1 for normal text, 3:1 for large text).",
        "image-alt": "Add descriptive alt text to all images that convey information.",
        "label": "Associate form inputs with labels using the 'for' attribute or by nesting inputs within label elements.",
        "link-name": "Ensure all links have discernible text that describes the link's purpose.",
        "button-name": "Provide accessible names for all buttons using visible text, aria-label, or aria-labelledby.",
        "html-has-lang": "Add a lang attribute to the <html> element to specify the page's language.",
        "document-title": "Provide a descriptive title for each page using the <title> element.",
        "heading-order": "Maintain proper heading hierarchy (h1, h2, h3, etc.) without skipping levels.",
        "landmark-one-main": "Include exactly one <main> landmark on each page.",
        "region": "Ensure all page content is contained within landmark regions.",
        "aria-required-attr": "Include all required ARIA attributes for elements with ARIA roles.",
        "aria-valid-attr": "Use only valid ARIA attributes and values.",
        "tabindex": "Avoid using tabindex values greater than 0.",
        "focus-visible": "Ensure keyboard focus is visible on all interactive elements.",
    }

    for vid, rec in recommendation_map.items():
        if vid in violation_ids:
            recommendations.append(rec)

    # Add general recommendations if there are many issues
    if len(violations) > 10:
        recommendations.append(
            "Consider implementing automated accessibility testing in your CI/CD pipeline to catch issues early."
        )

    if not recommendations:
        recommendations.append(
            "Great job! Continue to test with assistive technologies and real users."
        )

    return recommendations[:10]  # Limit to top 10 recommendations
