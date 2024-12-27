import argparse
import os
import pymupdf
from pathlib import Path


def extract(pdf_path, page_range, pdf_folder):
    doc = pymupdf.open(pdf_path)

    for page_num in page_range:
        if page_num < 0 or page_num >= len(doc):
            print(f"Page {page_num} is out of range. Skipping.")
            continue
        page = doc.load_page(page_num)
        pix = page.get_pixmap(dpi=300)  # High DPI for quality
        filename = Path(pdf_path).stem
        img_path = os.path.join(pdf_folder, f"{filename}_p{page_num+1:04}.png")
        pix.save(img_path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Used to find the optimal arguments to the dataloader"
    )
    parser.add_argument("infile", help="Relative path to the PDF file")
    parser.add_argument("start", help="The first page number to extract", type=int)
    parser.add_argument("end", help="The last page number to extract", type=int)
    parser.add_argument("outdir", help="Where to put the output")

    args = parser.parse_args()

    start = args.start - 1
    end = args.end - 1

    page_range = range(start, end + 1)

    extract(args.infile, page_range, args.outdir)
