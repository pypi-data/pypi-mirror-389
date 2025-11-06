//! Regression test for author name concatenation issue
//!
//! Issue: Author names are concatenated without spaces in multi-author papers
//! Examples:
//!   - "Shihan WangZhenyu YangYuhang Hu" → should be "Shihan Wang, Zhenyu Yang, Yuhang Hu"
//!   - "Sivajeet ChandMelih KilicRoland Wursching" → should have spaces
//!
//! Root cause: Text spans from adjacent author names are not separated by spaces
//! when extracted. This is the #1 quality issue (-6.3 points in author/metadata).
//!
//! Test PDFs:
//! - arxiv_2510.25332v1.pdf (StreamingCoT) - worst case, 3 authors concatenated
//! - arxiv_2510.26480v1.pdf (Extract Method) - 5 authors with superscripts
//! - arxiv_2510.21165v1.pdf (Financial Networks) - single author, baseline

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// Test files with known author concatenation issues
const STREAMING_COT_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";
const EXTRACT_METHOD_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.26480v1.pdf";
const FINANCIAL_NETWORKS_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

/// Known problematic concatenations that should NOT appear
const FORBIDDEN_CONCATENATIONS: &[&str] = &[
    // StreamingCoT paper (3 authors)
    "WangZhenyu",
    "ZhenyuYang",
    "YangYuhang",
    "YuhangHu",
    "Shihan WangZhenyu",

    // Extract Method paper (5 authors)
    "ChandMelih",
    "MelihKilic",
    "KilicRoland",
    "RolandWursching",
    "WurschingSushant",
    "Sivajeet ChandMelih",
    "ChandRoland",
    "Marzoccaand",  // Special case: missing space before "and"

    // General patterns
    "AuthorAuthor",  // Any two capitalized words together
];

/// Expected author names that SHOULD be present (properly spaced)
const EXPECTED_AUTHORS: &[(&str, &[&str])] = &[
    (
        STREAMING_COT_PDF,
        &[
            "Shihan Wang",
            "Zhenyu Yang",
            "Yuhang Hu",
            "Shengsheng Qian",
            "Bin Wen",
            "Fan Yang",
        ]
    ),
    (
        EXTRACT_METHOD_PDF,
        &[
            "Sivajeet Chand",
            "Melih Kilic",
            "Roland Wursching",
            "Sushant Kumar Pandey",
            "Alexander Pretschner",
        ]
    ),
    (
        FINANCIAL_NETWORKS_PDF,
        &[
            "Peng Liu",
        ]
    ),
];

#[test]
fn test_no_author_concatenation_streaming_cot() {
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("StreamingCoT markdown length: {} chars", markdown.len());
    println!("First 1000 chars:\n{}\n", &markdown[..1000.min(markdown.len())]);

    // Check for forbidden concatenations
    let mut found_issues = Vec::new();
    for forbidden in FORBIDDEN_CONCATENATIONS {
        if markdown.contains(forbidden) {
            found_issues.push(forbidden.to_string());
        }
    }

    if !found_issues.is_empty() {
        println!("\n❌ AUTHOR NAME CONCATENATION ISSUES FOUND:");
        for issue in &found_issues {
            println!("  - Found: \"{}\"", issue);
        }

        // Save for debugging
        std::fs::write("/tmp/streaming_cot_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("\n📝 Full markdown saved to: /tmp/streaming_cot_debug.md");

        panic!("Author names are concatenated without spaces");
    }

    println!("✅ No author name concatenation in StreamingCoT");
}

#[test]
fn test_no_author_concatenation_extract_method() {
    let mut doc = PdfDocument::open(EXTRACT_METHOD_PDF)
        .expect("Failed to open Extract Method PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Extract Method markdown length: {} chars", markdown.len());
    println!("First 1000 chars:\n{}\n", &markdown[..1000.min(markdown.len())]);

    // Check for "Marzoccaand" (missing space before "and")
    if markdown.contains("Marzoccaand") {
        println!("\n❌ SPECIAL ISSUE: Missing space before 'and'");
        println!("  Found: \"Marzoccaand\" should be \"Marzocca and\"");
        panic!("Missing space before 'and' in author list");
    }

    // Check for other concatenations
    let mut found_issues = Vec::new();
    for forbidden in FORBIDDEN_CONCATENATIONS {
        if markdown.contains(forbidden) {
            found_issues.push(forbidden.to_string());
        }
    }

    if !found_issues.is_empty() {
        println!("\n❌ AUTHOR NAME CONCATENATION ISSUES FOUND:");
        for issue in &found_issues {
            println!("  - Found: \"{}\"", issue);
        }
        panic!("Author names are concatenated without spaces");
    }

    println!("✅ No author name concatenation in Extract Method");
}

#[test]
fn test_expected_authors_present() {
    for (pdf_path, expected_authors) in EXPECTED_AUTHORS {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", pdf_path));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect("Failed to convert to markdown");

        println!("\nChecking: {}", pdf_path);

        let mut missing_authors = Vec::new();
        for author in *expected_authors {
            if !markdown.contains(author) {
                missing_authors.push(*author);
            } else {
                println!("  ✓ Found: \"{}\"", author);
            }
        }

        if !missing_authors.is_empty() {
            println!("\n❌ EXPECTED AUTHORS NOT FOUND:");
            for author in &missing_authors {
                println!("  - Missing: \"{}\"", author);
            }
            println!("\nThis likely means authors are concatenated or split incorrectly.");
            panic!("Expected author names not found in {}", pdf_path);
        }
    }

    println!("\n✅ All expected authors present in all test PDFs");
}

#[test]
fn test_author_span_spacing_heuristic() {
    // Test the span-level spacing detection
    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    println!("Extracted {} spans from page 0", spans.len());

    // Find author name region (typically top 20% of page)
    let page_height = spans.iter()
        .map(|s| s.bbox.y + s.bbox.height)
        .max_by(|a, b| a.partial_cmp(b).unwrap())
        .unwrap_or(0.0);

    let author_region_min_y = page_height * 0.8;
    let author_spans: Vec<_> = spans.iter()
        .filter(|s| s.bbox.y >= author_region_min_y)
        .collect();

    println!("Found {} spans in author region (top 20% of page)", author_spans.len());

    // Check for suspicious patterns: Capital letter immediately followed by another capital
    let mut suspicious_patterns = Vec::new();

    for window in author_spans.windows(2) {
        let span1 = &window[0];
        let span2 = &window[1];

        // Check horizontal distance between spans
        let gap = span2.bbox.x - (span1.bbox.x + span1.bbox.width);
        let font_size = span1.font_size;

        // If gap is very small (< 0.2em) and both start with capital letters
        if gap < font_size * 0.2 && gap > -font_size * 0.1 {
            let ends_with_lower = span1.text.chars().last()
                .map_or(false, |c| c.is_lowercase());
            let starts_with_upper = span2.text.chars().next()
                .map_or(false, |c| c.is_uppercase());

            if ends_with_lower && starts_with_upper {
                suspicious_patterns.push(format!(
                    "\"{}\" + \"{}\" (gap: {:.2}em) at y={:.1}",
                    span1.text, span2.text, gap / font_size, span1.bbox.y
                ));
            }
        }
    }

    if !suspicious_patterns.is_empty() {
        println!("\n⚠️ SUSPICIOUS SPAN PATTERNS (potential missing spaces):");
        for pattern in &suspicious_patterns {
            println!("  - {}", pattern);
        }
        println!("\nThese patterns suggest missing spaces between author names.");
        println!("Spans that transition from lowercase to uppercase with gap < 0.2em");
        println!("should probably have a space inserted.");
    }

    // This is informational, not a hard failure
    // The actual fix will insert spaces based on these heuristics
    println!("\n✅ Span spacing analysis complete");
}

#[test]
fn test_bold_text_boundary_spacing() {
    // Test that bold text boundaries don't cause concatenation
    let mut doc = PdfDocument::open(EXTRACT_METHOD_PDF)
        .expect("Failed to open Extract Method PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Known pattern in this PDF: "**Abstract—Automating the** Extract Method"
    // Should NOT be: "**Abstract—Automating the** Extract MethodThe recent"

    // Check for bold markers followed immediately by capital letters (no space)
    let bold_concat_patterns = [
        "**the** Extract Method",
        "**Abstract—Automating the** Extract",
    ];

    for pattern in &bold_concat_patterns {
        if markdown.contains(pattern) {
            // This is actually GOOD - means space is present
            println!("  ✓ Found correct pattern: \"{}\"", pattern);
        }
    }

    // Check for WRONG patterns (no space after bold)
    let wrong_patterns = [
        "**Extract MethodThe",
        "**the**Extract",
        "**Abstract**Automating",
    ];

    let mut found_wrong = Vec::new();
    for pattern in &wrong_patterns {
        if markdown.contains(pattern) {
            found_wrong.push(*pattern);
        }
    }

    if !found_wrong.is_empty() {
        println!("\n❌ BOLD TEXT BOUNDARY CONCATENATION:");
        for pattern in &found_wrong {
            println!("  - Found: \"{}\"", pattern);
        }
        panic!("Bold text boundaries are causing concatenation");
    }

    println!("✅ Bold text boundaries have correct spacing");
}

#[test]
fn test_missing_spaces_count_threshold() {
    // Statistical test: count missing spaces and ensure below threshold
    let test_pdfs = [
        (STREAMING_COT_PDF, 50),  // Should have < 50 missing spaces after fix
        (EXTRACT_METHOD_PDF, 40),
        (FINANCIAL_NETWORKS_PDF, 30),
    ];

    for (pdf_path, max_allowed) in &test_pdfs {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", pdf_path));

        let spans = doc.extract_spans(0)
            .expect("Failed to extract spans");

        // Count potential missing spaces using heuristics
        let mut missing_space_count = 0;

        for window in spans.windows(2) {
            let span1 = &window[0];
            let span2 = &window[1];

            let gap = span2.bbox.x - (span1.bbox.x + span1.bbox.width);
            let font_size = span1.font_size;
            let gap_em = gap / font_size;

            // Heuristic: gap > 0.05em and < 0.5em suggests missing space
            if gap_em > 0.05 && gap_em < 0.5 {
                let ends_alphanum = span1.text.chars().last()
                    .map_or(false, |c| c.is_alphanumeric());
                let starts_alphanum = span2.text.chars().next()
                    .map_or(false, |c| c.is_alphanumeric());

                if ends_alphanum && starts_alphanum {
                    missing_space_count += 1;
                }
            }
        }

        println!("\n{}: {} potential missing spaces",
                 pdf_path.split('/').last().unwrap(),
                 missing_space_count);

        if missing_space_count > *max_allowed {
            println!("  ❌ EXCEEDS THRESHOLD: {} > {}", missing_space_count, max_allowed);
            println!("  This indicates widespread spacing issues.");
            panic!("Too many missing spaces in {}", pdf_path);
        } else {
            println!("  ✓ Within threshold: {} <= {}", missing_space_count, max_allowed);
        }
    }

    println!("\n✅ Missing space counts within acceptable thresholds");
}

#[test]
fn test_capital_letter_transitions() {
    // Test for lowercase-to-uppercase transitions without space
    // e.g., "WangZhenyu" has "g" → "Z" transition

    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Find all lowercase→uppercase transitions without space
    let mut transitions = Vec::new();
    let chars: Vec<char> = markdown.chars().collect();

    for i in 0..chars.len()-1 {
        let current = chars[i];
        let next = chars[i+1];

        if current.is_lowercase() && next.is_uppercase() {
            // Extract context (5 chars before and after)
            let start = i.saturating_sub(5);
            let end = (i + 6).min(chars.len());
            let context: String = chars[start..end].iter().collect();

            transitions.push(context);
        }
    }

    println!("Found {} lowercase→uppercase transitions", transitions.len());

    // Filter out known good patterns (e.g., "arXiv" in references)
    let suspicious: Vec<_> = transitions.iter()
        .filter(|t| {
            !t.contains("arXiv") &&
            !t.contains("GitHub") &&
            !t.contains("https://") &&
            !t.contains("DOI") &&
            !t.chars().any(|c| c == '_' || c == '-')
        })
        .collect();

    if !suspicious.is_empty() {
        println!("\n⚠️ SUSPICIOUS LOWERCASE→UPPERCASE TRANSITIONS:");
        for (i, trans) in suspicious.iter().enumerate().take(10) {
            println!("  {}. \"{}\"", i+1, trans);
        }
        println!("\nTotal: {} suspicious transitions", suspicious.len());

        // If > 20 suspicious transitions, likely concatenation issue
        if suspicious.len() > 20 {
            panic!("Too many suspicious lowercase→uppercase transitions ({}), suggests name concatenation",
                   suspicious.len());
        }
    }

    println!("✅ Lowercase→uppercase transition analysis complete");
}
