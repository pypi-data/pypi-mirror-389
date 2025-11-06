use pdf_oxide::PdfDocument;

fn main() {
    let path = "test_datasets/pdfs/mixed/XYUJKKMUXDLLC6JTCXEWHK5ZMNSTPHF6.pdf";
    let mut doc = PdfDocument::open(path).unwrap();
    let text = doc.extract_text(0).unwrap();
    println!("{}", text);
}
