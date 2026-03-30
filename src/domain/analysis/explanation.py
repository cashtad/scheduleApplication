from __future__ import annotations

from datetime import datetime
from pathlib import Path

from .schedule_analysis_result import ScheduleAnalysisResult
from .severity import Severity
from .violation import Violation


class ExplanationGenerator:
    SEVERITY_ICONS = {
        Severity.CRITICAL: "🔴",
        Severity.MEDIUM: "🟡",
        Severity.LOW: "🟢",
    }

    SEVERITY_NAMES_CS = {
        Severity.CRITICAL: "KRITICKÉ",
        Severity.MEDIUM: "STŘEDN��",
        Severity.LOW: "NÍZKÉ",
    }

    RULE_NAMES_CS = {
        "MaxContinuousDancing": "Nepřetržitý čas tance",
        "CostumeChangeTime": "Čas na převlečení kostýmu",
        "MaxContinuousJudging": "Nepřetržitý čas rozhodování",
        "MaxGapBetweenPerformances": "Velká přestávka mezi vystoupeními",
        "SimultaneousDancing": "Současné taneční vystoupení",
        "SimultaneousJudging": "Současné rozhodování",
    }

    def generate_console_report(self, result: ScheduleAnalysisResult) -> str:
        summary = result.get_summary()
        lines: list[str] = [
            "=" * 80,
            "ANALÝZA ROZVRHU TANEČNÍHO KONKURZU",
            "=" * 80,
            "",
            f"📝 Celkem porušení: {summary['total_violations']}",
            f"   🔴 Kritických: {summary['critical_count']}",
            f"   🟡 Středních: {summary['medium_count']}",
            f"   🟢 Nízkých: {summary['low_count']}",
            "",
        ]

        if not result.violations:
            lines.extend(
                [
                    "✅ Nebyla zjištěna žádná porušení! Rozvrh je sestavený ideálně.",
                    "=" * 80,
                ]
            )
            return "\n".join(lines)

        lines.extend(["-" * 80, "PORUŠENÍ PODLE PRAVIDEL", "-" * 80, ""])

        for rule_name, violations in result.violations_by_rule.items():
            rule_name_cs = self.RULE_NAMES_CS.get(rule_name, rule_name)
            lines.append(f"📌 {rule_name_cs}: {len(violations)} porušení")

            # deterministic sorting: severity first, then description
            sorted_violations = sorted(
                violations,
                key=lambda v: (self._severity_order(v.severity), v.description),
            )

            for violation in sorted_violations:
                lines.append(self._format_violation_console(violation))
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def generate_html_report(self, result: ScheduleAnalysisResult, output_path: str) -> str:
        html = self._build_html(result)
        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(html, encoding="utf-8")
        return str(path)

    def _build_html(self, result: ScheduleAnalysisResult) -> str:
        summary = result.get_summary()

        html = f"""<!DOCTYPE html>
<html lang="cs">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Analýza rozvrhu tanečního konkurzu</title>
  <style>
    body {{
      font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
      background-color: #f5f5f5;
    }}
    .header {{
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      padding: 24px;
      border-radius: 10px;
      margin-bottom: 20px;
    }}
    .summary {{
      background: white;
      padding: 20px;
      border-radius: 10px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.1);
      margin-bottom: 20px;
    }}
    .stats {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
      gap: 12px;
      margin-top: 12px;
    }}
    .stat-card {{
      background: #f9f9f9;
      padding: 12px;
      border-radius: 8px;
      border-left: 4px solid #667eea;
    }}
    .rule-section {{
      margin-bottom: 24px;
    }}
    .rule-title {{
      background: #667eea;
      color: white;
      padding: 12px;
      border-radius: 8px;
      margin-bottom: 12px;
    }}
    .violation {{
      background: white;
      padding: 12px;
      margin-bottom: 10px;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.08);
    }}
    .violation.critical {{ border-left: 4px solid #F44336; }}
    .violation.medium   {{ border-left: 4px solid #FFC107; }}
    .violation.low      {{ border-left: 4px solid #4CAF50; }}
    .details {{
      color: #666;
      font-size: 0.92em;
      margin-top: 8px;
    }}
  </style>
</head>
<body>
  <div class="header">
    <h1>📊 Analýza rozvrhu tanečního konkurzu</h1>
    <p>Datum vytvoření zprávy: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
  </div>

  <div class="summary">
    <h2>Souhrn</h2>
    <div class="stats">
      <div class="stat-card"><strong>Celkem porušení</strong><br>{summary['total_violations']}</div>
      <div class="stat-card"><strong>🔴 Kritických</strong><br>{summary['critical_count']}</div>
      <div class="stat-card"><strong>🟡 Středních</strong><br>{summary['medium_count']}</div>
      <div class="stat-card"><strong>🟢 Nízkých</strong><br>{summary['low_count']}</div>
    </div>
  </div>
"""

        if not result.violations:
            html += """
  <div class="summary">
    <h2>✅ Nebyla zjištěna žádná porušení!</h2>
    <p>Rozvrh je sestavený ideálně.</p>
  </div>
"""
        else:
            for rule_name, violations in result.violations_by_rule.items():
                rule_name_cs = self.RULE_NAMES_CS.get(rule_name, rule_name)
                html += f"""
  <div class="rule-section">
    <div class="rule-title">
      <h3 style="margin:0">{rule_name_cs}</h3>
      <p style="margin:4px 0 0 0">Zjištěno porušení: {len(violations)}</p>
    </div>
"""
                sorted_violations = sorted(
                    violations,
                    key=lambda v: (self._severity_order(v.severity), v.description),
                )
                for violation in sorted_violations:
                    html += self._format_violation_html(violation)

                html += "  </div>\n"

        html += """
</body>
</html>
"""
        return html

    def _format_violation_console(self, violation: Violation) -> str:
        icon = self.SEVERITY_ICONS[violation.severity]
        severity_name = self.SEVERITY_NAMES_CS[violation.severity]
        text = f"  {icon} [{severity_name}] {violation.description}"

        if "start_time" in violation.details and "end_time" in violation.details:
            start = violation.details["start_time"]
            end = violation.details["end_time"]
            text += f"\n     Čas: {start.strftime('%H:%M')} - {end.strftime('%H:%M')}"

        if "gap_minutes" in violation.details:
            text += f"\n     Přestávka: {violation.details['gap_minutes']:.0f} minut"

        if "duration_minutes" in violation.details:
            text += f"\n     Délka: {violation.details['duration_minutes']:.0f} minut"

        return text

    def _format_violation_html(self, violation: Violation) -> str:
        severity_class = violation.severity.value
        severity_icon = self.SEVERITY_ICONS[violation.severity]
        severity_name = self.SEVERITY_NAMES_CS[violation.severity]

        html = f"""
    <div class="violation {severity_class}">
      <div><strong>{severity_icon} {severity_name}</strong> — {violation.description}</div>
      <div class="details">
"""
        details = violation.details

        if "start_time" in details and "end_time" in details:
            html += f"        <p>🕐 Čas: {details['start_time'].strftime('%H:%M')} - {details['end_time'].strftime('%H:%M')}</p>\n"

        if "gap_minutes" in details:
            html += f"        <p>⏱️ Přestávka: {details['gap_minutes']:.0f} minut</p>\n"

        if "from_time" in details and "to_time" in details:
            html += f"        <p>🕐 Časový úsek: {details['from_time'].strftime('%H:%M')} - {details['to_time'].strftime('%H:%M')}</p>\n"

        if "from_discipline" in details and "to_discipline" in details:
            html += f"        <p>💃 Disciplíny: {details['from_discipline']} → {details['to_discipline']}</p>\n"

        if "duration_minutes" in details:
            html += f"        <p>⏱️ Délka: {details['duration_minutes']:.0f} minut</p>\n"

        if "overlap_minutes" in details:
            html += f"        <p>⚠️ Překrytí: {details['overlap_minutes']:.0f} minut</p>\n"

        if "overlap_start" in details and "overlap_end" in details:
            html += f"        <p>🕐 Čas překrytí: {details['overlap_start'].strftime('%H:%M')} - {details['overlap_end'].strftime('%H:%M')}</p>\n"

        if "competition1" in details and "competition2" in details:
            html += f"        <p>🏆 Soutěže: {details['competition1']} ↔ {details['competition2']}</p>\n"

        if violation.source_rows:
            rows = ", ".join(str(r) for r in sorted(set(violation.source_rows)))
            html += f"        <p>📍 Řádky rozvrhu: {rows}</p>\n"

        html += """
      </div>
    </div>
"""
        return html

    @staticmethod
    def _severity_order(severity: Severity) -> int:
        if severity == Severity.CRITICAL:
            return 0
        if severity == Severity.MEDIUM:
            return 1
        return 2