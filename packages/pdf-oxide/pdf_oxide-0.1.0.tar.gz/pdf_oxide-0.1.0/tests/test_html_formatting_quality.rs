//! HTML Formatting Quality Tests
//!
//! Comprehensive test suite for HTML conversion quality, similar to markdown tests.
//! Tests clickable links, semantic HTML structure, layout preservation, and overall quality.

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;
use regex::Regex;

/// Sample PDFs for testing (same as markdown tests for comparison)
const SAMPLE_PDFS: &[&str] = &[
    "../pdf_oxide_tests/pdfs/academic/arxiv_2312.00001v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2312.01234v1.pdf",
    "../pdf_oxide_tests/pdfs/government/cfr_sample.pdf",
    "../pdf_oxide_tests/pdfs/forms/irs_w4.pdf",
];

/// Test that URLs are converted to clickable HTML links
#[test]
fn test_html_url_links_clickable() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("Â   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    println!("\n=== HTML URL Links Test ===");
    println!("PDF: {}", pdf_path);
    println!("HTML length: {} bytes\n", html.len());

    // Expected clickable link pattern: <a href="https://...">https://...</a>
    let link_pattern = Regex::new(r#"<a\s+href="(https?://[^"]+)"[^>]*>.*?</a>"#).unwrap();
    let links: Vec<_> = link_pattern.captures_iter(&html).collect();

    println!("Found {} clickable links:", links.len());
    for (i, link) in links.iter().enumerate() {
        let url = &link[1];
        println!("  {}. {}", i + 1, url);
    }

    // Check for specific expected URLs
    let expected_urls = vec![
        "https://github.com/Fleeting-hyh/StreamingCoT",
        "https://doi.org/10.1145/3746027.3758311",
    ];

    let mut found_urls = 0;
    for expected in &expected_urls {
        if html.contains(&format!(r#"href="{}""#, expected)) {
            println!(" Found clickable link: {}", expected);
            found_urls += 1;
        } else {
            println!("L Missing clickable link: {}", expected);
        }
    }

    // Check that URLs are NOT appearing as plain text (should be wrapped in <a> tags)
    //     let plain_url_pattern = Regex::new(r"(?<![href="])https://[^\s<]+(?![^<]*</a>)").unwrap();
    //     let plain_urls: Vec<_> = plain_url_pattern.find_iter(&html).collect();

    //     if !plain_urls.is_empty() {
    //         println!("\nÂ   Found {} plain URLs (should be clickable):", plain_urls.len());
    //         for plain_url in plain_urls.iter().take(5) {
    //             println!("  - {}", plain_url.as_str());
    //         }
    //     }

    assert!(found_urls >= 1, "Should find at least 1 clickable URL link");
    println!("\n HTML URL links test passed: {}/{} URLs are clickable", found_urls, expected_urls.len());
}

/// Test that email addresses are converted to clickable mailto: links
#[test]
fn test_html_email_links_clickable() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("Â   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    println!("\n=== HTML Email Links Test ===");
    println!("PDF: {}", pdf_path);

    // Expected mailto: link pattern: <a href="mailto:...">...</a>
    let mailto_pattern = Regex::new(r#"<a\s+href="mailto:([^"]+)"[^>]*>.*?</a>"#).unwrap();
    let mailto_links: Vec<_> = mailto_pattern.captures_iter(&html).collect();

    println!("Found {} clickable mailto: links:", mailto_links.len());
    for (i, link) in mailto_links.iter().enumerate() {
        let email = &link[1];
        println!("  {}. {}", i + 1, email);
    }

    // Check for specific expected emails
    let expected_emails = vec![
        "shihanwang@gs.zzu.edu.cn",
        "yangzhenyu2022@ia.ac.cn",
        "shengsheng.qian@nlpr.ia.ac.cn",
    ];

    let mut found_emails = 0;
    for expected in &expected_emails {
        if html.contains(&format!(r#"mailto:{}"#, expected)) {
            println!(" Found clickable mailto: link: {}", expected);
            found_emails += 1;
        } else {
            println!("L Missing clickable mailto: link: {}", expected);
        }
    }

    assert!(found_emails >= 2, "Should find at least 2 clickable email links");
    println!("\n HTML email links test passed: {}/{} emails are clickable", found_emails, expected_emails.len());
}

/// Test semantic HTML structure (headings, paragraphs, etc.)
#[test]
fn test_html_semantic_structure() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("Â   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions {
        detect_headings: true,
        preserve_layout: false,  // Semantic mode
        ..Default::default()
    };
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    println!("\n=== HTML Semantic Structure Test ===");
    println!("PDF: {}", pdf_path);

    // Count semantic HTML elements
    let h1_count = html.matches("<h1>").count();
    let h2_count = html.matches("<h2>").count();
    let h3_count = html.matches("<h3>").count();
    let p_count = html.matches("<p>").count();
    let a_count = html.matches("<a ").count();

    println!("Semantic HTML elements:");
    println!("  <h1>: {}", h1_count);
    println!("  <h2>: {}", h2_count);
    println!("  <h3>: {}", h3_count);
    println!("  <p>:  {}", p_count);
    println!("  <a>:  {}", a_count);

    // Verify semantic structure
    assert!(h1_count + h2_count + h3_count > 0, "Should detect headings");
    assert!(p_count > 0, "Should have paragraph tags");
    assert!(a_count > 0, "Should have link tags");

    // Check for proper HTML structure
    assert!(html.contains("<!DOCTYPE html>") || html.contains("<html"), "Should have HTML declaration");

    println!("\n HTML semantic structure test passed");
}

/// Test layout-preserved HTML mode
#[test]
fn test_html_layout_preservation() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("Â   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions {
        preserve_layout: true,  // Layout-preserved mode
        ..Default::default()
    };
    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");

    println!("\n=== HTML Layout Preservation Test ===");
    println!("PDF: {}", pdf_path);
    println!("HTML length: {} bytes", html.len());

    // Check for CSS positioning (indicates layout preservation)
    let has_position = html.contains("position:") || html.contains("position:");
    let has_left = html.contains("left:") || html.contains("left:");
    let has_top = html.contains("top:") || html.contains("top:");

    println!("Layout preservation indicators:");
    println!("  position: {}", has_position);
    println!("  left: {}", has_left);
    println!("  top: {}", has_top);

    assert!(
        has_position || has_left || has_top,
        "Layout-preserved mode should use CSS positioning"
    );

    println!("\n HTML layout preservation test passed");
}

/// Test overall HTML quality score
#[test]
fn test_overall_html_quality_score() {
    println!("\n=== Overall HTML Quality Score Test ===\n");

    let mut total_score = 0.0;
    let mut tests_run = 0;

    for pdf_path in SAMPLE_PDFS {
        if !std::path::Path::new(pdf_path).exists() {
            println!("Â   Skipping missing PDF: {}", pdf_path);
            continue;
        }

        println!("Testing: {}", pdf_path);

        let mut doc = match PdfDocument::open(pdf_path) {
            Ok(doc) => doc,
            Err(e) => {
                println!("  L Failed to open: {}", e);
                continue;
            }
        };

        let options = ConversionOptions::default();
        let html = match doc.to_html(0, &options) {
            Ok(html) => html,
            Err(e) => {
                println!("  L Failed to convert: {}", e);
                continue;
            }
        };

        let mut score = 100.0;

        // Check 1: Clickable URLs (20 points)
        let url_pattern = Regex::new(r#"<a\s+href="https?://[^"]+"[^>]*>"#).unwrap();
        let has_clickable_urls = url_pattern.is_match(&html);
        if !has_clickable_urls && html.contains("http") {
            score -= 20.0;
            println!("  Â   -20: URLs not clickable");
        }

        // Check 2: Clickable emails (20 points)
        let mailto_pattern = Regex::new(r#"<a\s+href="mailto:[^"]+"[^>]*>"#).unwrap();
        let has_clickable_emails = mailto_pattern.is_match(&html);
        if !has_clickable_emails && html.contains("@") {
            score -= 20.0;
            println!("  Â   -20: Emails not clickable");
        }

        // Check 3: Semantic structure (20 points)
        let has_headings = html.contains("<h1>") || html.contains("<h2>") || html.contains("<h3>");
        let has_paragraphs = html.contains("<p>");
        if !has_headings || !has_paragraphs {
            score -= 20.0;
            println!("  Â   -20: Poor semantic structure");
        }

        // Check 4: No garbled text (20 points)
        let garbled_pattern = Regex::new(r"[a-z]{3}[A-Z][a-z]{4}[a-z]{2}[A-Z]").unwrap();
        let garbled_matches: Vec<_> = garbled_pattern.find_iter(&html).collect();
        if garbled_matches.len() > 3 {
            score -= 20.0;
            println!("  Â   -20: Garbled text detected ({} instances)", garbled_matches.len());
        }

        // Check 5: No replacement characters (20 points)
        let replacement_chars = html.matches('\u{FFFD}').count();
        if replacement_chars > 0 {
            score -= 20.0;
            println!("  Â   -20: Replacement characters found ({})", replacement_chars);
        }

        println!("  Score: {}/100", score);
        total_score += score;
        tests_run += 1;
    }

    if tests_run > 0 {
        let avg_score = total_score / tests_run as f64;
        println!("\n{}", "=".repeat(70));
        println!("HTML Quality Score: {:.1}/100", avg_score);
        println!("{}\n", "=".repeat(70));

        assert!(
            avg_score >= 85.0,
            "HTML quality score should be >= 85/100, got {:.1}",
            avg_score
        );

        println!(" Overall HTML quality test passed: {:.1}/100", avg_score);
    } else {
        println!("Â   No PDFs could be tested");
    }
}

/// Test HTML vs Markdown link format differences
#[test]
fn test_html_link_format_differences() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("Â   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();

    let html = doc.to_html(0, &options)
        .expect("Failed to convert to HTML");
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to Markdown");

    println!("\n=== HTML vs Markdown Link Format Test ===");

    // HTML should use <a href="...">
    let html_link_count = html.matches("<a href=").count();
    println!("HTML <a href=> links: {}", html_link_count);

    // Markdown should use [text](url)
    let md_link_count = markdown.matches("](http").count() + markdown.matches("](mailto:").count();
    println!("Markdown [](url) links: {}", md_link_count);

    assert!(html_link_count > 0, "HTML should have <a href> links");
    assert!(md_link_count > 0, "Markdown should have []() links");

    // Verify they're roughly equivalent (allow some variance)
    let difference = (html_link_count as i32 - md_link_count as i32).abs();
    assert!(
        difference <= 5,
        "HTML and Markdown link counts should be similar (difference: {})",
        difference
    );

    println!(" HTML and Markdown link formats are correct");
}

/// Benchmark: Full document HTML conversion
#[test]
#[ignore] // Run with: cargo test --test test_html_formatting_quality --ignored
fn test_full_document_html_conversion() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("Â   Test PDF not found: {}", pdf_path);
        return;
    }

    println!("\n=== Full Document HTML Conversion Benchmark ===");

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    println!("Document: {}", pdf_path);
    println!("Pages: {}", page_count);

    let options = ConversionOptions::default();

    let start = std::time::Instant::now();
    let html = doc.to_html_all(&options)
        .expect("Failed to convert all pages to HTML");
    let elapsed = start.elapsed();

    println!("HTML output size: {} bytes ({:.2} KB)", html.len(), html.len() as f64 / 1024.0);
    println!("Conversion time: {:?}", elapsed);
    println!("Pages per second: {:.2}", page_count as f64 / elapsed.as_secs_f64());

    // Verify HTML structure
    assert!(html.contains("<html") || html.len() > 1000, "Should generate substantial HTML");
    assert!(html.contains("<a href="), "Should have clickable links");

    println!(" Full document HTML conversion completed");
}
