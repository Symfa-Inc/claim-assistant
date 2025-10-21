import io
import logging
from datetime import datetime
from pathlib import Path

from PyPDF2 import PdfReader, PdfWriter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from claim_assistant.models.form import Form
from claim_assistant.schemas.coverage_analysis import CoverageAnalysis
from claim_assistant.schemas.mock_policy_record import MockPolicyRecord


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
        if rows[1][0] == "Confidence Score":
            confidence_score = float(rows[1][1])
        data = []
        conclusion_color = None
        for key, val in rows:
            if val == "Positive" and confidence_score == 1.0:
                conclusion_color = colors.lightgreen
            elif val == "Uncertain":
                conclusion_color = colors.yellow
            elif val == "Negative" and confidence_score == 1.0:
                conclusion_color = colors.salmon
            elif val == "Negative":
                conclusion_color = colors.yellow

            if key == "Confidence Score" and confidence_score is not None:
                val = f"{int(confidence_score * 100)}%"

            key_p = self._para(f"<b>{key}:</b>")
            val_p = self._para(val or "")
            data.append([key_p, val_p])

        tbl = Table(data, colWidths=[2.0 * inch, 4.5 * inch], hAlign="LEFT")
        if conclusion_color:
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                        (
                            "BACKGROUND",
                            (-1, 0),
                            (-1, 0),
                            conclusion_color,
                        ),  # highlight conclusion (certain position)
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ],
                ),
            )
        else:
            tbl.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("BOX", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.lightgrey),
                        ("LEFTPADDING", (0, 0), (-1, -1), 6),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                    ],
                ),
            )
        return tbl

    def _page_number(self, canvas, doc):
        canvas.setFont("Helvetica", 9)
        canvas.setFillColor(colors.grey)
        canvas.drawRightString(doc.pagesize[0] - 36, 20, f"Page {doc.page}")

    # ------------------------------------------------------------
    # Main generation logic
    # ------------------------------------------------------------
    def process(
        self,
        form: Form,
        policy: MockPolicyRecord,
        analysis: CoverageAnalysis,
        output_path: str | Path,
    ) -> Path:
        """
        Create a multi-section PDF report:
          1. Executive summary (LLM conclusion and short text)
          2. Form contents (all extracted questions and answers)
          3. Policy metadata and full policy coverage as appendix

        Args:
            form: Filled Form object.
            policy: Matching MockPolicyRecord.
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
                    ("Conclusion", analysis.conclusion.capitalize()),
                    ("Confidence Score", f"{analysis.confidence:.2f}"),
                    ("Summary", analysis.executive_summary),
                ],
            ),
        )

        story.append(Spacer(1, 18))

        # --- Section 2: Extracted Form Fields ---
        story.append(self._section_header("Extracted Form Fields"))
        form_rows = [(f.text, str(f.answer or "N/A")) for f in form.fields]
        story.append(self._kv_table(form_rows))

        # story.append(PageBreak())

        # --- Section 3: Policy Information ---
        story.append(self._section_header("Policy Information"))
        policy_rows = [
            ("Policy Number", policy.policy_number),
            (
                "Policy Holder",
                f"{policy.policy_holder_first_name} {policy.policy_holder_last_name}",
            ),
            ("Coverage Start Date", policy.start_date.isoformat()),
            ("Coverage End Date", policy.end_date.isoformat()),
            # ("Policy Document Path", str(policy.get_policy_path())),
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
