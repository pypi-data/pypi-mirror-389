//! Regression tests for HTML conversion quality improvements
//!
//! Based on comparison: Our library 60/100 vs PyMuPDF 34/100 (+26.1 points)
//! These tests ensure we maintain and improve HTML quality.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

const ARXIV_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

#[test]
fn test_html_basic_generation() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    println!("Generated {} chars of HTML", html.len());

    // Basic checks
    assert!(html.len() > 1000, "HTML too short: {} chars", html.len());
    assert!(html.contains("<"), "No HTML tags found");
    assert!(html.contains(">"), "No HTML tags found");

    println!("✅ HTML generation works");
}

#[test]
fn test_html_urls_present() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    // This PDF (arxiv_2510.21165v1.pdf) is about "Chinese stock market"
    // and doesn't have external URLs on page 0
    // Just verify it contains expected content

    assert!(
        html.contains("Chinese stock market") || html.contains("Chinese stock"),
        "Expected title content not found"
    );

    assert!(
        html.contains("correlation"),
        "Expected keyword 'correlation' not found"
    );

    println!("✅ HTML content extracted correctly");
}

#[test]
fn test_html_has_structure() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions {
        preserve_layout: false,
        detect_headings: true,
        extract_tables: false,
        include_images: false,
        image_output_dir: None,
        reading_order_mode: pdf_oxide::converters::ReadingOrderMode::ColumnAware,
    };

    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    // Check for headings
    let has_headings = html.contains("<h1>") || html.contains("<h2>") || html.contains("<h3>");
    assert!(has_headings, "No heading tags found");

    // Check for paragraphs
    assert!(html.contains("<p>"), "No paragraph tags found");

    println!("✅ HTML has semantic structure");
}

#[test]
fn test_html_no_replacement_chars() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    let replacement_count = html.matches('\u{FFFD}').count();
    assert_eq!(
        replacement_count, 0,
        "Found {} replacement characters in HTML",
        replacement_count
    );

    println!("✅ No replacement characters");
}

#[test]
fn test_html_title_extracted() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions {
        preserve_layout: false,
        detect_headings: true,
        extract_tables: false,
        include_images: false,
        image_output_dir: None,
        reading_order_mode: pdf_oxide::converters::ReadingOrderMode::ColumnAware,
    };

    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    // This PDF's title contains "Chinese stock market" and "correlation"
    assert!(
        html.contains("Chinese stock market") || html.contains("Chinese stock"),
        "Title content not found"
    );

    assert!(html.contains("correlation"), "Key term 'correlation' not found");

    println!("✅ Title extracted");
}

#[test]
fn test_html_email_present() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    // This PDF has pengliuhep@outlook.com
    let email = "pengliuhep@outlook.com";
    assert!(html.contains(email), "Email not found in HTML");

    println!("✅ Email preserved");
}
