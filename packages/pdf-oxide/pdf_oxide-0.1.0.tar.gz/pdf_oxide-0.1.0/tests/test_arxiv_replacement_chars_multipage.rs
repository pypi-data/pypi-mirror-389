//! Regression test for replacement characters across ALL pages
//!
//! Issue: Phase 7A tests only checked page 0, but replacement characters
//! appear on later pages. This test validates ALL pages of multi-page PDFs.
//!
//! Root cause: Tests were passing because they only checked first page.
//! Full document conversion reveals issues on pages 1-33.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

const ARXIV_MATH: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25760v1.pdf";
const MIXED_ENCODING: &str = "../pdf_oxide_tests/pdfs/mixed/YBTLDNWUYL3SLS4NVMFEB3OFUWOZBLA7.pdf";

/// Count replacement characters (� U+FFFD)
fn count_replacement_chars(text: &str) -> usize {
    text.chars().filter(|&c| c == '\u{FFFD}').count()
}

/// Analyze character distribution
fn analyze_character_distribution(text: &str) -> (usize, usize, usize, usize) {
    let total = text.chars().count();
    let ascii = text.chars().filter(|c| c.is_ascii()).count();
    let unicode_non_ascii = text.chars().filter(|c| !c.is_ascii() && *c != '\u{FFFD}').count();
    let replacement = count_replacement_chars(text);

    (total, ascii, unicode_non_ascii, replacement)
}

#[test]
fn test_arxiv_math_all_pages_no_replacement_chars() {
    let mut doc = PdfDocument::open(ARXIV_MATH)
        .expect("Failed to open arxiv math PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    println!("\n=== Testing ALL {} pages of arxiv math PDF ===\n", page_count);

    let options = ConversionOptions::default();
    let mut total_replacement_chars = 0;
    let mut pages_with_issues = Vec::new();

    // Test each page individually
    for page_num in 0..page_count {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));

        let replacement_count = count_replacement_chars(&markdown);

        if replacement_count > 0 {
            pages_with_issues.push((page_num, replacement_count));
            total_replacement_chars += replacement_count;

            println!("Page {}: {} replacement chars", page_num, replacement_count);

            // Show first occurrence
            if let Some(pos) = markdown.find('\u{FFFD}') {
                let start = pos.saturating_sub(50);
                let end = (pos + 50).min(markdown.len());
                println!("  Context: ...{}...\n", &markdown[start..end]);
            }
        }
    }

    println!("\n=== Summary ===");
    println!("Total pages: {}", page_count);
    println!("Pages with � chars: {}", pages_with_issues.len());
    println!("Total � chars: {}", total_replacement_chars);

    if !pages_with_issues.is_empty() {
        println!("\n❌ REPLACEMENT CHARACTERS FOUND:");
        for (page, count) in &pages_with_issues {
            println!("  Page {}: {} chars", page, count);
        }

        // This should be 0 after Phase 7A
        panic!(
            "Found {} replacement characters across {} pages (expected 0)",
            total_replacement_chars,
            pages_with_issues.len()
        );
    }

    println!("✅ No replacement characters in any page");
}

#[test]
fn test_arxiv_math_full_document_conversion() {
    let mut doc = PdfDocument::open(ARXIV_MATH)
        .expect("Failed to open arxiv math PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    println!("\n=== Converting full document ({} pages) ===\n", page_count);

    let options = ConversionOptions::default();
    let mut full_markdown = String::new();

    // Convert all pages
    for page_num in 0..page_count {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));
        full_markdown.push_str(&markdown);
        full_markdown.push_str("\n\n---\n\n"); // Page separator
    }

    let (total, ascii, unicode, replacement) = analyze_character_distribution(&full_markdown);

    println!("Character distribution:");
    println!("  Total: {} chars", total);
    println!("  ASCII: {} ({:.1}%)", ascii, (ascii as f64 / total as f64) * 100.0);
    println!("  Unicode (non-ASCII): {} ({:.1}%)", unicode, (unicode as f64 / total as f64) * 100.0);
    println!("  Replacement (�): {} ({:.1}%)", replacement, (replacement as f64 / total as f64) * 100.0);

    // Target: <0.5% replacement chars (very strict)
    let replacement_percentage = (replacement as f64 / total as f64) * 100.0;

    assert!(
        replacement_percentage < 0.5,
        "Too many replacement characters: {:.2}% (expected <0.5%)",
        replacement_percentage
    );

    println!("\n✅ Full document conversion quality acceptable");
}

#[test]
fn test_mixed_encoding_all_pages() {
    let mut doc = PdfDocument::open(MIXED_ENCODING)
        .expect("Failed to open mixed encoding PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    println!("\n=== Testing ALL {} pages of mixed encoding PDF ===\n", page_count);

    let options = ConversionOptions::default();
    let mut total_replacement_chars = 0;

    for page_num in 0..page_count {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));

        let replacement_count = count_replacement_chars(&markdown);
        total_replacement_chars += replacement_count;

        if replacement_count > 0 {
            println!("Page {}: {} replacement chars", page_num, replacement_count);
        }
    }

    println!("\n=== Summary ===");
    println!("Total pages: {}", page_count);
    println!("Total � chars: {}", total_replacement_chars);

    // Target: <10 replacement chars total (from Phase 7B goal)
    assert!(
        total_replacement_chars < 10,
        "Too many replacement characters: {} (expected <10)",
        total_replacement_chars
    );

    println!("✅ Replacement character count acceptable: {}", total_replacement_chars);
}

#[test]
fn test_arxiv_math_character_quality_by_page() {
    let mut doc = PdfDocument::open(ARXIV_MATH)
        .expect("Failed to open arxiv math PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    println!("\n=== Character Quality Analysis by Page ===\n");

    let options = ConversionOptions::default();
    let mut worst_pages = Vec::new();

    for page_num in 0..page_count {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));

        let (total, ascii, unicode, replacement) = analyze_character_distribution(&markdown);

        if total == 0 {
            continue; // Skip empty pages
        }

        let replacement_percentage = (replacement as f64 / total as f64) * 100.0;

        if replacement_percentage > 0.1 {
            worst_pages.push((page_num, replacement, replacement_percentage));
            println!(
                "Page {}: {} chars, {} � ({:.2}%)",
                page_num, total, replacement, replacement_percentage
            );
        }
    }

    if !worst_pages.is_empty() {
        println!("\n❌ Pages with >0.1% replacement chars:");
        worst_pages.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap());

        for (page, count, percentage) in worst_pages.iter().take(10) {
            println!("  Page {}: {} chars ({:.2}%)", page, count, percentage);
        }

        panic!(
            "{} pages have >0.1% replacement characters",
            worst_pages.len()
        );
    }

    println!("\n✅ All pages have <0.1% replacement characters");
}

#[test]
fn test_common_pdfs_multipage_quality() {
    // Test a variety of PDFs to ensure Phase 7A works across all pages
    let test_pdfs = vec![
        ("../pdf_oxide_tests/pdfs/academic/arxiv_2510.25760v1.pdf", "arxiv math", 50), // Allow up to 50 � chars
        ("../pdf_oxide_tests/pdfs/mixed/YBTLDNWUYL3SLS4NVMFEB3OFUWOZBLA7.pdf", "mixed encoding", 10),
    ];

    println!("\n=== Testing multiple PDFs (all pages) ===\n");

    for (path, name, max_allowed) in &test_pdfs {
        let mut doc = match PdfDocument::open(path) {
            Ok(d) => d,
            Err(_) => {
                println!("⚠️  Skipping {} (file not found)", name);
                continue;
            }
        };

        let page_count = doc.page_count().expect("Failed to get page count");
        let options = ConversionOptions::default();
        let mut total_replacement_chars = 0;

        for page_num in 0..page_count {
            if let Ok(markdown) = doc.to_markdown(page_num, &options) {
                total_replacement_chars += count_replacement_chars(&markdown);
            }
        }

        println!("{}: {} pages, {} � chars (max allowed: {})",
                 name, page_count, total_replacement_chars, max_allowed);

        assert!(
            total_replacement_chars <= *max_allowed,
            "{}: Too many replacement characters: {} (max: {})",
            name, total_replacement_chars, max_allowed
        );
    }

    println!("\n✅ All PDFs meet quality targets");
}

#[test]
fn test_page_zero_vs_full_document_consistency() {
    // Ensure page 0 results are consistent with full document results
    let mut doc = PdfDocument::open(ARXIV_MATH)
        .expect("Failed to open arxiv math PDF");

    let options = ConversionOptions::default();

    // Get page 0 result
    let page0_markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert page 0");
    let page0_replacements = count_replacement_chars(&page0_markdown);

    println!("Page 0: {} replacement chars", page0_replacements);

    // Get full document result
    let page_count = doc.page_count().expect("Failed to get page count");
    let mut total_replacements = 0;

    for page_num in 0..page_count {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));
        total_replacements += count_replacement_chars(&markdown);
    }

    println!("Full document ({} pages): {} replacement chars", page_count, total_replacements);

    // If page 0 is clean, full document should also be mostly clean
    if page0_replacements == 0 {
        assert!(
            total_replacements < page_count, // Allow 1 per page maximum
            "Page 0 has 0 � chars, but full document has {} (inconsistent quality)",
            total_replacements
        );
    }

    println!("✅ Page 0 quality is representative of full document");
}
