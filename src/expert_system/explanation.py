from datetime import datetime

from src.expert_system.rules import Violation, Severity
from src.expert_system.inference_engine import ScheduleAnalysisResult


class ExplanationGenerator:
    """Generator for analysis results explanations"""

    SEVERITY_COLORS = {
        Severity.CRITICAL: '🔴',
        Severity.MEDIUM: '🟡',
        Severity.LOW: '🟢'
    }

    # Czech severity names
    SEVERITY_NAMES = {
        Severity.CRITICAL: 'KRITICKÉ',
        Severity.MEDIUM: 'STŘEDNÍ',
        Severity.LOW: 'NÍZKÉ'
    }

    # Czech rule names
    RULE_NAMES_CS = {
        'MaxContinuousDancing': 'Nepřetržitý čas tance',
        'CostumeChangeTime': 'Čas na převlečení kostýmu',
        'MaxContinuousJudging': 'Nepřetržitý čas rozhodování',
        'MaxGapBetweenPerformances': 'Velká přestávka mezi vystoupeními'
    }

    def generate_console_report(self, result: ScheduleAnalysisResult) -> str:
        """Generate report for console output

        Args:
            result: Schedule analysis result

        Returns:
            Formatted console report string
        """
        lines = []
        lines.append("=" * 80)
        lines.append("ANALÝZA ROZVRHU TANEČNÍHO KONKURZU")
        lines.append("=" * 80)
        lines.append("")

        # General information
        summary = result.get_summary()
        lines.append(f"📊 CELKOVÉ HODNOCENÍ: {result.rating}")
        lines.append(f"⚖️  Celková váha porušení: {result.total_weight:.1f}")
        lines.append(f"📝 Celkem porušení: {summary['total_violations']}")
        lines.append(f"   🔴 Kritických: {summary['critical_count']}")
        lines.append(f"   🟡 Středních: {summary['medium_count']}")
        lines.append(f"   🟢 Nízkých: {summary['low_count']}")
        lines.append("")

        if not result.violations:
            lines.append("✅ Nebyla zjištěna žádná porušení! Rozvrh je sestavený ideálně.")
            lines.append("=" * 80)
            return "\n".join(lines)

        # Violations by rules
        lines.append("-" * 80)
        lines.append("PORUŠENÍ PODLE PRAVIDEL")
        lines.append("-" * 80)
        lines.append("")

        for rule_name, violations in result.violations_by_rule.items():
            rule_name_cs = self.RULE_NAMES_CS.get(rule_name, rule_name)
            lines.append(f"📌 {rule_name_cs}: {len(violations)} porušení")

            # Sort by severity
            sorted_violations = sorted(
                violations,
                key=lambda v: (-v.weight)
            )

            for violation in sorted_violations:
                lines.append(self._format_violation(violation))

            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def _format_violation(self, violation: Violation) -> str:
        """Format a single violation for console output

        Args:
            violation: Violation object to format

        Returns:
            Formatted violation string
        """
        icon = self.SEVERITY_COLORS[violation.severity]
        severity_name = self.SEVERITY_NAMES[violation.severity]

        text = f"  {icon} [{severity_name}] (váha: {violation.weight:.1f}) {violation.description}"

        # Add details if available
        if 'start_time' in violation.details and 'end_time' in violation.details:
            start = violation.details['start_time']
            end = violation.details['end_time']
            text += f"\n     Čas: {start.strftime('%H:%M')} - {end.strftime('%H:%M')}"

        if 'gap_minutes' in violation.details:
            gap = violation.details['gap_minutes']
            text += f"\n     Přestávka: {gap:.0f} minut"

        if 'duration_minutes' in violation.details:
            duration = violation.details['duration_minutes']
            text += f"\n     Délka: {duration:.0f} minut"

        return text

    def generate_html_report(self, result: ScheduleAnalysisResult, output_path: str):
        """Generate HTML report and save to file

        Args:
            result: Schedule analysis result
            output_path: Path where to save the HTML file
        """
        html = self._build_html(result)

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html)

    def _build_html(self, result: ScheduleAnalysisResult) -> str:
        """Build HTML report content

        Args:
            result: Schedule analysis result

        Returns:
            Complete HTML document as string
        """
        summary = result.get_summary()

        # Define rating colors
        rating_colors = {
            'VYNIKAJÍCÍ': '#4CAF50',
            'DOBRÉ': '#8BC34A',
            'PŘIJATELNÉ': '#FFC107',
            'ŠPATNÉ': '#FF9800',
            'KRITICKÉ': '#F44336'
        }
        rating_color = rating_colors.get(result.rating, '#757575')

        html = f"""
<!DOCTYPE html>
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
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
        }}
        .summary {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            margin-bottom: 30px;
        }}
        .rating {{
            font-size: 2em;
            font-weight: bold;
            color: {rating_color};
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .stat-card {{
            background: #f9f9f9;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #667eea;
        }}
        .violation {{
            background: white;
            padding: 15px;
            margin-bottom: 15px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .violation.critical {{
            border-left: 4px solid #F44336;
        }}
        .violation.medium {{
            border-left: 4px solid #FFC107;
        }}
        .violation.low {{
            border-left: 4px solid #4CAF50;
        }}
        .rule-section {{
            margin-bottom: 30px;
        }}
        .rule-title {{
            background: #667eea;
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 15px;
        }}
        .details {{
            color: #666;
            font-size: 0.9em;
            margin-top: 10px;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Analýza rozvrhu tanečního konkurzu</h1>
        <p>Datum vytvoření zprávy: {datetime.now().strftime('%d.%m.%Y %H:%M')}</p>
    </div>
    
    <div class="summary">
        <div class="rating">Hodnocení: {result.rating}</div>
        <div class="stats">
            <div class="stat-card">
                <h3>Celková váha</h3>
                <p style="font-size: 1.5em; margin: 0;">{result.total_weight:.1f}</p>
            </div>
            <div class="stat-card">
                <h3>Celkem porušení</h3>
                <p style="font-size: 1.5em; margin: 0;">{summary['total_violations']}</p>
            </div>
            <div class="stat-card">
                <h3>🔴 Kritických</h3>
                <p style="font-size: 1.5em; margin: 0;">{summary['critical_count']}</p>
            </div>
            <div class="stat-card">
                <h3>🟡 Středních</h3>
                <p style="font-size: 1.5em; margin: 0;">{summary['medium_count']}</p>
            </div>
            <div class="stat-card">
                <h3>🟢 Nízkých</h3>
                <p style="font-size: 1.5em; margin: 0;">{summary['low_count']}</p>
            </div>
        </div>
    </div>
"""

        if result.violations:
            for rule_name, violations in result.violations_by_rule.items():
                rule_name_cs = self.RULE_NAMES_CS.get(rule_name, rule_name)
                html += f"""
    <div class="rule-section">
        <div class="rule-title">
            <h2>{rule_name_cs}</h2>
            <p style="margin: 0;">Zjištěno porušení: {len(violations)}</p>
        </div>
"""

                sorted_violations = sorted(violations, key=lambda v: (-v.weight))

                for violation in sorted_violations:
                    html += self._format_violation_html(violation)

                html += "    </div>\n"
        else:
            html += """
    <div class="summary">
        <h2>✅ Nebyla zjištěna žádná porušení!</h2>
        <p>Rozvrh je sestavený ideálně.</p>
    </div>
"""

        html += """
</body>
</html>
"""
        return html

    def _format_violation_html(self, violation: Violation) -> str:
        """Format violation for HTML output

        Args:
            violation: Violation object to format

        Returns:
            HTML string for the violation
        """
        severity_class = violation.severity.value
        severity_icon = self.SEVERITY_COLORS[violation.severity]
        severity_name = self.SEVERITY_NAMES[violation.severity]

        html = f"""
        <div class="violation {severity_class}">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <strong>{severity_icon} {severity_name}</strong> - {violation.description}
                </div>
                <div style="font-weight: bold; color: #667eea;">
                    Váha: {violation.weight:.1f}
                </div>
            </div>
            <div class="details">
"""

        if 'start_time' in violation.details and 'end_time' in violation.details:
            start = violation.details['start_time']
            end = violation.details['end_time']
            html += f"                <p>🕐 Čas: {start.strftime('%H:%M')} - {end.strftime('%H:%M')}</p>\n"

        if 'gap_minutes' in violation.details:
            gap = violation.details['gap_minutes']
            html += f"                <p>⏱️ Přestávka: {gap:.0f} minut</p>\n"

        if 'from_time'in violation.details and 'to_time' in violation.details:
            from_time = violation.details['from_time']
            to_time = violation.details['to_time']
            html += f"                <p>🕐 Časový úsek: {from_time.strftime('%H:%M')} - {to_time.strftime('%H:%M')}</p>\n"
            if 'from_discipline' in violation.details and 'to_discipline' in violation.details:
                from_discipline = violation.details['from_discipline']
                to_discipline = violation.details['to_discipline']
                html += f"                <p>💃 Disciplíny: {from_discipline} → {to_discipline}</p>\n"

        if 'duration_minutes' in violation.details:
            duration = violation.details['duration_minutes']
            html += f"                <p>⏱️ Délka: {duration:.0f} minut</p>\n"

        html += """
            </div>
        </div>
"""
        return html

