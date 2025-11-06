use pdf_oxide::document::PdfDocument;

#[test]
fn analyze_arxiv_spans() {
    let mut doc = PdfDocument::open("../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf").unwrap();
    let spans = doc.extract_spans(0).unwrap();

    println!("\n=== TOTAL SPANS: {} ===\n", spans.len());

    // Find problematic spans
    println!("=== LOOKING FOR 'traditional' AND 'The' ===");
    for (i, span) in spans.iter().enumerate() {
        if span.text.to_lowercase().contains("traditional") || span.text == "The" {
            println!(
                "Span {}: text=\"{}\" | x={:.1} y={:.1} width={:.1}",
                i, span.text, span.bbox.x, span.bbox.y, span.bbox.width
            );
        }
    }

    // Look for missing spaces
    println!("\n=== CHECKING FOR MISSING SPACES ===");
    for (i, span) in spans.iter().enumerate().take(50) {
        if span.text.len() > 20 && !span.text.contains(' ') {
            println!(
                "Span {}: \"{}\" | x={:.1} y={:.1}",
                i,
                &span.text[..40.min(span.text.len())],
                span.bbox.x,
                span.bbox.y
            );
        }
    }

    // Show first 20 spans to understand structure
    println!("\n=== FIRST 20 SPANS ===");
    for (i, span) in spans.iter().enumerate().take(20) {
        println!(
            "Span {}: text=\"{}\" | x={:.1} y={:.1} width={:.1}",
            i, span.text, span.bbox.x, span.bbox.y, span.bbox.width
        );
    }
}
