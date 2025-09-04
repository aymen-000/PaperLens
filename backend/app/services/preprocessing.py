import fitz  # PyMuPDF
import os
from pathlib import Path
from typing import List, Dict, Any


class PaperPreprocessor:
    """
    Handles preprocessing of a research paper PDF:
    - Extracts metadata (title, etc.)
    - Extracts textual content
    - Extracts figures/images
    """

    def __init__(self, pdf_path: str, output_dir: str = "storage/processed"):
        self.pdf_path = Path(pdf_path)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.doc = fitz.open(pdf_path)

    def extract_text(self) -> str:
        """Extract raw text from PDF pages."""
        text_content = []
        for page_num, page in enumerate(self.doc):
            text = page.get_text("text")
            if text.strip():
                text_content.append(text)
        return "\n".join(text_content)

    def extract_images(self, max_images: int = 20) -> List[str]:
        """
        Extracts figures/images from the PDF.
        Saves them into `output_dir/images/`.
        Returns list of image file paths.
        """
        images_dir = self.output_dir / "images"
        images_dir.mkdir(parents=True, exist_ok=True)

        saved_files = []
        img_count = 0

        for page_index, page in enumerate(self.doc):
            images = page.get_images(full=True)
            for img_index, img in enumerate(images):
                xref = img[0]
                pix = fitz.Pixmap(self.doc, xref)

                if pix.n - pix.alpha < 4:  # RGB or CMYK
                    img_path = images_dir / f"page{page_index+1}_img{img_index+1}.png"
                    pix.save(img_path)
                else:  # Convert CMYK to RGB
                    pix_converted = fitz.Pixmap(fitz.csRGB, pix)
                    img_path = images_dir / f"page{page_index+1}_img{img_index+1}.png"
                    pix_converted.save(img_path)
                    pix_converted = None

                saved_files.append(str(img_path))
                img_count += 1
                if img_count >= max_images:
                    return saved_files
        return saved_files

    def process(self) -> Dict[str, Any]:
        """
        Run the full preprocessing pipeline:
        - Extract text
        - Extract images
        - Save results to disk
        """
        text = self.extract_text()

        text_file = self.output_dir / f"{self.pdf_path.stem}_text.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(text)

        images = self.extract_images()

        return {
            "paper_id": self.pdf_path.stem,
            "text_file": str(text_file),
            "images": images,
        }


if __name__ == "__main__":
    pdf_path = "storage/raw/Whats_Left_Concept_Grounding.pdf"  
    processor = PaperPreprocessor(pdf_path)
    result = processor.process()
    print(result)
