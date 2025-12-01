from fpdf import FPDF
import datetime

class PDF(FPDF):
    def header(self):
        # Logo or Title
        self.set_font('Arial', 'B', 15)
        self.cell(0, 10, 'NEO-GENESIS: AI Product Catalog Generator', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.set_fill_color(200, 220, 255)
        self.cell(0, 6, title, 0, 1, 'L', 1)
        self.ln(4)

    def chapter_body(self, body):
        self.set_font('Arial', '', 11)
        self.multi_cell(0, 5, body)
        self.ln()

def create_report():
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title Page
    pdf.set_font('Arial', 'B', 24)
    pdf.ln(50)
    pdf.cell(0, 10, 'Project Report', 0, 1, 'C')
    pdf.ln(10)
    pdf.set_font('Arial', '', 16)
    pdf.cell(0, 10, 'AI Product Catalog Generator', 0, 1, 'C')
    pdf.ln(20)
    pdf.set_font('Arial', '', 12)
    pdf.cell(0, 10, f'Date: {datetime.date.today().strftime("%B %d, %Y")}', 0, 1, 'C')
    pdf.add_page()

    # 1. Executive Summary
    pdf.chapter_title('1. Executive Summary')
    pdf.chapter_body(
        "The AI Product Catalog Generator ('Neo-Genesis') is a cutting-edge application designed to automate the creation of high-quality product assets. "
        "By leveraging advanced Generative AI models, the system takes simple text inputs and produces detailed visual descriptions, photorealistic images, and verification metrics. "
        "The project features a dual-interface approach: a high-performance desktop application and a modern web-based platform, both unified by a 'Cyber-Glass' design aesthetic."
    )

    # 2. Key Features
    pdf.chapter_title('2. Key Features')
    pdf.chapter_body(
        "- AI Image Generation: Utilizes the Flux model (via Replicate) to generate 8k, photorealistic product renders.\n"
        "- Intelligent Description: Uses Google Gemini 2.0 Flash to expand simple keywords into rich, descriptive prompts.\n"
        "- Automated Verification: A custom-trained CLIP + MLP model verifies if the generated image matches the product description, providing a confidence score.\n"
        "- Parallel Processing: Generates multiple product variants simultaneously using multi-threading.\n"
        "- Smart Caching: Caches AI-generated backgrounds and assets to optimize performance and cost.\n"
        "- Dual Interface: Available as a native Desktop App (CustomTkinter) and a Web App (Flask + HTML5)."
    )

    # 3. Technical Architecture
    pdf.chapter_title('3. Technical Architecture')
    pdf.chapter_body(
        "The system is built on a robust Python ecosystem:\n\n"
        "Backend / Core Logic:\n"
        "- Python 3.10+\n"
        "- Flask (Web Server)\n"
        "- Replicate API (Flux Model for Image Gen)\n"
        "- Google Generative AI SDK (Gemini for Text Gen)\n"
        "- PyTorch & Transformers (CLIP Model for Verification)\n\n"
        "Frontend / UI:\n"
        "- Desktop: CustomTkinter (Modern wrapper for Tkinter)\n"
        "- Web: HTML5, CSS3 (Glassmorphism), JavaScript\n\n"
        "Data Flow:\n"
        "Input -> Gemini (Description) -> Flux (Image) -> CLIP (Verification) -> UI Display"
    )

    # 4. User Interface Design
    pdf.chapter_title('4. User Interface Design')
    pdf.chapter_body(
        "The project implements a distinct 'Cyber-Glass 2.0' design language:\n"
        "- Background: Deep, procedurally generated or AI-generated nebula/aurora backgrounds (Deep Purple/Violet theme).\n"
        "- Components: Semi-transparent 'frosted glass' panels with glowing neon borders.\n"
        "- Animations: Smooth transitions, floating elements, and matrix-style status streams.\n"
        "- Responsiveness: Adaptive grid layouts that adjust to screen size on both desktop and web."
    )

    # 5. Future Enhancements
    pdf.chapter_title('5. Future Enhancements')
    pdf.chapter_body(
        "- User Accounts: Save and manage catalogs across devices.\n"
        "- Direct Export: Export catalogs to PDF or e-commerce formats (Shopify/WooCommerce).\n"
        "- Fine-tuning: Allow users to fine-tune the image generation model on their own brand assets.\n"
        "- 3D Model Generation: Expand from 2D images to 3D assets."
    )

    pdf.output('Project_Report.pdf')
    print("PDF Report generated successfully: Project_Report.pdf")

if __name__ == "__main__":
    create_report()
