import argparse
from pathlib import Path

PDF_OBJECTS = [
    b"<< /Type /Catalog /Pages 2 0 R >>",
    b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
    b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
    b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
]


def pdf_bytes(label):
    content = f"BT /F1 12 Tf 72 720 Td ({label}) Tj ET".encode("ascii")
    objects = PDF_OBJECTS + [
        b"<< /Length " + str(len(content)).encode() + b" >>\nstream\n"
        + content
        + b"\nendstream"
    ]
    data = bytearray(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, start=1):
        offsets.append(len(data))
        data += f"{number} 0 obj\n".encode() + body + b"\nendobj\n"
    xref_offset = len(data)
    data += f"xref\n0 {len(objects) + 1}\n".encode()
    data += b"0000000000 65535 f \n"
    data += b"".join(f"{offset:010d} 00000 n \n".encode() for offset in offsets)
    data += (
        f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n"
        f"startxref\n{xref_offset}\n%%EOF\n"
    ).encode()
    return bytes(data)


def write_sample(folder, filename, label, extra_bytes=0):
    data = pdf_bytes(label)
    if extra_bytes:
        data += b"%" + b"0" * extra_bytes + b"\n"
    (folder / filename).write_bytes(data)


def generate(folder, oversized_mb):
    folder.mkdir(parents=True)
    write_sample(folder, "54_Name of the file.pdf", "Numeric prefix")
    write_sample(folder, "Name of the file.pdf", "No prefix")
    write_sample(folder, "DOS deed.pdf", "Deed of Sale")
    write_sample(folder, "alpha.pdf", "Alpha")
    write_sample(folder, "beta.pdf", "Beta")
    oversized_bytes = max(int(oversized_mb * 1024 * 1024), 1)
    write_sample(folder, "oversized.pdf", "Oversized", oversized_bytes)


def main():
    parser = argparse.ArgumentParser(description="Generate sample PDFs for release validation.")
    parser.add_argument("folder", type=Path, help="new folder to create")
    parser.add_argument("--oversized-mb", type=float, default=26)
    arguments = parser.parse_args()
    generate(arguments.folder, arguments.oversized_mb)
    print(f"Created sample PDFs in {arguments.folder}")


if __name__ == "__main__":
    main()
