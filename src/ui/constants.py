from PySide6.QtGui import QColor

TABLE_STATUS_CONFIG: dict[str, tuple[str, str]] = {
    "not_loaded":    ("Nevybráno",                "#9E9E9E"),
    "needs_mapping": ("Vyžaduje výběr sloupců",   "#FF9800"),
    "ready":         ("Připraveno",               "#4CAF50"),
}

DOT_STYLE = "border-radius: 8px; width: 16px; height: 16px; background-color: {color};"

MAPPING_HIGHLIGHT_COLORS = [
    QColor("#BBDEFB"),  # light blue
    QColor("#C8E6C9"),  # light green
    QColor("#FFE0B2"),  # light orange
    QColor("#F8BBD9"),  # light pink
    QColor("#E1BEE7"),  # light purple
    QColor("#B2EBF2"),  # light cyan
    QColor("#FFF9C4"),  # light yellow
]
MAPPING_DEFAULT_BG = QColor("#FFFFFF")
MAPPING_DEFAULT_FG = QColor("#000000")
MAPPING_HIGHLIGHT_FG = QColor("#000000")
