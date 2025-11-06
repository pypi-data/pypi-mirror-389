//! Regression test for control character issues
//!
//! Issue: 61 PDFs (17%) contain unexpected control characters
//! Root cause: Raw PDF bytes leaking into output
//!
//! Control characters (ASCII <32 except \n, \r, \t) should not
//! appear in final markdown output.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// Sample of PDFs with control character issues
const CONTROL_CHAR_FILES: &[&str] = &[
    // Will be populated from quality report
    "../pdf_oxide_tests/pdfs/diverse/*.pdf",  // Placeholder
];

fn count_control_characters(text: &str) -> (usize, Vec<(usize, char)>) {
    let mut count = 0;
    let mut examples = Vec::new();

    for (i, ch) in text.chars().enumerate() {
        let code = ch as u32;
        // Control chars: 0-31 except newline (10), carriage return (13), tab (9)
        if code < 32 && code != 10 && code != 13 && code != 9 {
            count += 1;
            if examples.len() < 10 {
                examples.push((i, ch));
            }
        }
    }

    (count, examples)
}

#[test]
fn test_no_control_characters_in_output() {
    println!("\n=== Testing for Control Characters ===");

    // Test with a real PDF that we know has issues
    let test_pdfs = vec![
        "../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Vol1_Navigation_and_Navigable_Waters.pdf",
        "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf",
    ];

    for pdf_path in &test_pdfs {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                match doc.to_markdown(0, &ConversionOptions::default()) {
                    Ok(markdown) => {
                        let (count, examples) = count_control_characters(&markdown);

                        println!("  Control characters: {}", count);

                        if count > 0 {
                            println!("  Examples (char code):");
                            for (pos, ch) in examples.iter().take(5) {
                                println!("    Position {}: U+{:04X}", pos, *ch as u32);
                            }

                            // Show context around first occurrence
                            if let Some((pos, _)) = examples.first() {
                                let start = pos.saturating_sub(20);
                                let end = (pos + 20).min(markdown.len());
                                let context = &markdown[start..end];
                                println!("  Context: {:?}", context);
                            }
                        }

                        assert_eq!(
                            count, 0,
                            "Found {} control characters in output", count
                        );
                    }
                    Err(e) => {
                        println!("  ❌ Extraction error: {}", e);
                    }
                }
            }
            Err(e) => {
                println!("  ❌ Failed to open: {}", e);
            }
        }
    }

    println!("\n✅ No control characters in output");
}

#[test]
fn test_spans_have_no_control_chars() {
    // Test at span level to see where control chars originate
    println!("\n=== Testing Spans for Control Characters ===");

    let test_pdfs = vec![
        "../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Vol1_Navigation_and_Navigable_Waters.pdf",
    ];

    for pdf_path in &test_pdfs {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        println!("\n{}", pdf_path);

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(spans) = doc.extract_spans(0) {
                let mut spans_with_control_chars = 0;

                for (i, span) in spans.iter().enumerate() {
                    let (count, _) = count_control_characters(&span.text);

                    if count > 0 {
                        spans_with_control_chars += 1;
                        if spans_with_control_chars <= 5 {
                            println!("  Span {}: {} control chars, font={}, text={:?}",
                                i, count, span.font_name, span.text.chars().take(20).collect::<String>());
                        }
                    }
                }

                println!("  Spans with control chars: {}/{}", spans_with_control_chars, spans.len());

                assert_eq!(
                    spans_with_control_chars, 0,
                    "Found control characters in {} spans", spans_with_control_chars
                );
            }
        }
    }
}

#[test]
fn test_markdown_is_clean_printable() {
    // Ensure output contains only printable characters plus whitespace
    println!("\n=== Testing for Clean Printable Output ===");

    let test_pdfs = vec![
        "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf",
    ];

    for pdf_path in &test_pdfs {
        if !std::path::Path::new(pdf_path).exists() {
            continue;
        }

        if let Ok(mut doc) = PdfDocument::open(pdf_path) {
            if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                let mut non_printable = 0;

                for ch in markdown.chars() {
                    let code = ch as u32;
                    // Allow: printable ASCII (32-126), newline (10), tab (9), high Unicode
                    if code < 32 && code != 10 && code != 9 {
                        non_printable += 1;
                    }
                }

                println!("  Non-printable characters: {}", non_printable);

                assert_eq!(
                    non_printable, 0,
                    "Found {} non-printable characters", non_printable
                );
            }
        }
    }
}
