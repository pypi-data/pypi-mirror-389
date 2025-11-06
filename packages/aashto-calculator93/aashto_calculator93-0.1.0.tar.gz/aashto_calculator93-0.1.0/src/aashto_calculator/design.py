import math
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet

def aashto_thickness(W18, ZR, SO, delta_PSI, MR):
    """Compute Structural Number (SN)"""
    SN = 2.0
    for _ in range(100):
        lhs = math.log10(W18)
        rhs = (
            ZR * SO
            + 9.36 * math.log10(SN + 1) - 0.20
            + (math.log10(delta_PSI / (4.2 - 1.5))) /
              (0.40 + (1094 / ((SN + 1) ** 5.19)))
            + 2.32 * math.log10(MR) - 8.07
        )
        err = lhs - rhs
        if abs(err) < 1e-6:
            break
        SN += 0.01 * err
    return round(SN, 3)


def draw_pavement(SN, save_path="pavement.png"):
    """Draw a simple pavement structure (asphalt + base + subbase + subgrade)."""
    layers = ["Asphalt", "Base", "Subbase", "Subgrade"]
    thicknesses = [SN*0.25, SN*0.35, SN*0.40, 10]
    colors = ["#333333", "#888888", "#BBBBBB", "#DDCCAA"]

    y_bottom = 0
    for layer, t, c in zip(layers, thicknesses, colors):
        plt.barh([0], [100], left=0, height=t, color=c, edgecolor="black")
        plt.text(50, y_bottom + t/2, f"{layer}\n{t:.1f} in", ha='center', va='center', fontsize=9)
        y_bottom += t

    plt.axis('off')
    plt.xlim(0, 100)
    plt.ylim(0, y_bottom)
    plt.title(f"Pavement Structure for SN = {SN}")
    plt.savefig(save_path, bbox_inches='tight')
    plt.close()


def make_report(W18, ZR, SO, delta_PSI, MR, SN, image_path="pavement.png", pdf_path="reports/report.pdf"):
    """Generate a simple PDF report."""
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_path)
    story = []

    story.append(Paragraph("<b>AASHTO 1993 Pavement Design Report</b>", styles["Title"]))
    story.append(Spacer(1, 20))
    story.append(Paragraph(f"Design Inputs:", styles["Heading2"]))
    story.append(Paragraph(f"- W18: {W18:.2e}", styles["Normal"]))
    story.append(Paragraph(f"- ZR: {ZR}", styles["Normal"]))
    story.append(Paragraph(f"- SO: {SO}", styles["Normal"]))
    story.append(Paragraph(f"- ΔPSI: {delta_PSI}", styles["Normal"]))
    story.append(Paragraph(f"- MR: {MR} psi", styles["Normal"]))
    story.append(Spacer(1, 10))
    story.append(Paragraph(f"<b>Computed Structural Number (SN):</b> {SN}", styles["Heading2"]))
    story.append(Spacer(1, 20))
    story.append(Image(image_path, width=400, height=200))
    doc.build(story)
    print(f"✅ Report generated: {pdf_path}")

