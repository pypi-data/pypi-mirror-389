//! Comprehensive multi-page quality tests for arxiv PDF
//!
//! Root cause: Previous tests only checked page 0, missing issues on page 12+
//! This test suite validates ALL pages to prevent regression.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

const ARXIV_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25760v1.pdf";

/// Count replacement characters (� U+FFFD)
fn count_replacement_chars(text: &str) -> usize {
    text.chars().filter(|&c| c == '\u{FFFD}').count()
}

#[test]
fn test_page_0_baseline_quality() {
    // Baseline: Page 0 should have 0 replacement chars
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert page 0");

    let replacement_count = count_replacement_chars(&markdown);

    assert_eq!(
        replacement_count, 0,
        "Page 0 should have 0 replacement chars (baseline), found {}",
        replacement_count
    );
}

#[test]
fn test_page_12_font_f1_issues() {
    // Page 12 has known issues with font 'F1'
    // Target: <10 replacement chars per page (Phase 7B goal)
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(12, &options)
        .expect("Failed to convert page 12");

    let replacement_count = count_replacement_chars(&markdown);

    println!("Page 12 replacement chars: {}", replacement_count);

    // Currently failing with 120 chars - this is the issue we're tracking
    // Once Phase 7C (Type 3 Font Handling) is implemented, this should pass
    assert!(
        replacement_count < 10,
        "Page 12 has {} replacement chars (expected <10). Font 'F1' needs Type 3 handling.",
        replacement_count
    );
}

#[test]
fn test_all_pages_quality_scan() {
    // Scan all pages and identify which pages have issues
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let page_count = doc.page_count()
        .expect("Failed to get page count");

    println!("\n=== Scanning {} pages ===\n", page_count);

    let options = ConversionOptions::default();
    let mut pages_with_issues = Vec::new();
    let mut total_replacement_chars = 0;

    for page_num in 0..page_count {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));

        let replacement_count = count_replacement_chars(&markdown);
        total_replacement_chars += replacement_count;

        if replacement_count > 0 {
            pages_with_issues.push((page_num, replacement_count));
            println!("Page {}: {} replacement chars", page_num, replacement_count);
        }
    }

    println!("\n=== Summary ===");
    println!("Total pages: {}", page_count);
    println!("Pages with issues: {}", pages_with_issues.len());
    println!("Total replacement chars: {}", total_replacement_chars);

    // Target: <0.5% replacement chars (Phase 7A goal)
    let total_chars: usize = (0..page_count)
        .map(|page_num| {
            doc.to_markdown(page_num, &options)
                .map(|md| md.chars().count())
                .unwrap_or(0)
        })
        .sum();

    let replacement_percentage = (total_replacement_chars as f64 / total_chars as f64) * 100.0;

    println!("Replacement percentage: {:.2}%", replacement_percentage);

    // This will fail until Phase 7C (Type 3 Font Handling) is implemented
    assert!(
        replacement_percentage < 0.5,
        "Too many replacement characters: {:.2}% (expected <0.5%). {} total chars across {} pages.",
        replacement_percentage,
        total_replacement_chars,
        pages_with_issues.len()
    );
}

#[test]
fn test_page_distribution_analysis() {
    // Analyze which pages have the most issues
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let page_count = doc.page_count()
        .expect("Failed to get page count");

    let options = ConversionOptions::default();
    let mut page_stats: Vec<(usize, usize, f64)> = Vec::new();

    for page_num in 0..page_count {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));

        let total_chars = markdown.chars().count();
        let replacement_count = count_replacement_chars(&markdown);

        if total_chars > 0 {
            let percentage = (replacement_count as f64 / total_chars as f64) * 100.0;
            page_stats.push((page_num, replacement_count, percentage));
        }
    }

    // Sort by replacement percentage (descending)
    page_stats.sort_by(|a, b| b.2.partial_cmp(&a.2).unwrap());

    println!("\n=== Top 10 pages by replacement char percentage ===");
    for (i, (page_num, count, percentage)) in page_stats.iter().take(10).enumerate() {
        println!("{}. Page {}: {} chars ({:.2}%)", i + 1, page_num, count, percentage);
    }

    // Identify the worst page
    if let Some((worst_page, worst_count, worst_percentage)) = page_stats.first() {
        println!("\nWorst page: {} with {} chars ({:.2}%)", worst_page, worst_count, worst_percentage);

        // Page 12 is known to be the worst
        assert_eq!(*worst_page, 12, "Expected page 12 to be the worst page");

        // Once Phase 7C is implemented, even the worst page should be <1%
        assert!(
            *worst_percentage < 1.0,
            "Worst page ({}) has {:.2}% replacement chars (expected <1.0%)",
            worst_page,
            worst_percentage
        );
    }
}

#[test]
fn test_font_f1_appears_only_after_page_0() {
    // Verify that font 'F1' (the problematic font) doesn't appear on page 0
    // This explains why page-0-only tests were passing
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    // Check page 0
    let page0_spans = doc.extract_spans(0)
        .expect("Failed to extract spans from page 0");

    let page0_has_f1 = page0_spans.iter().any(|s| s.font_name == "F1");

    assert!(
        !page0_has_f1,
        "Font 'F1' should not appear on page 0 (this is why tests were passing!)"
    );

    // Check page 12 (known to have F1)
    let page12_spans = doc.extract_spans(12)
        .expect("Failed to extract spans from page 12");

    let page12_has_f1 = page12_spans.iter().any(|s| s.font_name == "F1");

    assert!(
        page12_has_f1,
        "Font 'F1' should appear on page 12 (this is where failures occur)"
    );

    println!("✓ Confirmed: Font 'F1' absent on page 0, present on page 12");
}

#[test]
fn test_individual_problematic_pages() {
    // Test each page that's known to have issues individually
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let page_count = doc.page_count()
        .expect("Failed to get page count");

    let options = ConversionOptions::default();

    // First scan to find problematic pages
    let mut problematic_pages = Vec::new();
    for page_num in 0..page_count {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));

        let replacement_count = count_replacement_chars(&markdown);
        if replacement_count > 0 {
            problematic_pages.push(page_num);
        }
    }

    println!("Found {} problematic pages: {:?}", problematic_pages.len(), problematic_pages);

    // Test each problematic page
    for page_num in problematic_pages {
        let markdown = doc.to_markdown(page_num, &options)
            .expect(&format!("Failed to convert page {}", page_num));

        let replacement_count = count_replacement_chars(&markdown);
        let total_chars = markdown.chars().count();
        let percentage = (replacement_count as f64 / total_chars as f64) * 100.0;

        println!("Page {}: {} replacement chars ({:.2}%)", page_num, replacement_count, percentage);

        // Target: <0.5% per page
        assert!(
            percentage < 0.5,
            "Page {} has {:.2}% replacement chars (expected <0.5%)",
            page_num,
            percentage
        );
    }
}

#[test]
fn test_consistency_across_conversions() {
    // Ensure converting the same page multiple times gives consistent results
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let options = ConversionOptions::default();

    // Convert page 12 three times
    let markdown1 = doc.to_markdown(12, &options)
        .expect("Failed to convert page 12 (attempt 1)");
    let markdown2 = doc.to_markdown(12, &options)
        .expect("Failed to convert page 12 (attempt 2)");
    let markdown3 = doc.to_markdown(12, &options)
        .expect("Failed to convert page 12 (attempt 3)");

    let count1 = count_replacement_chars(&markdown1);
    let count2 = count_replacement_chars(&markdown2);
    let count3 = count_replacement_chars(&markdown3);

    assert_eq!(
        count1, count2,
        "Replacement char count should be consistent across conversions (attempt 1: {}, attempt 2: {})",
        count1, count2
    );

    assert_eq!(
        count2, count3,
        "Replacement char count should be consistent across conversions (attempt 2: {}, attempt 3: {})",
        count2, count3
    );

    println!("✓ Consistent: Page 12 produces {} replacement chars across 3 conversions", count1);
}

#[test]
fn test_page_12_spans_analysis() {
    // Detailed analysis of page 12 spans to understand the issue
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open arxiv PDF");

    let spans = doc.extract_spans(12)
        .expect("Failed to extract spans from page 12");

    let total_spans = spans.len();
    let spans_with_issues: Vec<_> = spans.iter()
        .filter(|s| s.text.contains('\u{FFFD}'))
        .collect();

    let problematic_fonts: std::collections::HashSet<_> = spans_with_issues.iter()
        .map(|s| s.font_name.as_str())
        .collect();

    println!("\n=== Page 12 Span Analysis ===");
    println!("Total spans: {}", total_spans);
    println!("Spans with issues: {}", spans_with_issues.len());
    println!("Problematic fonts: {:?}", problematic_fonts);

    // Verify that font 'F1' is the only problematic font
    assert_eq!(
        problematic_fonts.len(), 1,
        "Expected exactly 1 problematic font, found {}: {:?}",
        problematic_fonts.len(),
        problematic_fonts
    );

    assert!(
        problematic_fonts.contains("F1"),
        "Expected font 'F1' to be the problematic font, found: {:?}",
        problematic_fonts
    );

    // Count replacement chars in F1 spans
    let f1_replacement_count: usize = spans_with_issues.iter()
        .filter(|s| s.font_name == "F1")
        .map(|s| s.text.chars().filter(|&c| c == '\u{FFFD}').count())
        .sum();

    println!("Replacement chars in F1 spans: {}", f1_replacement_count);

    // This is the known issue - should be 0 after Phase 7C
    assert!(
        f1_replacement_count < 10,
        "Font 'F1' produces {} replacement chars (expected <10 after Phase 7C implementation)",
        f1_replacement_count
    );
}
