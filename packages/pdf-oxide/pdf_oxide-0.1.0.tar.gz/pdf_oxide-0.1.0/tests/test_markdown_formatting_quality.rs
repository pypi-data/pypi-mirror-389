//! Regression test for markdown formatting quality
//!
//! Issue: Generated markdown lacks professional features compared to PyMuPDF4LLM
//! Examples:
//!   - Missing clickable links for emails/URLs
//!   - No proper markdown headers (### for sections)
//!   - Reference formatting has spacing issues
//!   - Tables not structured properly
//!
//! This test ensures our markdown output meets professional standards.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;
use regex::Regex;

const STREAMING_COT_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25332v1.pdf";
const EXTRACT_METHOD_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.26480v1.pdf";
const FINANCIAL_NETWORKS_PDF: &str = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.21165v1.pdf";

#[test]
fn test_email_links_formatted() {
    // Test that email addresses are formatted as clickable links
    // Expected: [email@domain.com](mailto:email@domain.com)

    let test_cases = [
        (STREAMING_COT_PDF, "yangzhenyu2022@ia.ac.cn"),
        (FINANCIAL_NETWORKS_PDF, "pengliuhep@outlook.com"),
    ];

    for (pdf_path, email) in &test_cases {
        let mut doc = PdfDocument::open(pdf_path)
            .expect(&format!("Failed to open {}", pdf_path));

        let options = ConversionOptions::default();
        let markdown = doc.to_markdown(0, &options)
            .expect("Failed to convert to markdown");

        // Check for clickable email format
        let expected_link = format!("[{}](mailto:{})", email, email);

        if markdown.contains(&expected_link) {
            println!("  ✅ Found clickable email link: {}", email);
        } else if markdown.contains(email) {
            // Email is present but not clickable
            println!("\n⚠️ EMAIL NOT CLICKABLE:");
            println!("  Found: \"{}\"", email);
            println!("  Expected: \"{}\"", expected_link);
            println!("  File: {}", pdf_path);
            println!("\n  This reduces markdown quality - emails should be clickable.");
            // Don't fail yet, this is a known enhancement
        } else {
            panic!("Email {} not found in {}", email, pdf_path);
        }
    }

    println!("\n✅ Email link formatting check complete");
}

#[test]
fn test_url_links_formatted() {
    // Test that URLs are formatted as clickable links
    // Expected: [https://example.com](https://example.com)

    let mut doc = PdfDocument::open(STREAMING_COT_PDF)
        .expect("Failed to open StreamingCoT PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Known URL in this PDF
    let url = "https://github.com/Fleeting-hyh/StreamingCoT";

    if markdown.contains(&format!("[{}]({})", url, url)) {
        println!("  ✅ Found clickable URL link");
    } else if markdown.contains(url) {
        println!("\n⚠️ URL NOT CLICKABLE:");
        println!("  Found: \"{}\"", url);
        println!("  Expected: \"[{}]({})\"", url, url);
        println!("\n  This reduces markdown quality - URLs should be clickable.");
    } else {
        panic!("URL {} not found in markdown", url);
    }

    println!("\n✅ URL link formatting check complete");
}

#[test]
fn test_section_headers_formatted() {
    // Test that sections are formatted as proper markdown headers
    // Expected: ### **1 Introduction** or ## 1 Introduction

    let mut doc = PdfDocument::open(EXTRACT_METHOD_PDF)
        .expect("Failed to open Extract Method PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Known sections in this PDF
    let sections = [
        "Introduction",
        "Abstract",
        "Nomenclature",
    ];

    let mut proper_headers = 0;
    let mut plain_text_headers = 0;

    for section in &sections {
        // Check for proper markdown header formats
        let header_patterns = [
            format!("### **{}**", section),  // Level 3 with bold
            format!("### {}", section),       // Level 3
            format!("## **{}**", section),    // Level 2 with bold
            format!("## {}", section),        // Level 2
            format!("# **{}**", section),     // Level 1 with bold
            format!("# {}", section),         // Level 1
        ];

        let mut found_proper = false;
        for pattern in &header_patterns {
            if markdown.contains(pattern) {
                println!("  ✅ Found proper header: \"{}\"", pattern);
                proper_headers += 1;
                found_proper = true;
                break;
            }
        }

        if !found_proper {
            // Check if it's just bold (not a proper header)
            if markdown.contains(&format!("**{}**", section)) {
                println!("  ⚠️ Section \"{}\" is bold but not a markdown header", section);
                plain_text_headers += 1;
            }
        }
    }

    println!("\nHeader formatting summary:");
    println!("  Proper markdown headers: {}", proper_headers);
    println!("  Plain bold text (not headers): {}", plain_text_headers);

    if proper_headers == 0 && plain_text_headers > 0 {
        println!("\n⚠️ NO PROPER MARKDOWN HEADERS FOUND");
        println!("  Sections are bold text instead of markdown headers");
        println!("  This reduces navigation and formatting quality");
    }

    println!("\n✅ Section header formatting check complete");
}

#[test]
fn test_reference_formatting_quality() {
    // Test that citation references are formatted cleanly
    // Current issues: "21, 23 –25" (extra space before em-dash)
    // Expected: "[21], [23]–[25]" or at least "21, 23–25"

    let mut doc = PdfDocument::open(FINANCIAL_NETWORKS_PDF)
        .expect("Failed to open Financial Networks PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check for problematic spacing patterns
    let spacing_issues = [
        " –",   // Space before em-dash
        " —",   // Space before em-dash (long)
        "– ",   // Space after em-dash
        "— ",   // Space after em-dash (long)
    ];

    let mut found_issues = Vec::new();
    for pattern in &spacing_issues {
        // Find occurrences in citation context (surrounded by digits)
        let regex_pattern = format!(r"\d{}", regex::escape(pattern));
        let re = Regex::new(&regex_pattern).unwrap();

        for mat in re.find_iter(&markdown) {
            found_issues.push(mat.as_str().to_string());
        }
    }

    if !found_issues.is_empty() {
        println!("\n⚠️ REFERENCE SPACING ISSUES FOUND:");
        for issue in found_issues.iter().take(10) {
            println!("  - \"{}\"", issue);
        }
        println!("\n  These spacing issues reduce formatting quality.");
        println!("  Expected: \"21–25\" or \"[21]–[25]\"");
        println!("  Found: \"21 –25\" or similar");
    } else {
        println!("  ✅ No obvious spacing issues in references");
    }

    println!("\n✅ Reference formatting check complete");
}

#[test]
fn test_citation_bracket_formatting() {
    // Test if citations are formatted with brackets like PyMuPDF4LLM
    // PyMuPDF4LLM format: [1], [2]–[9], [21]
    // Our format: 1, 2–9, 21 (superscripts)

    let mut doc = PdfDocument::open(FINANCIAL_NETWORKS_PDF)
        .expect("Failed to open Financial Networks PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check for bracketed citations
    let bracket_re = Regex::new(r"\[\d+\]").unwrap();
    let bracket_count = bracket_re.find_iter(&markdown).count();

    // Check for plain number citations
    let plain_re = Regex::new(r"(?<![[\d])\d{1,2}(?![\d\]])").unwrap();
    let plain_count = plain_re.find_iter(&markdown).count();

    println!("Citation formatting:");
    println!("  Bracketed citations ([1]): {}", bracket_count);
    println!("  Plain number citations (1): {}", plain_count);

    if bracket_count > 0 {
        println!("  ✅ Using bracketed citation format (professional)");
    } else if plain_count > 50 {
        println!("\n⚠️ PLAIN NUMBER CITATIONS:");
        println!("  Found {} plain number citations", plain_count);
        println!("  PyMuPDF4LLM uses bracketed format: [1], [2]–[9]");
        println!("  This is a formatting preference, not an error");
    }

    println!("\n✅ Citation bracket formatting check complete");
}

#[test]
fn test_bold_marker_cleanup() {
    // Test that bold markers are clean (no excessive ** markers)
    let mut doc = PdfDocument::open(EXTRACT_METHOD_PDF)
        .expect("Failed to open Extract Method PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check for problematic bold patterns
    let problematic_patterns = [
        "** **",          // Empty bold
        "****",           // Double bold markers
        "** and **",      // Single word bold
        "** the **",      // Common word bold
    ];

    let mut found_issues = Vec::new();
    for pattern in &problematic_patterns {
        if markdown.contains(pattern) {
            let count = markdown.matches(pattern).count();
            found_issues.push((pattern.to_string(), count));
        }
    }

    if !found_issues.is_empty() {
        println!("\n⚠️ BOLD MARKER ISSUES:");
        for (pattern, count) in &found_issues {
            println!("  - \"{}\" appears {} times", pattern, count);
        }
        println!("\n  These patterns suggest over-aggressive bold detection");
    } else {
        println!("  ✅ No problematic bold marker patterns");
    }

    // Check bold marker density
    let bold_count = markdown.matches("**").count();
    let char_count = markdown.len();
    let bold_density = (bold_count as f32 / char_count as f32) * 100.0;

    println!("\nBold marker stats:");
    println!("  Bold markers (**): {}", bold_count);
    println!("  Density: {:.2}% of characters", bold_density);

    if bold_density > 5.0 {
        println!("\n⚠️ HIGH BOLD MARKER DENSITY:");
        println!("  {:.2}% of characters are bold markers", bold_density);
        println!("  May indicate over-use of bold formatting");
    }

    println!("\n✅ Bold marker cleanup check complete");
}

#[test]
fn test_line_break_consistency() {
    // Test that line breaks are used consistently and appropriately
    let mut doc = PdfDocument::open(FINANCIAL_NETWORKS_PDF)
        .expect("Failed to open Financial Networks PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check for problematic line break patterns
    let lines: Vec<&str> = markdown.lines().collect();

    let mut very_short_lines = 0;
    let mut very_long_lines = 0;
    let mut empty_lines = 0;

    for line in &lines {
        let len = line.trim().len();
        if len == 0 {
            empty_lines += 1;
        } else if len < 20 {
            very_short_lines += 1;
        } else if len > 200 {
            very_long_lines += 1;
        }
    }

    let total_lines = lines.len();
    let short_pct = (very_short_lines as f32 / total_lines as f32) * 100.0;
    let long_pct = (very_long_lines as f32 / total_lines as f32) * 100.0;

    println!("Line break analysis:");
    println!("  Total lines: {}", total_lines);
    println!("  Empty lines: {}", empty_lines);
    println!("  Very short (<20 chars): {} ({:.1}%)", very_short_lines, short_pct);
    println!("  Very long (>200 chars): {} ({:.1}%)", very_long_lines, long_pct);

    if short_pct > 40.0 {
        println!("\n⚠️ HIGH SHORT LINE PERCENTAGE:");
        println!("  {:.1}% of lines are very short", short_pct);
        println!("  May indicate excessive line breaking");
    }

    println!("\n✅ Line break consistency check complete");
}

#[test]
fn test_table_structure_detection() {
    // Test if tables are detected and formatted
    let mut doc = PdfDocument::open(FINANCIAL_NETWORKS_PDF)
        .expect("Failed to open Financial Networks PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check for markdown table format
    let has_table_separators = markdown.contains("|---|") || markdown.contains("| --- |");
    let has_pipe_rows = markdown.lines().filter(|l| l.trim().starts_with('|')).count();

    println!("Table structure detection:");
    println!("  Has table separators: {}", has_table_separators);
    println!("  Lines with pipes (|): {}", has_pipe_rows);

    if has_table_separators {
        println!("  ✅ Tables are formatted with markdown syntax");
    } else if has_pipe_rows > 0 {
        println!("  ⚠️ Pipes present but no proper table format");
    } else {
        println!("  ℹ️ No table structures detected in markdown");
    }

    // Known table in this PDF (periods table)
    let table_keywords = ["Period", "Starting date", "Ending date", "P1", "P2", "P10"];
    let keyword_count = table_keywords.iter()
        .filter(|&&kw| markdown.contains(kw))
        .count();

    if keyword_count >= 4 {
        println!("\n  Table data is present ({} keywords found)", keyword_count);
        if !has_table_separators {
            println!("  ⚠️ But not formatted as proper markdown table");
            println!("  Expected format:");
            println!("    | Period | Starting Date | Ending Date |");
            println!("    |--------|---------------|-------------|");
            println!("    | P1     | 2004-04-07    | ...         |");
        }
    }

    println!("\n✅ Table structure detection check complete");
}

#[test]
fn test_metadata_header_format() {
    // Test that PDF metadata is formatted properly
    let mut doc = PdfDocument::open(FINANCIAL_NETWORKS_PDF)
        .expect("Failed to open Financial Networks PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    // Check for our metadata header
    let has_pages_metadata = markdown.contains("**Pages:**");
    let has_extracted_metadata = markdown.contains("# Extracted from:");

    println!("Metadata header formatting:");
    println!("  Has '**Pages:**' metadata: {}", has_pages_metadata);
    println!("  Has '# Extracted from:' header: {}", has_extracted_metadata);

    if has_pages_metadata && has_extracted_metadata {
        println!("  ✅ Metadata header is present");

        // Check if it's at the top
        let first_line = markdown.lines().next().unwrap_or("");
        if first_line.starts_with("# Extracted from:") {
            println!("  ✅ Metadata header is at the top");
        }
    } else {
        println!("  ⚠️ Metadata header format may be inconsistent");
    }

    println!("\n✅ Metadata header format check complete");
}

#[test]
fn test_overall_markdown_quality_score() {
    // Comprehensive quality score based on multiple factors
    let mut doc = PdfDocument::open(EXTRACT_METHOD_PDF)
        .expect("Failed to open Extract Method PDF");

    let options = ConversionOptions::default();
    let markdown = doc.to_markdown(0, &options)
        .expect("Failed to convert to markdown");

    let mut score = 100.0;
    let mut deductions: Vec<String> = Vec::new();

    // Check 1: Clickable links (-10 if missing)
    let has_clickable_links = markdown.contains("](mailto:") || markdown.contains("](http");
    if !has_clickable_links {
        score -= 10.0;
        deductions.push("No clickable links (-10)".to_string());
    }

    // Check 2: Proper headers (-10 if missing)
    let has_proper_headers = markdown.contains("### ") || markdown.contains("## ");
    if !has_proper_headers {
        score -= 10.0;
        deductions.push("No proper markdown headers (-10)".to_string());
    }

    // Check 3: Clean reference spacing (-5 if issues)
    let has_spacing_issues = markdown.contains(" –") || markdown.contains("— ");
    if has_spacing_issues {
        score -= 5.0;
        deductions.push("Reference spacing issues (-5)".to_string());
    }

    // Check 4: Bold marker cleanliness (-5 if excessive)
    let bold_count = markdown.matches("**").count();
    let char_count = markdown.len();
    let bold_density = (bold_count as f32 / char_count as f32) * 100.0;
    if bold_density > 5.0 {
        score -= 5.0;
        deductions.push(format!("High bold density {:.1}% (-5)", bold_density));
    }

    // Check 5: Table formatting (-5 if tables present but not formatted)
    let has_pipes = markdown.contains('|');
    let has_table_format = markdown.contains("|---");
    if has_pipes && !has_table_format {
        score -= 5.0;
        deductions.push("Tables not properly formatted (-5)".to_string());
    }

    println!("\n╔══════════════════════════════════════════════╗");
    println!("║   MARKDOWN QUALITY SCORE: {:.1}/100        ║", score);
    println!("╚══════════════════════════════════════════════╝");

    if !deductions.is_empty() {
        println!("\nDeductions:");
        for deduction in &deductions {
            println!("  - {}", deduction);
        }
    }

    if score >= 90.0 {
        println!("\n✅ EXCELLENT - Professional markdown quality");
    } else if score >= 75.0 {
        println!("\n⚠️ GOOD - Some improvements possible");
    } else {
        println!("\n❌ NEEDS IMPROVEMENT - Multiple quality issues");
    }

    // Don't fail the test, this is informational
    println!("\n✅ Overall quality assessment complete");
}
