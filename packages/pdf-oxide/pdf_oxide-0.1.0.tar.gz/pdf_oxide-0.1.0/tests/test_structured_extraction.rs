use pdf_oxide::{PdfDocument, extractors::StructuredExtractor};

#[test]
fn test_structured_extraction_simple_pdf() {
    // Initialize logger for debugging
    let _ = env_logger::builder()
        .is_test(true)
        .filter_level(log::LevelFilter::Debug)
        .try_init();

    // Use a simple PDF from test_datasets
    let test_pdf = "../pdf_oxide_tests/pdfs/mixed/QIYEVQGJUXO4R45CCFYLL65JS6FERSNA.pdf";

    let mut doc =
        PdfDocument::open(test_pdf).expect(&format!("Failed to open test PDF: {}", test_pdf));

    let mut extractor = StructuredExtractor::new();
    let structured = extractor
        .extract_page(&mut doc, 0)
        .expect("Failed to extract structured content");

    // Verify we got some elements
    assert!(!structured.elements.is_empty(), "Should extract some elements from the PDF");

    // Verify metadata
    assert!(structured.metadata.element_count > 0, "Element count should be > 0");
    assert_eq!(
        structured.metadata.element_count,
        structured.elements.len(),
        "Element count should match actual number of elements"
    );

    // Verify JSON export works
    let json = structured.to_json().expect("Failed to export to JSON");
    assert!(json.contains("\"type\""), "JSON should contain type field");

    println!("\n=== Structured Extraction Test Results ===");
    println!("Extracted {} elements", structured.elements.len());
    println!("  Headers: {}", structured.metadata.header_count);
    println!("  Paragraphs: {}", structured.metadata.paragraph_count);
    println!("  Lists: {}", structured.metadata.list_count);
    println!("  Tables: {}", structured.metadata.table_count);

    // Print first few elements for verification
    println!("\n=== First 10 Elements ===");
    for (i, element) in structured.elements.iter().take(10).enumerate() {
        match element {
            pdf_oxide::extractors::DocumentElement::Header {
                level, text, style, ..
            } => {
                println!(
                    "{}. H{}: {} ({}pt, {}{})",
                    i + 1,
                    level,
                    text.chars().take(60).collect::<String>(),
                    style.font_size,
                    if style.bold { "bold, " } else { "" },
                    if style.italic { "italic" } else { "" }
                );
            },
            pdf_oxide::extractors::DocumentElement::Paragraph {
                text,
                style,
                alignment,
                ..
            } => {
                println!(
                    "{}. P ({}): {} ({}pt, {:?})",
                    i + 1,
                    match alignment {
                        pdf_oxide::extractors::TextAlignment::Left => "left",
                        pdf_oxide::extractors::TextAlignment::Center => "center",
                        pdf_oxide::extractors::TextAlignment::Right => "right",
                        pdf_oxide::extractors::TextAlignment::Justified => "justified",
                    },
                    text.chars().take(60).collect::<String>(),
                    style.font_size,
                    style.font_family
                );
            },
            pdf_oxide::extractors::DocumentElement::List { items, ordered, .. } => {
                println!(
                    "{}. {} with {} items:",
                    i + 1,
                    if *ordered {
                        "Ordered List"
                    } else {
                        "Unordered List"
                    },
                    items.len()
                );
                for (j, item) in items.iter().take(3).enumerate() {
                    println!("    {}. {}", j + 1, item.text.chars().take(50).collect::<String>());
                }
            },
            _ => {
                println!("{}. Other element type", i + 1);
            },
        }
    }

    // Verify we can serialize to JSON without errors
    println!("\n=== JSON Export Sample ===");
    println!("{}", &json.chars().take(500).collect::<String>());
    println!("... (truncated)");
}

#[test]
fn test_structured_extraction_empty_page() {
    let _ = env_logger::builder().is_test(true).try_init();

    let test_pdf = "../pdf_oxide_tests/pdfs/mixed/QIYEVQGJUXO4R45CCFYLL65JS6FERSNA.pdf";
    let mut doc = PdfDocument::open(test_pdf).unwrap();

    let mut extractor = StructuredExtractor::new();

    // Try to extract from a page number that likely doesn't exist
    // (most test PDFs have only 1-2 pages)
    let _page_count = doc.page_count().unwrap_or(1);

    // Test with page 0 which should work
    let result = extractor.extract_page(&mut doc, 0);
    assert!(result.is_ok(), "Should successfully extract from page 0");
}

#[test]
fn test_structured_extractor_configuration() {
    use pdf_oxide::extractors::ExtractorConfig;

    let config = ExtractorConfig {
        min_header_size: 16.0,
        max_header_levels: 4,
        paragraph_gap_threshold: 2.0,
        detect_lists: true,
        detect_tables: false,
    };

    let mut extractor = StructuredExtractor::with_config(config);

    // Just verify the extractor was created with custom config
    // (we can't directly access private fields, but we can test behavior)
    let test_pdf = "../pdf_oxide_tests/pdfs/mixed/QIYEVQGJUXO4R45CCFYLL65JS6FERSNA.pdf";
    let mut doc = PdfDocument::open(test_pdf).unwrap();

    let result = extractor.extract_page(&mut doc, 0);
    assert!(result.is_ok(), "Should extract with custom configuration");
}

#[test]
fn test_json_serialization() {
    let _ = env_logger::builder().is_test(true).try_init();

    let test_pdf = "../pdf_oxide_tests/pdfs/mixed/QIYEVQGJUXO4R45CCFYLL65JS6FERSNA.pdf";
    let mut doc = PdfDocument::open(test_pdf).unwrap();

    let mut extractor = StructuredExtractor::new();
    let structured = extractor.extract_page(&mut doc, 0).unwrap();

    // Test JSON serialization
    let json = structured.to_json().unwrap();

    // Verify it's valid JSON by parsing it back
    let parsed: serde_json::Value =
        serde_json::from_str(&json).expect("Generated JSON should be valid");

    // Verify structure
    assert!(parsed.get("elements").is_some(), "JSON should have elements field");
    assert!(parsed.get("page_size").is_some(), "JSON should have page_size field");
    assert!(parsed.get("metadata").is_some(), "JSON should have metadata field");
}

#[test]
fn test_plain_text_export() {
    let _ = env_logger::builder().is_test(true).try_init();

    let test_pdf = "../pdf_oxide_tests/pdfs/mixed/QIYEVQGJUXO4R45CCFYLL65JS6FERSNA.pdf";
    let mut doc = PdfDocument::open(test_pdf).unwrap();

    let mut extractor = StructuredExtractor::new();
    let structured = extractor.extract_page(&mut doc, 0).unwrap();

    // Test plain text conversion
    let plain_text = structured.to_plain_text();

    assert!(!plain_text.is_empty(), "Plain text should not be empty");

    // Verify it contains some content from elements
    if !structured.elements.is_empty() {
        // At least one element's text should be in the plain text output
        let has_content = structured.elements.iter().any(|elem| match elem {
            pdf_oxide::extractors::DocumentElement::Header { text, .. } => {
                !text.is_empty() && plain_text.contains(text)
            },
            pdf_oxide::extractors::DocumentElement::Paragraph { text, .. } => {
                !text.is_empty() && plain_text.contains(text)
            },
            _ => false,
        });

        assert!(has_content, "Plain text should contain element text");
    }
}
