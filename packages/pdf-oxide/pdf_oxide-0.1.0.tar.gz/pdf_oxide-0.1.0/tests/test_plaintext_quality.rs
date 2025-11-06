//! Plain Text Extraction Quality Tests
//!
//! Comprehensive test suite for plain text extraction quality.
//! Tests text completeness, encoding correctness, reading order, and overall quality.

use pdf_oxide::converters::ConversionOptions;
use pdf_oxide::PdfDocument;
use regex::Regex;

/// Sample PDFs for testing
const SAMPLE_PDFS: &[&str] = &[
    "../pdf_oxide_tests/pdfs/academic/arxiv_2312.00001v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2312.01234v1.pdf",
    "../pdf_oxide_tests/pdfs/government/cfr_sample.pdf",
    "../pdf_oxide_tests/pdfs/forms/irs_w4.pdf",
];

/// Test that URLs are preserved in plain text
#[test]
fn test_plaintext_url_preservation() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    println!("\n=== Plain Text URL Preservation Test ===");
    println!("PDF: {}", pdf_path);
    println!("Text length: {} chars\n", text.len());

    // Find all URLs in plain text
    let url_pattern = Regex::new(r"https?://[^\s]+").unwrap();
    let urls: Vec<_> = url_pattern.find_iter(&text).collect();

    println!("Found {} URLs:", urls.len());
    for (i, url) in urls.iter().enumerate() {
        println!("  {}. {}", i + 1, url.as_str());
    }

    // Check for specific expected URLs
    let expected_urls = vec![
        "https://github.com/Fleeting-hyh/StreamingCoT",
        "https://doi.org/10.1145/3746027.3758311",
    ];

    let mut found_urls = 0;
    for expected in &expected_urls {
        if text.contains(expected) {
            println!(" Found URL: {}", expected);
            found_urls += 1;
        } else {
            println!("L Missing URL: {}", expected);
        }
    }

    assert!(found_urls >= 1, "Should find at least 1 URL in plain text");
    println!("\n Plain text URL preservation test passed: {}/{} URLs found", found_urls, expected_urls.len());
}

/// Test that email addresses are preserved in plain text
#[test]
fn test_plaintext_email_preservation() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    println!("\n=== Plain Text Email Preservation Test ===");
    println!("PDF: {}", pdf_path);

    // Find all email addresses
    let email_pattern = Regex::new(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b").unwrap();
    let emails: Vec<_> = email_pattern.find_iter(&text).collect();

    println!("Found {} emails:", emails.len());
    for (i, email) in emails.iter().enumerate() {
        println!("  {}. {}", i + 1, email.as_str());
    }

    // Check for specific expected emails
    let expected_emails = vec![
        "shihanwang@gs.zzu.edu.cn",
        "yangzhenyu2022@ia.ac.cn",
        "shengsheng.qian@nlpr.ia.ac.cn",
    ];

    let mut found_emails = 0;
    for expected in &expected_emails {
        if text.contains(expected) {
            println!(" Found email: {}", expected);
            found_emails += 1;
        } else {
            println!("L Missing email: {}", expected);
        }
    }

    assert!(found_emails >= 2, "Should find at least 2 email addresses");
    println!("\n Plain text email preservation test passed: {}/{} emails found", found_emails, expected_emails.len());
}

/// Test text completeness (no missing content)
#[test]
fn test_plaintext_completeness() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    println!("\n=== Plain Text Completeness Test ===");
    println!("PDF: {}", pdf_path);
    println!("Text length: {} chars", text.len());

    // Check for expected content (title, authors, abstract_text)
    let expected_content = vec![
        "StreamingCoT",  // Title
        "Shihan Wang",   // Author
        "Abstract",      // Section
        "VideoQA",       // Key term
    ];

    let mut found_content = 0;
    for expected in &expected_content {
        if text.contains(expected) {
            println!(" Found: {}", expected);
            found_content += 1;
        } else {
            println!("L Missing: {}", expected);
        }
    }

    assert!(
        found_content >= 3,
        "Should find at least 3/4 expected content pieces, found {}/4",
        found_content
    );

    // Check text is substantial (not just metadata)
    assert!(text.len() > 1000, "Plain text should be substantial (>{} chars)", 1000);

    println!("\n Plain text completeness test passed: {}/{} content found", found_content, expected_content.len());
}

/// Test encoding quality (no replacement characters)
#[test]
fn test_plaintext_encoding_quality() {
    println!("\n=== Plain Text Encoding Quality Test ===\n");

    let mut total_replacement_chars = 0;
    let mut files_tested = 0;

    for pdf_path in SAMPLE_PDFS {
        if !std::path::Path::new(pdf_path).exists() {
            println!("   Skipping missing PDF: {}", pdf_path);
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
        let text = match doc.to_plain_text(0, &options) {
            Ok(text) => text,
            Err(e) => {
                println!("  L Failed to extract: {}", e);
                continue;
            }
        };

        // Count replacement characters (ý)
        let replacement_count = text.matches('\u{FFFD}').count();
        total_replacement_chars += replacement_count;

        if replacement_count > 0 {
            println!("     Found {} replacement characters (ý)", replacement_count);
        } else {
            println!("   Clean encoding (no ý characters)");
        }

        files_tested += 1;
    }

    println!("\n{}", "=".repeat(70));
    println!("Total replacement characters: {} across {} files", total_replacement_chars, files_tested);
    println!("Average per file: {:.2}", total_replacement_chars as f64 / files_tested as f64);
    println!("{}\n", "=".repeat(70));

    // Allow some replacement characters (malformed PDFs), but should be rare
    let avg_per_file = total_replacement_chars as f64 / files_tested as f64;
    assert!(
        avg_per_file < 10.0,
        "Too many replacement characters on average: {:.2}",
        avg_per_file
    );

    println!(" Plain text encoding quality test passed");
}

/// Test reading order (text flows naturally)
#[test]
fn test_plaintext_reading_order() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");

    println!("\n=== Plain Text Reading Order Test ===");
    println!("PDF: {}", pdf_path);

    // Check that title appears before abstract
    let title_pos = text.find("StreamingCoT");
    let abstract_pos = text.find("Abstract");

    println!("Title position: {:?}", title_pos);
    println!("Abstract position: {:?}", abstract_pos);

    if let (Some(title), Some(abstract_text)) = (title_pos, abstract_pos) {
        assert!(
            title < abstract_text,
            "Title should appear before Abstract in reading order"
        );
        println!(" Reading order correct: Title ({}) < Abstract ({})", title, abstract_text);
    }

    // Check that authors appear after title
    let author_pos = text.find("Shihan Wang");
    println!("Author position: {:?}", author_pos);

    if let (Some(title), Some(author)) = (title_pos, author_pos) {
        assert!(
            title < author,
            "Title should appear before author names in reading order"
        );
        println!(" Reading order correct: Title ({}) < Author ({})", title, author);
    }

    println!("\n Plain text reading order test passed");
}

/// Test overall plain text quality score
#[test]
fn test_overall_plaintext_quality_score() {
    println!("\n=== Overall Plain Text Quality Score Test ===\n");

    let mut total_score = 0.0;
    let mut tests_run = 0;

    for pdf_path in SAMPLE_PDFS {
        if !std::path::Path::new(pdf_path).exists() {
            println!("   Skipping missing PDF: {}", pdf_path);
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
        let text = match doc.to_plain_text(0, &options) {
            Ok(text) => text,
            Err(e) => {
                println!("  L Failed to convert: {}", e);
                continue;
            }
        };

        let mut score = 100.0;

        // Check 1: Text completeness (25 points)
        if text.len() < 500 {
            score -= 25.0;
            println!("     -25: Text too short ({} chars)", text.len());
        }

        // Check 2: No replacement characters (25 points)
        let replacement_count = text.matches('\u{FFFD}').count();
        if replacement_count > 0 {
            let penalty = (replacement_count as f64 * 5.0).min(25.0);
            score -= penalty;
            println!("     -{:.0}: Replacement characters found ({})", penalty, replacement_count);
        }

        // Check 3: URLs preserved (25 points)
        let has_urls = text.contains("http://") || text.contains("https://");
        let url_pattern = Regex::new(r"https?://[^\s]+").unwrap();
        let url_count = url_pattern.find_iter(&text).count();
        if has_urls && url_count == 0 {
            score -= 25.0;
            println!("     -25: URLs not preserved");
        }

        // Check 4: Emails preserved (25 points)
        let has_at = text.contains('@');
        let email_pattern = Regex::new(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b").unwrap();
        let email_count = email_pattern.find_iter(&text).count();
        if has_at && email_count == 0 {
            score -= 25.0;
            println!("     -25: Emails not preserved");
        }

        println!("  Score: {}/100", score);
        total_score += score;
        tests_run += 1;
    }

    if tests_run > 0 {
        let avg_score = total_score / tests_run as f64;
        println!("\n{}", "=".repeat(70));
        println!("Plain Text Quality Score: {:.1}/100", avg_score);
        println!("{}", "=".repeat(70));

        assert!(
            avg_score >= 90.0,
            "Plain text quality score should be >= 90/100, got {:.1}",
            avg_score
        );

        println!(" Overall plain text quality test passed: {:.1}/100", avg_score);
    } else {
        println!("   No PDFs could be tested");
    }
}

/// Test plain text vs markdown content equivalence
#[test]
fn test_plaintext_vs_markdown_equivalence() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("   Test PDF not found: {}", pdf_path);
        return;
    }

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();

    let text = doc.to_plain_text(0, &options)
        .expect("Failed to convert to plain text");
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("\n=== Plain Text vs Markdown Equivalence Test ===");
    println!("Plain text length: {} chars", text.len());
    println!("Markdown length: {} chars", markdown.len());

    // Strip markdown formatting to get plain content
    let markdown_plain = markdown
        .replace("**", "")
        .replace("##", "")
        .replace("###", "")
        .replace("[", "")
        .replace("](", " ")
        .replace(")", "");

    // Compare word counts (should be similar)
    let text_words: Vec<_> = text.split_whitespace().collect();
    let markdown_words: Vec<_> = markdown_plain.split_whitespace().collect();

    println!("Plain text words: {}", text_words.len());
    println!("Markdown words (stripped): {}", markdown_words.len());

    // Allow some variance due to formatting
    let word_diff = (text_words.len() as i32 - markdown_words.len() as i32).abs();
    let diff_percent = (word_diff as f64 / text_words.len() as f64) * 100.0;

    println!("Word count difference: {} ({:.1}%)", word_diff, diff_percent);

    assert!(
        diff_percent < 15.0,
        "Plain text and markdown should have similar word counts (difference: {:.1}%)",
        diff_percent
    );

    println!(" Plain text and markdown content are equivalent");
}

/// Benchmark: Full document plain text extraction
#[test]
#[ignore] // Run with: cargo test --test test_plaintext_quality --ignored
fn test_full_document_plaintext_extraction() {
    let pdf_path = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";

    if !std::path::Path::new(pdf_path).exists() {
        println!("   Test PDF not found: {}", pdf_path);
        return;
    }

    println!("\n=== Full Document Plain Text Extraction Benchmark ===");

    let mut doc = PdfDocument::open(pdf_path)
        .expect("Failed to open PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    println!("Document: {}", pdf_path);
    println!("Pages: {}", page_count);

    let options = ConversionOptions::default();

    let start = std::time::Instant::now();
    let text = doc.to_plain_text_all(&options)
        .expect("Failed to extract all pages to plain text");
    let elapsed = start.elapsed();

    println!("Plain text output size: {} bytes ({:.2} KB)", text.len(), text.len() as f64 / 1024.0);
    println!("Extraction time: {:?}", elapsed);
    println!("Pages per second: {:.2}", page_count as f64 / elapsed.as_secs_f64());

    // Verify text content
    assert!(text.len() > 5000, "Should extract substantial text from full document");

    println!(" Full document plain text extraction completed");
}
