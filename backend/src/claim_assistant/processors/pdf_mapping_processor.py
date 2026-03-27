import io
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

from claim_assistant.schemas import CoverageAnalysisResponse
from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


class PDFMappingProcessor:
    """
    Responsible for mapping a filled claim form and validation results
    back into a generated PDF report.

    This processor consolidates extracted form data, matched policy details,
    and LLM analysis results into a human-readable report.
    """

    def __init__(self, logger: logging.Logger) -> None:
        self.logger = logger

    # ------------------------------------------------------------
    # Utility helpers
    # ------------------------------------------------------------
    def _para(self, text: str, style_name: str = "BodyText") -> Paragraph:
        styles = getSampleStyleSheet()
        return Paragraph((text or "").replace("\n", "<br/>"), styles[style_name])

    def _section_header(self, text: str) -> Paragraph:
        styles = getSampleStyleSheet()
        hdr = ParagraphStyle(
            "SectionHeader",
            parent=styles["Heading2"],
            fontSize=13,
            textColor=colors.darkgreen,
            spaceBefore=12,
            spaceAfter=6,
        )
        return Paragraph(text, hdr)

    def _title(self, text: str) -> Paragraph:
        styles = getSampleStyleSheet()
        ttl = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            textColor=colors.darkblue,
            fontSize=16,
            spaceAfter=16,
        )
        return Paragraph(text, ttl)

    def _kv_table(self, rows: list[tuple[str, str]]) -> Table:
        """Create a simple key-value table."""
        confidence_score: float | None = None
        if len(rows) > 1 and rows[1][0] == "Confidence Score":
            try:
                confidence_score = float(rows[1][1])
            except Exception:
                confidence_score = None

        data: list[list[Paragraph]] = []
        conclusion_color = None

        for key, val in rows:
            if key == "Confidence Score" and confidence_score is not None:
                val = f"{int(confidence_score * 100)}%"

            if key == "Conclusion":
                if (val or "").lower() == "positive" and confidence_score == 1.0:
                    conclusion_color = colors.lightgreen
                elif (val or "").lower() == "uncertain":
                    conclusion_color = colors.yellow
                elif (val or "").lower() == "negative":
                    conclusion_color = colors.salmon

            key_p = self._para(f"<b>{key}:</b>")
            val_p = self._para(val or "")
            data.append([key_p, val_p])

        tbl = Table(data, colWidths=[2.0 * inch, 4.5 * inch], hAlign="LEFT")
        base_style = [
            ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("BOX", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
            ("LEFTPADDING", (0, 0), (-1, -1), 6),
            ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ]
        if conclusion_color:
            # highlight the "Conclusion" row value cell; it's row 0 in this table
            base_style.insert(
                1,
                ("BACKGROUND", (-1, 0), (-1, 0), conclusion_color),
            )
        tbl.setStyle(TableStyle(base_style))
        return tbl

    @classmethod
    def _format_field_value_and_confidence(cls, field) -> str:
        """
        Render a single field as:
          <value> (conf=XX%)
        without any bounding regions.

        If value is empty/None -> "N/A".
        """
        ans = getattr(field, "answer", None)
        if not ans:
            return "N/A"

        value = getattr(ans, "value", None)
        if value is None or (isinstance(value, str) and not value.strip()):
            value_str = "N/A"
        else:
            value_str = str(value)

        evidences = getattr(ans, "evidences", None) or []
        conf = cls._avg_confidence(evidences)
        if conf is None:
            return value_str

        return f"{value_str} (conf={int(conf * 100)}%)"

    @staticmethod
    def _avg_confidence(evidences: list[Any]) -> float | None:
        """
        Average confidence across evidences.
        Evidences may arrive as Pydantic models or raw dicts.
        """
        if not evidences:
            return None

        vals: list[float] = []
        for e in evidences:
            conf = None
            if isinstance(e, dict):
                conf = e.get("confidence")
            else:
                conf = getattr(e, "confidence", None)
            if conf is None:
                continue
            try:
                vals.append(float(conf))
            except Exception:
                continue

        if not vals:
            return None
        return sum(vals) / len(vals)

    def _page_number(self, canvas, doc):
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(doc.pagesize[0] - 36, 20, f"Page {doc.page}")

    # ------------------------------------------------------------
    # Main generation logic
    # ------------------------------------------------------------
    def process(
        self,
        analysis: CoverageAnalysisResponse,
        output_path: str | Path,
    ) -> Path:
        """
        Create a multi-section PDF report:
          1. Executive summary (LLM conclusion and short text)
          2. Form contents (all extracted questions and answers)
          3. Policy metadata and full policy coverage as appendix

        Args:
            analysis: CoverageAnalysis result.
            output_path: Path to save generated PDF.

        Returns:
            Path to saved PDF file.
        """
        self.logger.info("Generating claim report PDF...")
        output = Path(output_path)
        output.parent.mkdir(parents=True, exist_ok=True)

        temp_buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            temp_buffer,
            pagesize=letter,
            leftMargin=54,
            rightMargin=54,
            topMargin=54,
            bottomMargin=54,
            title="Insurance Claim Report",
            author="Claim Assistant",
        )

        story: list = []
        story.append(self._title("Insurance Claim Report"))
        story.append(
            self._para(
                f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                style_name="Italic",
            ),
        )
        story.append(Spacer(1, 16))

        # --- Section 1: Executive Summary ---
        story.append(self._section_header("Executive Summary"))
        story.append(
            self._kv_table(
                [
                    ("Conclusion", (analysis.conclusion or "unknown").capitalize()),
                    ("Confidence Score", f"{analysis.confidence:.2f}"),
                    ("Summary", analysis.executive_summary or ""),
                ],
            ),
        )

        story.append(Spacer(1, 18))

        # --- Section 2: Extracted Form Fields ---
        story.append(self._section_header("Extracted Form Fields"))
        form_fields = analysis.form or []
        form_rows = [
            (f.text, self._format_field_value_and_confidence(f)) for f in form_fields
        ]
        story.append(self._kv_table(form_rows))
        story.append(Spacer(1, 18))

        # story.append(PageBreak())

        # --- Section 3: Policy Information ---
        policy = analysis.policy
        if policy is not None:
            story.append(self._section_header("Policy Information"))
            policy_rows = [
                ("Policy Number", getattr(policy, "policy_number", "") or "N/A"),
                (
                    "Policy Holder",
                    (
                        f"{getattr(policy, 'policy_holder_first_name', '')} "
                        f"{getattr(policy, 'policy_holder_last_name', '')}"
                    ).strip()
                    or "N/A",
                ),
                (
                    "Coverage Start Date",
                    getattr(
                        getattr(policy, "start_date", None),
                        "isoformat",
                        lambda: "N/A",
                    )(),
                ),
                (
                    "Coverage End Date",
                    getattr(
                        getattr(policy, "end_date", None),
                        "isoformat",
                        lambda: "N/A",
                    )(),
                ),
            ]
            story.append(self._kv_table(policy_rows))

        story.append(Spacer(1, 24))
        story.append(
            self._para(
                "<font size=9 color=grey>This report is auto-generated by Claim Assistant.</font>",
            ),
        )

        # Build PDF into buffer
        doc.build(story, onFirstPage=self._page_number, onLaterPages=self._page_number)
        temp_buffer.seek(0)

        # --- Combine base report with policy PDF ---
        writer = PdfWriter()
        report_reader = PdfReader(temp_buffer)
        for page in report_reader.pages:
            writer.add_page(page)

        # policy_path = policy.get_policy_path()
        # if policy_path and policy_path.exists():
        #     try:
        #         policy_reader = PdfReader(str(policy_path))
        #         for page in policy_reader.pages:
        #             writer.add_page(page)
        #         self.logger.info(f"Appended {len(policy_reader.pages)} policy pages.")
        #     except Exception as e:
        #         self.logger.error(f"Failed to append policy PDF: {e}")

        # --- Save final combined report ---
        with open(output, "wb") as f:
            writer.write(f)

        self.logger.info(f"PDF report successfully written to {output}")
        return output
