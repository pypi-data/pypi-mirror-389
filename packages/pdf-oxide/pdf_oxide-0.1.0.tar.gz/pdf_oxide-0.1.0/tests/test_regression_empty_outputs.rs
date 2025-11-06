//! Regression test for empty/minimal output failures
//!
//! Issue: 11 PDFs (3%) produce <100 characters of output
//! Root cause: Complete extraction failure on certain PDF types
//!
//! These PDFs should produce meaningful output but currently fail.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// PDFs that produce empty or minimal output (< 100 chars)
const EMPTY_OUTPUT_FILES: &[&str] = &[
    "../pdf_oxide_tests/benchmark_outputs/pdf_oxide/diverse/WXURHXHVCOCL3XIN4PFUPT2OGYFIXYR5.md",
    "../pdf_oxide_tests/benchmark_outputs/pdf_oxide/diverse/5JWNPTKTIAPTHTEGVKW7WVNBDBKQMRJO.md",
    "../pdf_oxide_tests/benchmark_outputs/pdf_oxide/diverse/QJRUY4FRCDHXZJT5ZAWKMADAMAQUP5R6.md",
    "../pdf_oxide_tests/benchmark_outputs/pdf_oxide/diverse/D45G6SVN7QZSMYJOJGWLKE3MJ6DHTYY5.md",
    "../pdf_oxide_tests/benchmark_outputs/pdf_oxide/diverse/ZC2ELDSYWFVOJZRXTLERXVM7UMXWCWZN.md",
];

/// Map markdown filename back to PDF filename
fn get_pdf_path(md_filename: &str) -> Option<String> {
    // Extract the base name from markdown path
    let base_name = std::path::Path::new(md_filename)
        .file_stem()?
        .to_str()?;

    // Search for corresponding PDF in test_datasets
    let search_paths = vec![
        format!("../pdf_oxide_tests/pdfs/diverse/{}.pdf", base_name),
        format!("../pdf_oxide_tests/pdfs/government/{}.pdf", base_name),
        format!("../pdf_oxide_tests/pdfs/academic/{}.pdf", base_name),
        format!("../pdf_oxide_tests/pdfs/forms/{}.pdf", base_name),
    ];

    for path in search_paths {
        if std::path::Path::new(&path).exists() {
            return Some(path);
        }
    }

    None
}

#[test]
fn test_empty_output_files_have_content() {
    let mut failures = Vec::new();
    let mut checked = 0;

    println!("\n=== Testing Empty Output PDFs ===");

    for md_file in EMPTY_OUTPUT_FILES {
        if let Some(pdf_path) = get_pdf_path(md_file) {
            println!("\nChecking: {}", pdf_path);
            checked += 1;

            match PdfDocument::open(&pdf_path) {
                Ok(mut doc) => {
                    let page_count = doc.page_count().unwrap_or(0);
                    println!("  Pages: {}", page_count);

                    if page_count == 0 {
                        failures.push(format!("{}: No pages found", pdf_path));
                        continue;
                    }

                    // Try extracting first page
                    match doc.to_markdown(0, &ConversionOptions::default()) {
                        Ok(markdown) => {
                            let char_count = markdown.len();
                            println!("  Extracted: {} chars", char_count);

                            if char_count < 100 {
                                failures.push(format!(
                                    "{}: Only {} chars extracted (expected >100)",
                                    pdf_path, char_count
                                ));

                                // Save output for debugging
                                let debug_path = format!("/tmp/empty_output_{}.md",
                                    std::path::Path::new(&pdf_path)
                                        .file_stem().unwrap()
                                        .to_str().unwrap());
                                let _ = std::fs::write(&debug_path, &markdown);
                                println!("  Saved debug output to: {}", debug_path);
                            } else {
                                println!("  ✓ Has sufficient content");
                            }
                        }
                        Err(e) => {
                            failures.push(format!("{}: Extraction error: {}", pdf_path, e));
                        }
                    }
                }
                Err(e) => {
                    failures.push(format!("{}: Failed to open: {}", pdf_path, e));
                }
            }
        } else {
            println!("⚠️  Could not find PDF for: {}", md_file);
        }
    }

    println!("\n=== Summary ===");
    println!("Checked: {}/{} files", checked, EMPTY_OUTPUT_FILES.len());
    println!("Failures: {}", failures.len());

    if !failures.is_empty() {
        println!("\n❌ FAILURES:");
        for failure in &failures {
            println!("  • {}", failure);
        }
        panic!("Empty output test failed for {} files", failures.len());
    }

    println!("✅ All files produce adequate output");
}

#[test]
fn test_empty_outputs_have_spans() {
    println!("\n=== Testing Span Extraction ===");

    let mut failures = Vec::new();
    let mut checked = 0;

    for md_file in EMPTY_OUTPUT_FILES {
        if let Some(pdf_path) = get_pdf_path(md_file) {
            checked += 1;

            if let Ok(mut doc) = PdfDocument::open(&pdf_path) {
                match doc.extract_spans(0) {
                    Ok(spans) => {
                        println!("\n{}: {} spans", pdf_path, spans.len());

                        if spans.is_empty() {
                            failures.push(format!("{}: No spans extracted", pdf_path));
                        } else {
                            // Show first few spans
                            println!("  First spans:");
                            for (i, span) in spans.iter().take(5).enumerate() {
                                println!("    {}: {:?}", i, span.text);
                            }
                        }
                    }
                    Err(e) => {
                        failures.push(format!("{}: Span extraction error: {}", pdf_path, e));
                    }
                }
            }
        }
    }

    println!("\n=== Summary ===");
    println!("Checked: {}/{} files", checked, EMPTY_OUTPUT_FILES.len());

    if !failures.is_empty() {
        println!("\n❌ FAILURES:");
        for failure in &failures {
            println!("  • {}", failure);
        }
        panic!("Span extraction failed for {} files", failures.len());
    }

    println!("✅ All files have extractable spans");
}

#[test]
fn test_empty_outputs_minimum_chars() {
    // This test will fail initially - it documents the expected behavior
    let min_expected_chars = 500; // Reasonable minimum for a real PDF page

    for md_file in EMPTY_OUTPUT_FILES.iter().take(1) {  // Start with just one
        if let Some(pdf_path) = get_pdf_path(md_file) {
            if let Ok(mut doc) = PdfDocument::open(&pdf_path) {
                if let Ok(markdown) = doc.to_markdown(0, &ConversionOptions::default()) {
                    assert!(
                        markdown.len() >= min_expected_chars,
                        "PDF {} produced only {} chars, expected at least {}",
                        pdf_path, markdown.len(), min_expected_chars
                    );
                }
            }
        }
    }
}
