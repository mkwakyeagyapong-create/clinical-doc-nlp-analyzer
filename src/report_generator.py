"""
ReportGenerator — Produces structured documentation quality reports
in multiple formats (HTML, JSON, CSV).

Generates human-readable and machine-readable reports from analysis
results for review by clinical documentation improvement specialists,
quality managers, and compliance officers.

Author: Michael Kwakye Agyapong
"""

import json
import os
from datetime import datetime
from typing import Optional


class ReportGenerator:
    """
    Generates documentation quality reports from analysis results.

    Supports HTML (human-readable), JSON (machine-readable), and
    CSV (spreadsheet-compatible) output formats.

    Parameters
    ----------
    config : dict
        Configuration dictionary with output settings.
    """

    def __init__(self, config: dict):
        output_config = config.get("output", {})
        self.formats = output_config.get("formats", ["json"])
        self.output_dir = output_config.get("output_dir", "output/reports")

    def generate(self, report, output_path: str, format: str = "json") -> str:
        """
        Generate a report file from analysis results.

        Parameters
        ----------
        report : AnalysisReport
            The analysis report to export.
        output_path : str
            Path for the output file.
        format : str
            Output format ('json', 'html', 'csv').

        Returns
        -------
        str
            Path to the generated report file.
        """
        os.makedirs(os.path.dirname(output_path) or ".", exist_ok=True)

        if format == "json":
            return self._generate_json(report, output_path)
        elif format == "html":
            return self._generate_html(report, output_path)
        elif format == "csv":
            return self._generate_csv(report, output_path)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _generate_json(self, report, output_path: str) -> str:
        """Generate JSON report."""
        with open(output_path, "w") as f:
            json.dump(report.to_dict(), f, indent=2, default=str)
        return output_path

    def _generate_html(self, report, output_path: str) -> str:
        """Generate HTML report."""
        severity_colors = {
            "CRITICAL": "#dc3545",
            "HIGH": "#e74c3c",
            "MEDIUM": "#f39c12",
            "LOW": "#3498db",
        }

        deficiency_rows = ""
        for d in report.deficiencies:
            color = severity_colors.get(d.severity, "#666")
            deficiency_rows += f"""
            <tr>
                <td><span style="color:{color};font-weight:bold;">{d.severity}</span></td>
                <td>{d.category}</td>
                <td>{d.description}</td>
                <td>{d.recommended_action or 'N/A'}</td>
            </tr>"""

        dimension_rows = ""
        for dim, score in report.dimension_scores.items():
            bar_color = "#27ae60" if score >= 80 else "#f39c12" if score >= 60 else "#e74c3c"
            dimension_rows += f"""
            <tr>
                <td>{dim.replace('_', ' ').title()}</td>
                <td>
                    <div style="background:#eee;border-radius:4px;overflow:hidden;">
                        <div style="width:{score}%;background:{bar_color};
                             padding:4px 8px;color:white;font-size:12px;">
                            {score:.0f}%
                        </div>
                    </div>
                </td>
            </tr>"""

        score_color = "#27ae60" if report.quality_score >= 80 else \
                      "#f39c12" if report.quality_score >= 60 else "#e74c3c"

        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Clinical Documentation Quality Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; max-width: 900px;
               margin: 0 auto; padding: 20px; color: #333; }}
        h1 {{ color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px; }}
        h2 {{ color: #2c3e50; margin-top: 30px; }}
        table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
        th, td {{ padding: 10px 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #f8f9fa; font-weight: bold; }}
        .score-badge {{ font-size: 48px; font-weight: bold; color: {score_color};
                       text-align: center; padding: 20px; }}
        .meta {{ color: #666; font-size: 14px; }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid #ddd;
                  font-size: 12px; color: #999; }}
    </style>
</head>
<body>
    <h1>Clinical Documentation Quality Report</h1>
    <p class="meta">
        Note Type: {report.note_type} |
        Analyzed: {report.analysis_date} |
        Word Count: {report.metadata.get('word_count', 'N/A')}
    </p>

    <div class="score-badge">{report.quality_score:.0f}/100</div>
    <p style="text-align:center;color:#666;">Composite Quality Score</p>

    <h2>Dimension Scores</h2>
    <table>{dimension_rows}
    </table>

    <h2>Deficiencies Detected ({len(report.deficiencies)})</h2>
    <table>
        <tr>
            <th style="width:80px;">Severity</th>
            <th style="width:120px;">Category</th>
            <th>Description</th>
            <th style="width:250px;">Recommended Action</th>
        </tr>
        {deficiency_rows}
    </table>

    <div class="footer">
        Generated by Clinical Documentation NLP Analyzer v0.1.0<br>
        Author: Michael Kwakye Agyapong |
        <a href="https://github.com/mkagyapong/clinical-doc-nlp-analyzer">GitHub</a>
    </div>
</body>
</html>"""

        with open(output_path, "w") as f:
            f.write(html)
        return output_path

    def _generate_csv(self, report, output_path: str) -> str:
        """Generate CSV report of deficiencies."""
        import csv
        with open(output_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Severity", "Category", "Description",
                "Recommended Action", "Quality Score"
            ])
            for d in report.deficiencies:
                writer.writerow([
                    d.severity, d.category, d.description,
                    d.recommended_action or "", report.quality_score
                ])
        return output_path
