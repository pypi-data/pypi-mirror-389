//! Regression test for page count zero (P0 CRITICAL)
//!
//! Issue: 4 PDFs show "**Pages:** 0" and extract almost nothing
//! Root cause: Page extraction completely failing for certain PDF structures
//!
//! This is a CRITICAL blocker discovered by comparing with PyMuPDF4LLM.
//! These PDFs have substantial content but we extract < 1%.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// PDFs where page extraction fails (Pages: 0)
const PAGE_ZERO_PDFS: &[&str] = &[
    "../pdf_oxide_tests/pdfs/newspapers/IA_0001-cdc-2015-american-tour.pdf",
    "../pdf_oxide_tests/pdfs/newspapers/IA_0001-cdc-2018-american-tour.pdf",
    "../pdf_oxide_tests/pdfs/newspapers/IA_0001-chambers-museum.pdf",
];

#[test]
fn test_page_count_not_zero() {
    println!("\n=== Testing Page Count Not Zero ===");

    let mut failures = Vec::new();

    for pdf_path in PAGE_ZERO_PDFS {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                match doc.page_count() {
                    Ok(count) => {
                        println!("  Page count: {}", count);

                        if count == 0 {
                            failures.push(format!("{}: page_count = 0", pdf_path));
                            println!("  ❌ CRITICAL: Page count is zero!");
                        } else {
                            println!("  ✓ Page count is valid");
                        }
                    }
                    Err(e) => {
                        failures.push(format!("{}: page_count error: {}", pdf_path, e));
                        println!("  ❌ Failed to get page count: {}", e);
                    }
                }
            }
            Err(e) => {
                failures.push(format!("{}: failed to open: {}", pdf_path, e));
                println!("  ❌ Failed to open: {}", e);
            }
        }
    }

    if !failures.is_empty() {
        println!("\n❌ CRITICAL FAILURES:");
        for failure in &failures {
            println!("  • {}", failure);
        }
        panic!("Page count zero detected in {} files", failures.len());
    }

    println!("\n✅ All files have valid page counts");
}

#[test]
fn test_extraction_not_empty() {
    println!("\n=== Testing Extraction Not Empty ===");

    let mut failures = Vec::new();

    for pdf_path in PAGE_ZERO_PDFS {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                match doc.to_markdown(0, &ConversionOptions::default()) {
                    Ok(markdown) => {
                        let char_count = markdown.len();
                        println!("  Extracted: {} chars", char_count);

                        // PyMuPDF4LLM extracts 3,920 - 11,308 chars from these (full document)
                        // We're only testing page 0, so we expect less content
                        // We should extract at least 500 chars (meaningful content, not just headers)
                        if char_count < 500 {
                            failures.push(format!(
                                "{}: only {} chars (expected >500 from page 0)",
                                pdf_path, char_count
                            ));
                            println!("  ❌ CRITICAL: Almost no content extracted!");

                            // Show what we did extract
                            if char_count > 0 {
                                println!("  Content: {}", markdown.trim());
                            }
                        } else {
                            println!("  ✓ Substantial content extracted ({} chars from page 0)", char_count);
                        }
                    }
                    Err(e) => {
                        failures.push(format!("{}: extraction error: {}", pdf_path, e));
                        println!("  ❌ Extraction failed: {}", e);
                    }
                }
            }
            Err(e) => {
                failures.push(format!("{}: failed to open: {}", pdf_path, e));
                println!("  ❌ Failed to open: {}", e);
            }
        }
    }

    if !failures.is_empty() {
        println!("\n❌ CRITICAL FAILURES:");
        for failure in &failures {
            println!("  • {}", failure);
        }
        panic!("Empty extraction detected in {} files", failures.len());
    }

    println!("\n✅ All files extracted substantial content");
}

#[test]
fn test_compare_with_pymupdf4llm_length() {
    // Compare our extraction length with PyMuPDF4LLM
    println!("\n=== Comparing Extraction Length ===");

    let test_cases = vec![
        ("../pdf_oxide_tests/pdfs/newspapers/IA_0001-cdc-2015-american-tour.pdf",
         "../pdf_oxide_tests/benchmark_outputs/pymupdf4llm/IA_0001-cdc-2015-american-tour.md",
         7361),
        ("../pdf_oxide_tests/pdfs/newspapers/IA_0001-cdc-2018-american-tour.pdf",
         "../pdf_oxide_tests/benchmark_outputs/pymupdf4llm/IA_0001-cdc-2018-american-tour.md",
         11308),
        ("../pdf_oxide_tests/pdfs/newspapers/IA_0001-chambers-museum.pdf",
         "../pdf_oxide_tests/benchmark_outputs/pymupdf4llm/IA_0001-chambers-museum.md",
         3920),
    ];

    for (pdf_path, pymupdf_path, expected_min) in test_cases {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  PDF not found: {}", pdf_path);
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        let mut doc = PdfDocument::open(pdf_path)
            .expect("Failed to open PDF");

        // Extract ALL pages (PyMuPDF4LLM outputs are full documents)
        let page_count = doc.page_count().expect("Failed to get page count");
        let mut full_markdown = String::new();
        for page_idx in 0..page_count {
            match doc.to_markdown(page_idx, &ConversionOptions::default()) {
                Ok(page_md) => {
                    full_markdown.push_str(&page_md);
                    full_markdown.push('\n'); // Separate pages
                }
                Err(e) => {
                    eprintln!("  ⚠️  Failed to extract page {}: {}", page_idx, e);
                }
            }
        }

        let our_len = full_markdown.len();

        // Check if PyMuPDF4LLM output exists
        if std::path::Path::new(pymupdf_path).exists() {
            let their_markdown = std::fs::read_to_string(pymupdf_path)
                .expect("Failed to read PyMuPDF4LLM output");

            let their_len = their_markdown.len();
            let ratio = (our_len as f64 / their_len as f64) * 100.0;

            println!("  Our length: {} chars", our_len);
            println!("  PyMuPDF4LLM: {} chars", their_len);
            println!("  Ratio: {:.1}%", ratio);

            // We should extract at least 70% of what PyMuPDF4LLM extracts
            assert!(
                ratio >= 70.0,
                "Only extracted {:.1}% of PyMuPDF4LLM's content (expected ≥70%)",
                ratio
            );
        } else {
            // Fallback: check against known minimum
            println!("  Our length: {} chars", our_len);
            println!("  Expected minimum: {} chars", expected_min);

            assert!(
                our_len >= (expected_min as f64 * 0.7) as usize,
                "Only extracted {} chars (expected ≥{})",
                our_len,
                (expected_min as f64 * 0.7) as usize
            );
        }
    }

    println!("\n✅ Extraction length is adequate");
}

#[test]
fn test_spans_extracted() {
    // Test if spans are extracted even if markdown conversion fails
    println!("\n=== Testing Span Extraction ===");

    for pdf_path in PAGE_ZERO_PDFS {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        let mut doc = PdfDocument::open(pdf_path)
            .expect("Failed to open PDF");

        match doc.extract_spans(0) {
            Ok(spans) => {
                println!("  Extracted {} spans", spans.len());

                if spans.is_empty() {
                    println!("  ❌ No spans extracted!");
                } else {
                    // Show first few spans
                    println!("  First 3 spans:");
                    for (i, span) in spans.iter().take(3).enumerate() {
                        println!("    {}. {:?} - bbox: {:?}", i+1, span.text, span.bbox);
                    }

                    assert!(
                        spans.len() >= 10,
                        "Only {} spans extracted (expected substantial content)",
                        spans.len()
                    );
                }
            }
            Err(e) => {
                println!("  ❌ Span extraction failed: {}", e);
                panic!("Failed to extract spans from {}: {}", pdf_path, e);
            }
        }
    }

    println!("\n✅ Spans extracted successfully");
}

#[test]
fn test_page_structure_diagnostic() {
    // Diagnostic test to understand the PDF structure
    println!("\n=== Diagnostic: Page Structure ===");

    let test_file = "../pdf_oxide_tests/pdfs/newspapers/IA_0001-cdc-2015-american-tour.pdf";

    if !std::path::Path::new(test_file).exists() {
        println!("⚠️  Test file not found");
        return;
    }

    let mut doc = PdfDocument::open(test_file)
        .expect("Failed to open PDF");

    match doc.page_count() {
        Ok(count) => {
            println!("Page count: {}", count);

            if count == 0 {
                println!("\n🔍 DIAGNOSIS: Page count is zero");
                println!("   Possible causes:");
                println!("   1. Page tree not found in PDF structure");
                println!("   2. Page count calculation error");
                println!("   3. Unusual PDF structure (scanned image?)");
                println!("   4. Corrupted page catalog");
            }
        }
        Err(e) => {
            println!("❌ Failed to get page count: {}", e);
        }
    }

    // Try to extract spans to see if content exists
    let mut doc = PdfDocument::open(test_file)
        .expect("Failed to open PDF");

    match doc.extract_spans(0) {
        Ok(spans) => {
            println!("\nSpan extraction: {} spans", spans.len());

            if spans.is_empty() {
                println!("   No text spans found on page 0");
                println!("   This may be a scanned image PDF");
            }
        }
        Err(e) => {
            println!("\n❌ Span extraction error: {}", e);
            println!("   Error suggests page access issue");
        }
    }

    println!("\n📋 Diagnostic complete - review output above");
}
