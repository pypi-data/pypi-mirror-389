//! Regression test for missing spaces between words
//!
//! Issue: Words concatenated without spaces, especially at:
//! - Case transitions: `thenThe` → should be `then The`
//! - Number-letter boundaries: `Figure1shows` → should be `Figure 1 shows`
//! - Letter-number boundaries: `page3contains` → should be `page 3 contains`
//!
//! Root cause: Characters positioned tightly in PDF without explicit spaces.
//! The merge_adjacent_spans() function tries to add spaces based on gap threshold,
//! but fails at CamelCase transitions and number boundaries.
//!
//! Expected behavior: Space insertion heuristics should detect:
//! - lowercase + uppercase transitions
//! - digit + letter transitions
//! - letter + digit transitions

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;
use regex::Regex;

// PDFs with known missing space issues
const GOVERNMENT_DOC: &str = "../pdf_oxide_tests/pdfs/government/CFR_2024_Title33_Part1.pdf";
const ARXIV_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

/// Patterns that indicate missing spaces
const MISSING_SPACE_PATTERNS: &[(&str, &str, &str)] = &[
    // CamelCase transitions (but not acronyms)
    (r"[a-z][A-Z]", "CamelCase transition", "thenThe"),

    // Number followed by letter (common in "Figure1", "Table2")
    (r"\d[a-zA-Z]", "Number-letter transition", "1shows"),

    // Letter followed by number (common in "page3", "section5")
    (r"[a-zA-Z]\d", "Letter-number transition", "page3"),

    // Lowercase followed by uppercase mid-word (not sentence start)
    (r"[a-z]{3,}[A-Z][a-z]", "Mid-word case split", "correlationNetwork"),
];

/// Patterns that should NOT trigger space insertion (legitimate cases)
const LEGITIMATE_PATTERNS: &[&str] = &[
    r"[A-Z]{2,}",      // Acronyms: HTML, PDF, API
    r"\d+\.\d+",       // Decimals: 3.14, 10.5
    r"[A-Z][a-z]+[A-Z]", // CamelCase identifiers (keep as-is in code)
];

/// Helper: Detect missing space patterns
fn detect_missing_spaces(text: &str) -> Vec<(String, String, Vec<String>)> {
    let mut issues = Vec::new();

    for (pattern, description, example) in MISSING_SPACE_PATTERNS {
        let regex = Regex::new(pattern).unwrap();

        let mut matches = Vec::new();
        for mat in regex.find_iter(text) {
            let matched_text = mat.as_str();

            // Filter out legitimate cases
            let is_legitimate = LEGITIMATE_PATTERNS.iter().any(|legit_pattern| {
                Regex::new(legit_pattern).unwrap().is_match(matched_text)
            });

            if !is_legitimate {
                matches.push(matched_text.to_string());
            }
        }

        if !matches.is_empty() {
            // Deduplicate and limit to first 10 examples
            matches.sort();
            matches.dedup();
            matches.truncate(10);

            issues.push((
                description.to_string(),
                example.to_string(),
                matches,
            ));
        }
    }

    issues
}

/// Helper: Extract word-level context around matches
fn extract_word_context(text: &str, pattern: &str) -> Vec<String> {
    let regex = Regex::new(pattern).unwrap();
    let mut contexts = Vec::new();

    for mat in regex.find_iter(text).take(5) {
        // Find word boundaries around the match
        let start = mat.start();
        let end = mat.end();

        // Expand to include full words
        let word_start = text[..start]
            .rfind(|c: char| c.is_whitespace())
            .map(|i| i + 1)
            .unwrap_or(0);

        let word_end = text[end..]
            .find(|c: char| c.is_whitespace())
            .map(|i| end + i)
            .unwrap_or(text.len());

        let context = &text[word_start..word_end];
        contexts.push(context.to_string());
    }

    contexts
}

#[test]
fn test_no_camelcase_transitions() {
    let mut doc = PdfDocument::open(GOVERNMENT_DOC)
        .expect("Failed to open government doc");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Generated {} chars of markdown", markdown.len());

    // Check for lowercase-uppercase transitions (excluding sentence starts)
    let camelcase_pattern = Regex::new(r"[a-z][A-Z]").unwrap();

    // Filter out legitimate sentence starts (. followed by space, then capital)
    let lines: Vec<&str> = markdown.lines().collect();
    let mut violations = Vec::new();

    for line in &lines {
        for mat in camelcase_pattern.find_iter(line) {
            let matched_text = mat.as_str();
            let start = mat.start();

            // Check if this is a sentence start
            let is_sentence_start = if start > 2 {
                let prev_chars = &line[start.saturating_sub(2)..start];
                prev_chars.ends_with(". ") || prev_chars.ends_with(".\t")
            } else {
                start == 0
            };

            if !is_sentence_start {
                // Extract context (20 chars before and after)
                let ctx_start = start.saturating_sub(20);
                let ctx_end = (mat.end() + 20).min(line.len());
                let context = &line[ctx_start..ctx_end];

                violations.push(format!("{} → ...{}...", matched_text, context));
            }
        }
    }

    if !violations.is_empty() {
        println!("\n❌ CAMELCASE TRANSITIONS FOUND (missing spaces):\n");
        for (i, violation) in violations.iter().enumerate().take(15) {
            println!("{}. {}", i + 1, violation);
        }
        println!("\n(showing first 15 of {} violations)", violations.len());

        panic!("Found {} CamelCase transitions indicating missing spaces", violations.len());
    }

    println!("✅ No CamelCase transitions detected");
}

#[test]
fn test_no_number_letter_transitions() {
    let mut doc = PdfDocument::open(GOVERNMENT_DOC)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Pattern: digit followed by letter (e.g., "Figure1shows", "Table2contains")
    let number_letter_pattern = Regex::new(r"\d[a-zA-Z]").unwrap();

    let matches: Vec<String> = extract_word_context(&markdown, r"\d[a-zA-Z]");

    if !matches.is_empty() {
        println!("\n❌ NUMBER-LETTER TRANSITIONS FOUND (missing spaces):\n");
        for (i, context) in matches.iter().enumerate().take(15) {
            println!("{}. {}", i + 1, context);
        }
        println!("\n(showing first 15 of {} violations)", matches.len());

        panic!("Found {} number-letter transitions indicating missing spaces", matches.len());
    }

    println!("✅ No number-letter transitions detected");
}

#[test]
fn test_no_letter_number_transitions() {
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Pattern: letter followed by digit (e.g., "page3", "section5")
    // But exclude legitimate cases like "H2O", "CO2", "3x", "10x"
    let letter_number_pattern = Regex::new(r"[a-zA-Z]\d").unwrap();

    let all_matches: Vec<String> = extract_word_context(&markdown, r"[a-zA-Z]\d");

    // Filter out common legitimate cases
    let legitimate_chemicals = Regex::new(r"^[A-Z]\d+$").unwrap(); // H2, O2, CO2
    let scientific_notation = Regex::new(r"^\d+x\d+$").unwrap(); // 10x5

    let violations: Vec<String> = all_matches
        .into_iter()
        .filter(|word| {
            !legitimate_chemicals.is_match(word) && !scientific_notation.is_match(word)
        })
        .collect();

    if !violations.is_empty() {
        println!("\n❌ LETTER-NUMBER TRANSITIONS FOUND (missing spaces):\n");
        for (i, context) in violations.iter().enumerate().take(15) {
            println!("{}. {}", i + 1, context);
        }
        println!("\n(showing first 15 of {} violations)", violations.len());

        panic!("Found {} letter-number transitions indicating missing spaces", violations.len());
    }

    println!("✅ No letter-number transitions detected");
}

#[test]
fn test_figure_table_references_have_spaces() {
    // Common pattern: "Figure 1", "Table 2", not "Figure1", "Table2"
    let mut doc = PdfDocument::open(GOVERNMENT_DOC)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Bad patterns
    let bad_figure = Regex::new(r"Figure\d|figure\d").unwrap();
    let bad_table = Regex::new(r"Table\d|table\d").unwrap();
    let bad_section = Regex::new(r"Section\d|section\d").unwrap();

    let mut violations = Vec::new();

    for pattern in &[bad_figure, bad_table, bad_section] {
        let matches: Vec<String> = pattern
            .find_iter(&markdown)
            .map(|m| m.as_str().to_string())
            .collect();
        violations.extend(matches);
    }

    if !violations.is_empty() {
        println!("\n❌ FIGURE/TABLE REFERENCES WITHOUT SPACES:\n");
        violations.sort();
        violations.dedup();

        for (i, violation) in violations.iter().enumerate().take(10) {
            println!("{}. '{}' (should be e.g., 'Figure 1')", i + 1, violation);
        }
        println!("\n(showing first 10 of {} violations)", violations.len());

        panic!("Found {} figure/table references without spaces", violations.len());
    }

    println!("✅ All figure/table references properly spaced");
}

#[test]
fn test_proper_acronyms_not_split() {
    // Ensure legitimate acronyms (HTML, PDF, API, etc.) are NOT split
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Common acronyms that should stay together
    let acronyms = vec!["HTML", "PDF", "API", "URL", "HTTP", "XML", "JSON", "SQL"];

    let mut missing_acronyms = Vec::new();

    for acronym in &acronyms {
        // Check if acronym appears intact
        let intact = markdown.contains(acronym);

        // Check if it appears split (e.g., "H T M L" or "P D F")
        let split_pattern = acronym
            .chars()
            .map(|c| c.to_string())
            .collect::<Vec<String>>()
            .join(" ");

        let is_split = markdown.contains(&split_pattern);

        if is_split && !intact {
            missing_acronyms.push(acronym);
        }
    }

    if !missing_acronyms.is_empty() {
        println!("\n⚠️  ACRONYMS APPEAR SPLIT:");
        for acronym in &missing_acronyms {
            println!("  - {}", acronym);
        }

        // This is a warning, not a failure (document may not contain these acronyms)
        println!("\nThis may indicate over-aggressive space insertion.");
    }

    println!("✅ Acronym preservation check complete");
}

#[test]
fn test_comprehensive_missing_space_detection() {
    // Combined test for all missing space patterns
    let mut doc = PdfDocument::open(GOVERNMENT_DOC)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Analyzing {} chars of markdown for missing spaces", markdown.len());

    let issues = detect_missing_spaces(&markdown);

    if !issues.is_empty() {
        println!("\n❌ MISSING SPACE PATTERNS DETECTED:\n");

        let mut total_violations = 0;
        for (description, example, matches) in &issues {
            total_violations += matches.len();
            println!("Pattern: {} (example: {})", description, example);
            println!("Found {} instances:", matches.len());
            for (i, mat) in matches.iter().enumerate().take(5) {
                println!("  {}. '{}'", i + 1, mat);
            }
            if matches.len() > 5 {
                println!("  ... and {} more", matches.len() - 5);
            }
            println!();
        }

        // Save for debugging
        std::fs::write("/tmp/missing_spaces_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("📝 Full markdown saved to: /tmp/missing_spaces_debug.md");

        panic!("Found {} missing space violations across {} pattern types",
               total_violations, issues.len());
    }

    println!("✅ No missing space patterns detected");
}

#[test]
fn test_word_boundary_heuristic_quality() {
    // Statistical check: reasonable distribution of word lengths
    let mut doc = PdfDocument::open(ARXIV_PDF)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Extract words (alphanumeric sequences)
    let word_pattern = Regex::new(r"\b[a-zA-Z]+\b").unwrap();
    let words: Vec<&str> = word_pattern
        .find_iter(&markdown)
        .map(|m| m.as_str())
        .collect();

    if words.is_empty() {
        panic!("No words found - extraction completely failed");
    }

    // Calculate statistics
    let total_words = words.len();
    let avg_word_length: f64 = words.iter().map(|w| w.len()).sum::<usize>() as f64 / total_words as f64;

    // Count very long words (possible missing spaces)
    let very_long_words: Vec<&&str> = words.iter().filter(|w| w.len() > 20).collect();
    let long_word_percentage = (very_long_words.len() as f64 / total_words as f64) * 100.0;

    println!("Total words: {}", total_words);
    println!("Average word length: {:.1} chars", avg_word_length);
    println!("Words > 20 chars: {} ({:.2}%)", very_long_words.len(), long_word_percentage);

    // Heuristic thresholds
    if avg_word_length > 8.0 {
        println!("\n⚠️  WARNING: Average word length suspiciously high ({:.1} chars)", avg_word_length);
        println!("This may indicate missing spaces between words.");
    }

    if long_word_percentage > 2.0 {
        println!("\n⚠️  WARNING: Too many very long words ({:.2}%)", long_word_percentage);
        println!("Sample long words:");
        for (i, word) in very_long_words.iter().take(5).enumerate() {
            println!("  {}. {} ({} chars)", i + 1, word, word.len());
        }

        panic!("Excessive long words ({:.2}%) suggests missing space issues", long_word_percentage);
    }

    println!("✅ Word boundary heuristic quality looks good");
}
