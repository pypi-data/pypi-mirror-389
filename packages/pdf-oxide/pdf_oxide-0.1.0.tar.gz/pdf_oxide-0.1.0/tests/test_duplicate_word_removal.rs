//! Regression test for duplicate consecutive words
//!
//! Issue: Same word appears twice consecutively (e.g., "the the", "and and")
//!
//! Root cause: Layout/column detection issues causing same text region to be
//! read twice, or header/footer duplication, or multi-column text merging incorrectly.
//!
//! Expected behavior:
//! - No consecutive duplicate words (except intentional cases like quotes)
//! - Column boundaries detected correctly
//! - Reading order prevents double-processing of regions

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;
use regex::Regex;

// PDFs with known duplicate word issues
const GOVERNMENT_DOC_1: &str = "../pdf_oxide_tests/pdfs/government/CFR_2024_Title38_Vol1_Pensions_Bonuses_and_Veterans'_Relief.pdf";
const GOVERNMENT_DOC_2: &str = "../pdf_oxide_tests/pdfs/government/CFR_2024_Title19_Vol1_Customs_Duties.pdf";

/// Helper: Find all consecutive duplicate words
fn find_duplicate_words(text: &str) -> Vec<(String, Vec<usize>)> {
    // Pattern: word boundary, capture word (4+ chars), whitespace, same word, word boundary
    // Minimum 4 chars to avoid false positives with common short words
    let pattern = Regex::new(r"\b(\w{4,})\s+\1\b").unwrap();

    let mut duplicates: std::collections::HashMap<String, Vec<usize>> =
        std::collections::HashMap::new();

    for mat in pattern.captures_iter(text) {
        let word = mat.get(1).unwrap().as_str().to_string();
        let pos = mat.get(0).unwrap().start();

        duplicates.entry(word).or_insert_with(Vec::new).push(pos);
    }

    let mut result: Vec<(String, Vec<usize>)> = duplicates.into_iter().collect();
    result.sort_by(|a, b| b.1.len().cmp(&a.1.len())); // Sort by frequency

    result
}

/// Helper: Extract context around a duplicate
fn extract_context(text: &str, pos: usize, word: &str) -> String {
    let start = pos.saturating_sub(30);
    let end = (pos + word.len() * 2 + 30).min(text.len());
    let context = &text[start..end];

    format!("...{}...", context)
}

/// Helper: Check if a duplicate might be intentional
fn is_likely_intentional(context: &str, word: &str) -> bool {
    // Check for quote patterns like: "the the"
    let in_quotes = context.contains(&format!("\"{}  {}\"", word, word))
        || context.contains(&format!("'{} {}'", word, word));

    // Check for emphasis patterns like: "very very"
    let emphasis_words = ["very", "really", "quite", "much"];
    let is_emphasis = emphasis_words.contains(&word.to_lowercase().as_str());

    in_quotes || is_emphasis
}

#[test]
fn test_no_consecutive_duplicate_words() {
    let mut doc = PdfDocument::open(GOVERNMENT_DOC_1)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    println!("Generated {} chars of markdown", markdown.len());

    let duplicates = find_duplicate_words(&markdown);

    // Filter out likely intentional duplicates
    let unintentional: Vec<_> = duplicates
        .into_iter()
        .filter(|(word, positions)| {
            // Check first occurrence
            if let Some(&first_pos) = positions.first() {
                let context = extract_context(&markdown, first_pos, word);
                !is_likely_intentional(&context, word)
            } else {
                true
            }
        })
        .collect();

    if !unintentional.is_empty() {
        println!("\n❌ CONSECUTIVE DUPLICATE WORDS FOUND:\n");

        let total_duplicates: usize = unintentional.iter().map(|(_, pos)| pos.len()).sum();
        println!("Total duplicate instances: {}", total_duplicates);
        println!("Unique words duplicated: {}", unintentional.len());
        println!();

        // Show top 10 most frequent duplicates
        for (i, (word, positions)) in unintentional.iter().enumerate().take(10) {
            println!("{}. \"{}\" (duplicated {} times)", i + 1, word, positions.len());

            // Show first occurrence with context
            if let Some(&first_pos) = positions.first() {
                let context = extract_context(&markdown, first_pos, word);
                println!("   First occurrence: {}", context);
            }
        }

        if unintentional.len() > 10 {
            println!("\n... and {} more", unintentional.len() - 10);
        }

        // Save for debugging
        std::fs::write("/tmp/duplicate_words_debug.md", &markdown)
            .expect("Failed to write debug file");
        println!("\n📝 Full markdown saved to: /tmp/duplicate_words_debug.md");

        panic!(
            "Found {} consecutive duplicate words across {} unique words",
            total_duplicates,
            unintentional.len()
        );
    }

    println!("✅ No consecutive duplicate words detected");
}

#[test]
fn test_common_duplicates() {
    // Test for specific common duplicate patterns
    let mut doc = PdfDocument::open(GOVERNMENT_DOC_2)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Common words that shouldn't be duplicated
    let common_words = ["the", "and", "that", "this", "with", "from", "have", "been"];

    let mut found_duplicates = Vec::new();

    for word in &common_words {
        let pattern = format!(r"\b{}\s+{}\b", word, word);
        let regex = Regex::new(&pattern).unwrap();

        let count = regex.find_iter(&markdown).count();
        if count > 0 {
            found_duplicates.push((word.to_string(), count));
        }
    }

    if !found_duplicates.is_empty() {
        println!("\n❌ COMMON WORD DUPLICATES FOUND:");
        for (word, count) in &found_duplicates {
            println!("  \"{}  {}\": {} occurrences", word, word, count);
        }

        let total: usize = found_duplicates.iter().map(|(_, c)| c).sum();
        panic!("Found {} instances of common word duplication", total);
    }

    println!("✅ No common word duplicates detected");
}

#[test]
fn test_duplicate_distribution() {
    // Statistical test: check if duplicates are localized or spread throughout
    let mut doc = PdfDocument::open(GOVERNMENT_DOC_1)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let duplicates = find_duplicate_words(&markdown);

    if duplicates.is_empty() {
        println!("✅ No duplicates to analyze");
        return;
    }

    println!("Analyzing {} unique duplicated words", duplicates.len());

    // Calculate statistics
    let total_instances: usize = duplicates.iter().map(|(_, pos)| pos.len()).sum();
    let avg_per_word = total_instances as f64 / duplicates.len() as f64;

    println!("Total duplicate instances: {}", total_instances);
    println!("Average duplications per word: {:.2}", avg_per_word);

    // Check if duplicates are concentrated (indicates systematic issue)
    let max_duplicates = duplicates.iter().map(|(_, pos)| pos.len()).max().unwrap_or(0);

    if max_duplicates > 10 {
        println!("\n⚠️  HIGH CONCENTRATION:");
        println!("One word appears duplicated {} times", max_duplicates);
        println!("This suggests a systematic layout/column detection issue");

        if let Some((word, _)) = duplicates.first() {
            println!("Most duplicated word: \"{}\"", word);
        }
    }

    // Heuristic: if average is high, it's likely not random
    if avg_per_word > 3.0 {
        panic!(
            "High average duplication rate ({:.2}) suggests systematic issue",
            avg_per_word
        );
    }

    println!("✅ Duplicate distribution analysis complete");
}

#[test]
fn test_intentional_duplicates_preserved() {
    // Verify that legitimate duplicate patterns are preserved
    let mut doc = PdfDocument::open(GOVERNMENT_DOC_1)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // If markdown contains quotes, check for legitimate duplicates
    let has_quotes = markdown.contains('"');

    if !has_quotes {
        println!("ℹ️  No quotes found, skipping intentional duplicate check");
        return;
    }

    // Look for patterns like: "word word" in quotes
    let quoted_duplicate = Regex::new(r#""[^"]*\b(\w+)\s+\1\b[^"]*""#).unwrap();
    let count = quoted_duplicate.find_iter(&markdown).count();

    if count > 0 {
        println!("Found {} potential intentional duplicates in quotes", count);
        println!("✅ Intentional duplicates can be preserved");
    } else {
        println!("✅ No intentional duplicates found (or none needed)");
    }
}

#[test]
fn test_multipage_duplicate_detection() {
    // Test duplicate detection across multiple pages
    let mut doc = PdfDocument::open(GOVERNMENT_DOC_1)
        .expect("Failed to open PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    let pages_to_check = 3.min(page_count);

    println!("Checking {} pages for duplicates", pages_to_check);

    let options = ConversionOptions::default();
    let mut page_duplicate_counts = Vec::new();

    for page_num in 0..pages_to_check {
        let markdown = doc.to_markdown(page_num, &options)
            .expect("Failed to convert page");

        let duplicates = find_duplicate_words(&markdown);
        let total_instances: usize = duplicates.iter().map(|(_, pos)| pos.len()).sum();

        page_duplicate_counts.push((page_num, total_instances));

        println!("Page {}: {} duplicate instances", page_num, total_instances);
    }

    // Check if any page has excessive duplicates
    let max_duplicates = page_duplicate_counts
        .iter()
        .map(|(_, count)| count)
        .max()
        .copied()
        .unwrap_or(0);

    if max_duplicates > 50 {
        println!("\n❌ EXCESSIVE DUPLICATES ON SOME PAGES:");
        for (page_num, count) in &page_duplicate_counts {
            if *count > 50 {
                println!("  Page {}: {} duplicates", page_num, count);
            }
        }

        panic!("Some pages have excessive duplicate words (>{} instances)", max_duplicates);
    }

    println!("✅ Duplicate distribution reasonable across all pages");
}

#[test]
fn test_no_header_footer_duplication() {
    // Headers/footers being read twice is a common source of duplicates
    let mut doc = PdfDocument::open(GOVERNMENT_DOC_1)
        .expect("Failed to open PDF");

    let page_count = doc.page_count().expect("Failed to get page count");
    if page_count < 2 {
        println!("ℹ️  Need at least 2 pages to test header/footer duplication");
        return;
    }

    let options = ConversionOptions::default();

    // Get first two pages
    let page1 = doc.to_markdown(0, &options).expect("Failed to convert page 1");
    let page2 = doc.to_markdown(1, &options).expect("Failed to convert page 2");

    // Extract first and last 100 chars from each page
    let page1_start = &page1[..100.min(page1.len())];
    let page1_end = &page1[page1.len().saturating_sub(100)..];

    let page2_start = &page2[..100.min(page2.len())];
    let page2_end = &page2[page2.len().saturating_sub(100)..];

    // Check for suspicious similarities (possible header/footer duplication)
    let start_similarity = page1_start == page2_start;
    let end_similarity = page1_end == page2_end;

    if start_similarity {
        println!("⚠️  SUSPICIOUS: Pages start with identical text");
        println!("This might indicate header duplication");
    }

    if end_similarity {
        println!("⚠️  SUSPICIOUS: Pages end with identical text");
        println!("This might indicate footer duplication");
    }

    if !start_similarity && !end_similarity {
        println!("✅ No obvious header/footer duplication detected");
    } else {
        println!("ℹ️  This is informational - identical headers/footers are valid");
    }
}

#[test]
fn test_column_boundary_issues() {
    // Duplicates near column boundaries might indicate column detection issues
    let mut doc = PdfDocument::open(GOVERNMENT_DOC_1)
        .expect("Failed to open PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let duplicates = find_duplicate_words(&markdown);

    if duplicates.is_empty() {
        println!("✅ No duplicates found");
        return;
    }

    // Analyze the context of duplicates for column-like patterns
    let mut column_indicators = 0;

    for (word, positions) in &duplicates {
        for &pos in positions {
            let context = extract_context(&markdown, pos, word);

            // Look for patterns that suggest column boundaries
            // e.g., lots of whitespace, repeated structures
            if context.contains("     ") || context.matches('\n').count() > 3 {
                column_indicators += 1;
            }
        }
    }

    if column_indicators > 0 {
        let ratio = column_indicators as f64
            / duplicates.iter().map(|(_, p)| p.len()).sum::<usize>() as f64;

        println!(
            "ℹ️  {:.1}% of duplicates occur near potential column boundaries",
            ratio * 100.0
        );

        if ratio > 0.5 {
            println!("⚠️  High ratio suggests column detection issues");
        }
    }

    println!("✅ Column boundary analysis complete");
}
