/**
 * PDF Export Utility
 *
 * Generates professional PDF reports with:
 * - Markdown content converted to formatted text
 * - Charts captured as images
 * - Proper page breaks and formatting
 */

import jsPDF from "jspdf";

interface VisualizationSummary {
  title?: string;
  type?: string;
  description?: string;
  [key: string]: unknown;
}

interface ExportData {
  sessionId: string;
  research_plan?: string;
  executive_summary?: string;
  final_report?: string;
  comparative_analysis?: {
    analysis_text?: string;
  };
  competitor_profiles?: Record<string, { analysis: string }>;
  visualizations?: VisualizationSummary[];
}

/**
 * Export research report to PDF
 *
 * @param data - Research results data
 * @param includeCharts - Whether to include chart images (slower but better)
 */
export async function exportToPDF(
  data: ExportData,
  includeCharts: boolean = true
): Promise<void> {
  const pdf = new jsPDF({
    orientation: "portrait",
    unit: "mm",
    format: "a4",
  });

  const pageWidth = pdf.internal.pageSize.getWidth();
  const pageHeight = pdf.internal.pageSize.getHeight();
  const margin = 20;
  const contentWidth = pageWidth - 2 * margin;
  let yPosition = margin;

  // Helper: Add page if needed
  const checkPageBreak = (neededSpace: number = 20) => {
    if (yPosition + neededSpace > pageHeight - margin) {
      pdf.addPage();
      yPosition = margin;
      return true;
    }
    return false;
  };

  // Helper: Add text with word wrap
  const addText = (
    text: string,
    fontSize: number = 11,
    fontStyle: "normal" | "bold" = "normal"
  ) => {
    pdf.setFontSize(fontSize);
    pdf.setFont("helvetica", fontStyle);

    const lines = pdf.splitTextToSize(text, contentWidth);
    lines.forEach((line: string) => {
      checkPageBreak(7);
      pdf.text(line, margin, yPosition);
      yPosition += 7;
    });
  };

  // Helper: Add heading
  const addHeading = (text: string, level: 1 | 2 | 3 = 1) => {
    const fontSize = level === 1 ? 18 : level === 2 ? 14 : 12;
    const spacing = level === 1 ? 15 : level === 2 ? 10 : 7;

    checkPageBreak(spacing + 10);
    yPosition += spacing;

    pdf.setFontSize(fontSize);
    pdf.setFont("helvetica", "bold");
    pdf.text(text, margin, yPosition);

    yPosition += 10;
  };

  // Helper: Add horizontal line
  const addLine = () => {
    checkPageBreak(5);
    pdf.setDrawColor(200, 200, 200);
    pdf.line(margin, yPosition, pageWidth - margin, yPosition);
    yPosition += 5;
  };

  // ============================================================================
  // PDF CONTENT
  // ============================================================================

  // Cover page
  pdf.setFontSize(24);
  pdf.setFont("helvetica", "bold");
  pdf.text("Market Research Report", pageWidth / 2, 60, { align: "center" });

  pdf.setFontSize(12);
  pdf.setFont("helvetica", "normal");
  pdf.text(`Generated: ${new Date().toLocaleDateString()}`, pageWidth / 2, 80, {
    align: "center",
  });

  pdf.setFontSize(10);
  pdf.setTextColor(100, 100, 100);
  pdf.text(`Session ID: ${data.sessionId.slice(0, 8)}`, pageWidth / 2, 90, {
    align: "center",
  });

  pdf.setTextColor(0, 0, 0);
  pdf.addPage();
  yPosition = margin;

  // Research Strategy (from Coordinator)
  if (data.research_plan) {
    addHeading("Research Strategy", 1);
    addLine();
    addText(data.research_plan);
    yPosition += 10;
  }

  // Executive Summary
  if (data.executive_summary) {
    addHeading("Executive Summary", 1);
    addLine();
    addText(data.executive_summary);
    yPosition += 10;
  }

  // Full Report
  if (data.final_report) {
    checkPageBreak(30);
    addHeading("Detailed Analysis", 1);
    addLine();

    // Parse markdown-style headings and content
    const reportLines = data.final_report.split("\n");
    for (const line of reportLines) {
      if (line.startsWith("# ")) {
        addHeading(line.replace("# ", ""), 1);
      } else if (line.startsWith("## ")) {
        addHeading(line.replace("## ", ""), 2);
      } else if (line.startsWith("### ")) {
        addHeading(line.replace("### ", ""), 3);
      } else if (line.trim().startsWith("- ")) {
        addText("  - " + line.replace(/^-\s*/, ""));
      } else if (line.trim()) {
        addText(line);
      } else {
        yPosition += 5; // Empty line spacing
      }
    }
  }

  // Comparative Analysis
  if (data.comparative_analysis?.analysis_text) {
    checkPageBreak(30);
    addHeading("Comparative Analysis", 1);
    addLine();
    addText(data.comparative_analysis.analysis_text);
    yPosition += 10;
  }

  // Competitor Profiles
  if (
    data.competitor_profiles &&
    Object.keys(data.competitor_profiles).length > 0
  ) {
    checkPageBreak(30);
    addHeading("Competitor Profiles", 1);
    addLine();

    for (const [company, profile] of Object.entries(data.competitor_profiles)) {
      checkPageBreak(20);
      addHeading(company, 2);
      addText(profile.analysis);
      yPosition += 10;
    }
  }

  // Visualizations (as images)
  if (includeCharts && data.visualizations && data.visualizations.length > 0) {
    pdf.addPage();
    yPosition = margin;
    addHeading("Data Visualizations", 1);
    addLine();

    // Capture charts as images
    const chartElements = document.querySelectorAll("canvas");
    for (
      let i = 0;
      i < Math.min(chartElements.length, data.visualizations.length);
      i++
    ) {
      try {
        const canvas = chartElements[i] as HTMLCanvasElement;
        const imgData = canvas.toDataURL("image/png");

        checkPageBreak(100);

        const imgWidth = contentWidth;
        const imgHeight = (canvas.height * contentWidth) / canvas.width;

        pdf.addImage(imgData, "PNG", margin, yPosition, imgWidth, imgHeight);
        yPosition += imgHeight + 10;

        // Add chart title if available
        if (data.visualizations[i].title) {
          pdf.setFontSize(10);
          pdf.setFont("helvetica", "italic");
          pdf.text(data.visualizations[i].title || "", pageWidth / 2, yPosition, {
            align: "center",
          });
          yPosition += 10;
        }
      } catch (error) {
        console.error("Failed to capture chart:", error);
      }
    }
  }

  // Footer on all pages
  const totalPages = pdf.internal.pages.length - 1; // Exclude the first empty page
  for (let i = 1; i <= totalPages; i++) {
    pdf.setPage(i);
    pdf.setFontSize(9);
    pdf.setTextColor(150, 150, 150);
    pdf.text(`Page ${i} of ${totalPages}`, pageWidth / 2, pageHeight - 10, {
      align: "center",
    });
    pdf.text(
      "Multi-Agent Market Research Platform",
      pageWidth / 2,
      pageHeight - 5,
      { align: "center" }
    );
  }

  // Save PDF
  const fileName = `research-report-${data.sessionId.slice(0, 8)}.pdf`;
  pdf.save(fileName);
}

/**
 * Quick PDF export without charts (faster)
 */
export async function exportToPDFQuick(data: ExportData): Promise<void> {
  return exportToPDF(data, false);
}
