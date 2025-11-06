//! Regression test for missing content (>50% loss)
//!
//! Issue: 24 PDFs (6.7%) extract <50% of PyMuPDF4LLM's content
//! Root cause: Unknown - needs page-by-page investigation
//!
//! This is a P1 HIGH issue discovered by comparing with PyMuPDF4LLM.
//! Unacceptable data loss for production use.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// PDFs where we extract <50% of content
const CONTENT_LOSS_PDFS: &[(&str, usize)] = &[
    ("../pdf_oxide_tests/pdfs/theses/Berkeley_Thesis_Theory_1.pdf", 36140),
    ("../pdf_oxide_tests/pdfs/diverse/EMMM5FRYBCPVBLVU4RY6OFEKZFWM2KIJ.pdf", 13569),
    ("../pdf_oxide_tests/pdfs/diverse/QRJ42GGGA52M42R57XTGIQONYKAKWVG5.pdf", 25000), // Approximate
];

#[test]
fn test_no_major_content_loss() {
    println!("\n=== Testing for Major Content Loss ===");

    let mut failures = Vec::new();

    for (pdf_path, expected_len) in CONTENT_LOSS_PDFS {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                match doc.to_markdown(0, &ConversionOptions::default()) {
                    Ok(markdown) => {
                        let our_len = markdown.len();
                        let ratio = (our_len as f64 / *expected_len as f64) * 100.0;

                        println!("  Our length: {} chars", our_len);
                        println!("  PyMuPDF4LLM: {} chars", expected_len);
                        println!("  Ratio: {:.1}%", ratio);

                        if ratio < 50.0 {
                            failures.push(format!(
                                "{}: {:.1}% of expected content",
                                pdf_path, ratio
                            ));
                            println!("  ❌ CRITICAL: Only {:.1}% extracted!", ratio);
                        } else if ratio < 70.0 {
                            println!("  ⚠️  Only {:.1}% extracted (acceptable but not ideal)", ratio);
                        } else {
                            println!("  ✓ Adequate content extracted ({:.1}%)", ratio);
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
        println!("\n❌ CONTENT LOSS FAILURES:");
        for failure in &failures {
            println!("  • {}", failure);
        }
        panic!("Major content loss detected in {} files", failures.len());
    }

    println!("\n✅ No major content loss detected");
}

#[test]
fn test_compare_with_pymupdf4llm() {
    // Direct comparison with PyMuPDF4LLM outputs
    println!("\n=== Comparing with PyMuPDF4LLM Outputs ===");

    let test_cases = vec![
        (
            "../pdf_oxide_tests/pdfs/theses/Berkeley_Thesis_Theory_1.pdf",
            "../pdf_oxide_tests/benchmark_outputs/pymupdf4llm/Berkeley_Thesis_Theory_1.md"
        ),
        (
            "../pdf_oxide_tests/pdfs/diverse/EMMM5FRYBCPVBLVU4RY6OFEKZFWM2KIJ.pdf",
            "../pdf_oxide_tests/benchmark_outputs/pymupdf4llm/EMMM5FRYBCPVBLVU4RY6OFEKZFWM2KIJ.md"
        ),
    ];

    for (pdf_path, pymupdf_path) in test_cases {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  PDF not found: {}", pdf_path);
            continue;
        }

        if !std::path::Path::new(pymupdf_path).exists() {
            println!("⚠️  PyMuPDF4LLM output not found: {}", pymupdf_path);
            continue;
        }

        println!("\nComparing: {}", pdf_path);

        let mut doc = PdfDocument::open(pdf_path)
            .expect("Failed to open PDF");

        let our_markdown = doc.to_markdown(0, &ConversionOptions::default())
            .expect("Failed to extract markdown");

        let their_markdown = std::fs::read_to_string(pymupdf_path)
            .expect("Failed to read PyMuPDF4LLM output");

        let our_len = our_markdown.len();
        let their_len = their_markdown.len();
        let ratio = (our_len as f64 / their_len as f64) * 100.0;

        println!("  Our length: {} chars", our_len);
        println!("  PyMuPDF4LLM: {} chars", their_len);
        println!("  Ratio: {:.1}%", ratio);

        // Minimum acceptable: 70% of PyMuPDF4LLM
        assert!(
            ratio >= 70.0,
            "Only extracted {:.1}% of PyMuPDF4LLM's content (expected ≥70%)",
            ratio
        );

        println!("  ✓ Content extraction adequate");
    }

    println!("\n✅ All comparisons passed");
}

#[test]
fn test_multipage_extraction() {
    // Test if content loss is on first page or across all pages
    println!("\n=== Testing Multi-Page Extraction ===");

    let test_file = "../pdf_oxide_tests/pdfs/theses/Berkeley_Thesis_Theory_1.pdf";

    if !std::path::Path::new(test_file).exists() {
        println!("⚠️  Test file not found");
        return;
    }

    let mut doc = PdfDocument::open(test_file)
        .expect("Failed to open PDF");

    let page_count = doc.page_count()
        .expect("Failed to get page count");

    println!("PDF has {} pages", page_count);

    // Extract first 5 pages
    let pages_to_check = 5.min(page_count);

    for page_num in 0..pages_to_check {
        let mut doc = PdfDocument::open(test_file)
            .expect("Failed to open PDF");

        match doc.to_markdown(page_num, &ConversionOptions::default()) {
            Ok(markdown) => {
                println!("  Page {}: {} chars", page_num, markdown.len());

                if markdown.len() < 100 {
                    println!("    ⚠️  Very little content on this page");
                }
            }
            Err(e) => {
                println!("  Page {}: ❌ extraction error: {}", page_num, e);
            }
        }
    }

    println!("\n📋 Review per-page extraction above");
}

#[test]
fn test_span_count_vs_content() {
    // Check if low character count is due to span extraction issues
    println!("\n=== Testing Span Count vs Content Length ===");

    for (pdf_path, _) in CONTENT_LOSS_PDFS.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        let mut doc = PdfDocument::open(pdf_path)
            .expect("Failed to open PDF");

        match doc.extract_spans(0) {
            Ok(spans) => {
                let span_count = spans.len();
                let total_chars: usize = spans.iter().map(|s| s.text.len()).sum();

                println!("  Span count: {}", span_count);
                println!("  Total chars in spans: {}", total_chars);

                // Now get markdown
                let mut doc = PdfDocument::open(pdf_path)
                    .expect("Failed to open PDF");

                let markdown = doc.to_markdown(0, &ConversionOptions::default())
                    .expect("Failed to extract markdown");

                let markdown_len = markdown.len();

                println!("  Markdown length: {}", markdown_len);
                println!("  Conversion ratio: {:.1}%", (markdown_len as f64 / total_chars as f64) * 100.0);

                if span_count < 100 {
                    println!("  ⚠️  Very few spans extracted");
                    println!("      This may indicate span extraction issue");
                }

                if markdown_len < total_chars * 50 / 100 {
                    println!("  ⚠️  Markdown much shorter than spans");
                    println!("      This may indicate conversion issue");
                }
            }
            Err(e) => {
                println!("  ❌ Span extraction failed: {}", e);
            }
        }
    }

    println!("\n📋 Diagnostic complete");
}

#[test]
fn test_word_count_comparison() {
    // Compare word count with PyMuPDF4LLM
    println!("\n=== Testing Word Count ===");

    let test_cases = vec![
        (
            "../pdf_oxide_tests/pdfs/diverse/EMMM5FRYBCPVBLVU4RY6OFEKZFWM2KIJ.pdf",
            "../pdf_oxide_tests/benchmark_outputs/pymupdf4llm/EMMM5FRYBCPVBLVU4RY6OFEKZFWM2KIJ.md"
        ),
    ];

    for (pdf_path, pymupdf_path) in test_cases {
        if !std::path::Path::new(pdf_path).exists() || !std::path::Path::new(pymupdf_path).exists() {
            println!("⚠️  Files not found");
            continue;
        }

        println!("\nComparing: {}", pdf_path);

        let mut doc = PdfDocument::open(pdf_path)
            .expect("Failed to open PDF");

        let our_markdown = doc.to_markdown(0, &ConversionOptions::default())
            .expect("Failed to extract markdown");

        let their_markdown = std::fs::read_to_string(pymupdf_path)
            .expect("Failed to read PyMuPDF4LLM output");

        let our_words = our_markdown.split_whitespace().count();
        let their_words = their_markdown.split_whitespace().count();
        let ratio = (our_words as f64 / their_words as f64) * 100.0;

        println!("  Our word count: {}", our_words);
        println!("  PyMuPDF4LLM: {}", their_words);
        println!("  Ratio: {:.1}%", ratio);

        if ratio < 70.0 {
            println!("  ❌ Missing {:.1}% of words", 100.0 - ratio);
        } else {
            println!("  ✓ Adequate word count");
        }
    }
}

#[test]
#[ignore] // Enable for detailed debugging
fn test_save_comparison_outputs() {
    // Save both outputs for manual comparison
    println!("\n=== Saving Outputs for Comparison ===");

    let test_file = "../pdf_oxide_tests/pdfs/theses/Berkeley_Thesis_Theory_1.pdf";

    if !std::path::Path::new(test_file).exists() {
        println!("⚠️  Test file not found");
        return;
    }

    let mut doc = PdfDocument::open(test_file)
        .expect("Failed to open PDF");

    let our_markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to extract markdown");

    std::fs::write("/tmp/berkeley_thesis_our_output.md", &our_markdown)
        .expect("Failed to write output");

    println!("✓ Our output saved to: /tmp/berkeley_thesis_our_output.md");

    // Copy PyMuPDF4LLM output for comparison
    let pymupdf_path = "../pdf_oxide_tests/benchmark_outputs/pymupdf4llm/Berkeley_Thesis_Theory_1.md";
    if std::path::Path::new(pymupdf_path).exists() {
        std::fs::copy(pymupdf_path, "/tmp/berkeley_thesis_pymupdf_output.md")
            .expect("Failed to copy PyMuPDF4LLM output");

        println!("✓ PyMuPDF4LLM output copied to: /tmp/berkeley_thesis_pymupdf_output.md");
        println!("\nCompare with:");
        println!("  diff /tmp/berkeley_thesis_our_output.md /tmp/berkeley_thesis_pymupdf_output.md");
    }
}
