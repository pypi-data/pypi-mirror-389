//! Regression test for unnatural bold marker splitting
//!
//! Issue: Bold markers (`**`) are inserted mid-word, splitting natural word boundaries
//! Examples: `gr**I(Z)`, `8**21`, `forces**F`, `I(Z)**=`
//!
//! Root cause: Font changes (regular → bold/italic) detected mid-word cause separate spans.
//! The markdown converter inserts `**` at span boundaries without checking word boundaries.
//!
//! Expected behavior: Bold markers should only appear at:
//! - Whitespace boundaries (spaces, tabs, newlines)
//! - Punctuation boundaries
//! - Never mid-word (between alphanumeric characters)

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;
use regex::Regex;

// PDFs with known unnatural bold splitting issues
const ARXIV_MATH_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25106v2.pdf";
const RFC_TOC_PDF: &str = "../pdf_oxide_tests/pdfs/diverse/RFC_2616_HTTP_1_1.pdf";

/// Forbidden patterns: bold markers splitting alphanumeric sequences
///
/// Pattern explanation:
/// - `\w**\w` - alphanumeric, then **, then alphanumeric (e.g., "gr**I")
/// - `\d**\d` - digit, then **, then digit (e.g., "8**21")
/// - `[a-z]**[A-Z]` - lowercase, then **, then uppercase (e.g., "word**Next")
const FORBIDDEN_PATTERNS: &[(&str, &str)] = &[
    // Alphanumeric split
    (r"\w\*\*\w", "Alphanumeric split (e.g., 'gr**I')"),
    // Digit split
    (r"\d\*\*\d", "Digit split (e.g., '8**21')"),
    // Math expressions split
    (r"[a-zA-Z]\*\*\(", "Variable-to-paren split (e.g., 'I**(Z)')"),
    (r"\)\*\*=", "Paren-to-equals split (e.g., ')**=')"),
    // Compound word split
    (r"[a-z]\*\*[a-z]", "Lowercase word split (e.g., 'wor**ds')"),
];

/// Helper: Check markdown for unnatural bold marker patterns
fn check_for_unnatural_bold_splits(markdown: &str) -> Vec<(String, String, Vec<String>)> {
    let mut issues = Vec::new();

    for (pattern, description) in FORBIDDEN_PATTERNS {
        let regex = Regex::new(pattern).unwrap();
        let matches: Vec<String> = regex
            .find_iter(markdown)
            .map(|m| m.as_str().to_string())
            .take(5) // Limit to first 5 examples per pattern
            .collect();

        if !matches.is_empty() {
            issues.push((
                pattern.to_string(),
                description.to_string(),
                matches,
            ));
        }
    }

    issues
}

/// Helper: Extract context around a match for debugging
fn extract_context(text: &str, pattern: &str, context_chars: usize) -> Vec<String> {
    let regex = Regex::new(pattern).unwrap();
    let mut contexts = Vec::new();

    for mat in regex.find_iter(text).take(3) {
        let start = mat.start().saturating_sub(context_chars);
        let end = (mat.end() + context_chars).min(text.len());
        let context = &text[start..end];
        contexts.push(format!("...{}...", context));
    }

    contexts
}

#[test]
fn test_arxiv_math_no_unnatural_bold_splits() {
    let mut doc = PdfDocument::open(ARXIV_MATH_PDF)
        .expect("Failed to open arxiv math PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Generated {} chars of markdown from arxiv math paper", markdown.len());

    // Check for unnatural bold splitting patterns
    let issues = check_for_unnatural_bold_splits(&markdown);

    if !issues.is_empty() {
        println!("\n❌ UNNATURAL BOLD MARKER SPLITS FOUND:\n");

        for (pattern, description, examples) in &issues {
            println!("Pattern: {} - {}", pattern, description);
            println!("Examples:");
            for example in examples {
                println!("  - '{}'", example);
            }

            // Show context
            let contexts = extract_context(&markdown, pattern, 30);
            if !contexts.is_empty() {
                println!("Context:");
                for context in contexts {
                    println!("  {}", context);
                }
            }
            println!();
        }

        // Save problematic output for debugging
        std::fs::write("/tmp/arxiv_math_bold_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("📝 Full markdown saved to: /tmp/arxiv_math_bold_debug.md");

        let total_bad_splits: usize = issues.iter().map(|(_, _, ex)| ex.len()).sum();
        panic!("Found {} unnatural bold marker splits across {} patterns",
               total_bad_splits, issues.len());
    }

    println!("✅ No unnatural bold marker splits detected");
}

#[test]
fn test_bold_markers_only_at_word_boundaries() {
    let mut doc = PdfDocument::open(ARXIV_MATH_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Find all bold marker positions
    let bold_positions: Vec<usize> = markdown
        .match_indices("**")
        .map(|(pos, _)| pos)
        .collect();

    println!("Found {} bold markers", bold_positions.len());

    let mut violations = Vec::new();

    for &pos in &bold_positions {
        // Check character before and after the **
        let prev_char = if pos > 0 {
            markdown.chars().nth(pos - 1)
        } else {
            None
        };

        let next_char = if pos + 2 < markdown.len() {
            markdown[pos + 2..].chars().next()
        } else {
            None
        };

        // Violation: alphanumeric on both sides (mid-word)
        let is_violation = match (prev_char, next_char) {
            (Some(p), Some(n)) if p.is_alphanumeric() && n.is_alphanumeric() => true,
            _ => false,
        };

        if is_violation {
            // Extract context
            let start = pos.saturating_sub(20);
            let end = (pos + 22).min(markdown.len());
            let context = &markdown[start..end];
            violations.push(format!("Position {}: ...{}...", pos, context));
        }
    }

    if !violations.is_empty() {
        println!("\n❌ BOLD MARKERS AT NON-WORD-BOUNDARIES:\n");
        for (i, violation) in violations.iter().enumerate().take(10) {
            println!("{}. {}", i + 1, violation);
        }
        println!("\n(showing first 10 of {} violations)", violations.len());

        panic!("Found {} bold markers not at word boundaries", violations.len());
    }

    println!("✅ All bold markers at proper word boundaries");
}

#[test]
fn test_rfc_table_of_contents_no_bold_splits() {
    // RFC 2616 has complex table of contents with numbers and formatting
    // Previous output had patterns like: 13**3** **.............13**

    let mut doc = PdfDocument::open(RFC_TOC_PDF)
        .expect("Failed to open RFC PDF");

    let options = ConversionOptions::default();

    // Extract first 3 pages (includes table of contents)
    let page_count = doc.page_count().expect("Failed to get page count");
    let mut full_markdown = String::new();
    for page_num in 0..3.min(page_count) {
        let page_md = doc.to_markdown(page_num, &options)
            .expect("Failed to convert page");
        full_markdown.push_str(&page_md);
        full_markdown.push_str("\n\n");
    }

    println!("Generated {} chars of markdown from RFC ToC", full_markdown.len());

    // Check for number-number splits (common in ToC)
    let number_split_pattern = Regex::new(r"\d\*\*\d").unwrap();
    let number_splits: Vec<_> = number_split_pattern
        .find_iter(&full_markdown)
        .map(|m| m.as_str().to_string())
        .collect();

    if !number_splits.is_empty() {
        println!("\n❌ NUMBER SPLITS IN TABLE OF CONTENTS:");
        for (i, split) in number_splits.iter().enumerate().take(10) {
            println!("  {}. '{}'", i + 1, split);
        }
        println!("\n(showing first 10 of {})", number_splits.len());

        panic!("Found {} number splits (e.g., '13**3') in RFC ToC", number_splits.len());
    }

    println!("✅ RFC table of contents has no unnatural bold splits");
}

#[test]
fn test_mathematical_expressions_preserved() {
    // Mathematical expressions should not have bold markers inserted mid-expression
    let mut doc = PdfDocument::open(ARXIV_MATH_PDF)
        .expect("Failed to open math paper");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Common bad patterns in math expressions
    let math_violations = vec![
        (r"\w\*\*\(", "Variable-paren split: x**("),
        (r"\)\*\*\w", "Paren-variable split: )**x"),
        (r"\w\*\*=", "Variable-equals split: x**="),
        (r"=\*\*\w", "Equals-variable split: =**x"),
    ];

    let mut found_violations = Vec::new();

    for (pattern, description) in &math_violations {
        let regex = Regex::new(pattern).unwrap();
        let count = regex.find_iter(&markdown).count();

        if count > 0 {
            let examples: Vec<String> = regex
                .find_iter(&markdown)
                .take(3)
                .map(|m| m.as_str().to_string())
                .collect();

            found_violations.push((description.to_string(), count, examples));
        }
    }

    if !found_violations.is_empty() {
        println!("\n❌ MATHEMATICAL EXPRESSION VIOLATIONS:");
        for (desc, count, examples) in &found_violations {
            println!("\n{} (count: {})", desc, count);
            println!("Examples: {}", examples.join(", "));
        }

        let total: usize = found_violations.iter().map(|(_, c, _)| c).sum();
        panic!("Found {} math expression bold marker violations", total);
    }

    println!("✅ Mathematical expressions preserved correctly");
}

#[test]
fn test_bold_phrase_integrity() {
    // Bold formatting should wrap complete phrases, not split them
    // BAD:  **Chinese stock** market
    // GOOD: **Chinese stock market**

    let mut doc = PdfDocument::open(ARXIV_MATH_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Pattern: bold phrase followed immediately by non-bold word without punctuation
    // This suggests the bold formatting ended mid-phrase
    let broken_phrase_pattern = Regex::new(r"\*\*[a-z]+ [a-z]+\*\* [a-z]+").unwrap();

    let broken_phrases: Vec<String> = broken_phrase_pattern
        .find_iter(&markdown)
        .map(|m| m.as_str().to_string())
        .take(10)
        .collect();

    // This is informational only - we can't definitively say these are wrong
    // without semantic understanding, but flagging for review
    if !broken_phrases.is_empty() {
        println!("\n⚠️  POTENTIALLY BROKEN BOLD PHRASES (informational):");
        for (i, phrase) in broken_phrases.iter().enumerate() {
            println!("  {}. '{}'", i + 1, phrase);
        }
        println!("\nThese may be legitimate formatting, but worth reviewing.");
    }

    println!("✅ Bold phrase integrity check complete");
}

#[test]
fn test_bold_marker_balance() {
    // All bold markers should be properly balanced (even count)
    let mut doc = PdfDocument::open(ARXIV_MATH_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let bold_marker_count = markdown.matches("**").count();

    if bold_marker_count % 2 != 0 {
        println!("\n❌ UNBALANCED BOLD MARKERS:");
        println!("Total ** markers: {}", bold_marker_count);
        println!("Expected: even number (pairs)");
        println!("Got: odd number (unclosed bold)");

        // Try to find where the imbalance occurs
        let mut balance = 0;
        for (i, _) in markdown.match_indices("**") {
            balance = 1 - balance; // Toggle between 0 and 1
            if balance == 0 && i > markdown.len() - 100 {
                println!("\nLast closing ** at position {}", i);
            }
        }

        panic!("Unclosed bold markers detected (odd count: {})", bold_marker_count);
    }

    println!("✅ All bold markers properly balanced ({} pairs)", bold_marker_count / 2);
}
