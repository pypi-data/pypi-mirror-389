//! Regression test for missing table detection
//!
//! Issue: 89 PDFs (25%) have tables that PyMuPDF4LLM extracts but we don't
//! Root cause: No table detection/extraction implementation
//!
//! This is a MAJOR feature gap discovered by comparing with PyMuPDF4LLM.
//! Tables are critical for academic, financial, and technical documents.

use pdf_oxide::PdfDocument;
use pdf_oxide::converters::ConversionOptions;

/// Sample PDFs with tables (identified from comparison analysis)
const PDFS_WITH_TABLES: &[&str] = &[
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.26610v1.pdf",
    "../pdf_oxide_tests/pdfs/diverse/2Z5VOQ6G6CMR5GMVSAAXULXHXTMJPTM2.pdf",
    "../pdf_oxide_tests/pdfs/diverse/QRJ42GGGA52M42R57XTGIQONYKAKWVG5.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25440v1.pdf",
    "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25502v1.pdf",
];

/// Detect potential table patterns in text
fn detect_table_patterns(text: &str) -> Vec<String> {
    let mut indicators = Vec::new();

    // 1. Multiple consecutive spaces (table columns)
    let multi_space_lines = text.lines()
        .filter(|line| line.contains("   ") || line.contains("  "))
        .count();

    if multi_space_lines > 5 {
        indicators.push(format!(
            "Multiple-space alignment: {} lines (possible table columns)",
            multi_space_lines
        ));
    }

    // 2. Pipe characters (markdown tables)
    let pipe_lines = text.lines()
        .filter(|line| line.contains('|'))
        .count();

    if pipe_lines > 3 {
        indicators.push(format!(
            "Pipe characters: {} lines (possible markdown table)",
            pipe_lines
        ));
    }

    // 3. Tab characters (table columns)
    let tab_lines = text.lines()
        .filter(|line| line.contains('\t'))
        .count();

    if tab_lines > 3 {
        indicators.push(format!(
            "Tab characters: {} lines (possible table)",
            tab_lines
        ));
    }

    // 4. Consistent column structure (repeating pattern of words)
    let lines_with_numbers = text.lines()
        .filter(|line| {
            let words: Vec<&str> = line.split_whitespace().collect();
            words.len() >= 3 && words.iter().any(|w| w.chars().all(|c| c.is_numeric() || c == '.' || c == ','))
        })
        .count();

    if lines_with_numbers > 5 {
        indicators.push(format!(
            "Numeric columns: {} lines (possible data table)",
            lines_with_numbers
        ));
    }

    indicators
}

#[test]
fn test_table_detection_basic() {
    println!("\n=== Testing Table Detection ===");

    for pdf_path in PDFS_WITH_TABLES.iter().take(2) {
        if !std::path::Path::new(pdf_path).exists() {
            println!("⚠️  File not found: {}", pdf_path);
            continue;
        }

        println!("\nChecking: {}", pdf_path);

        match PdfDocument::open(pdf_path) {
            Ok(mut doc) => {
                match doc.to_markdown(0, &ConversionOptions::default()) {
                    Ok(markdown) => {
                        let indicators = detect_table_patterns(&markdown);

                        if indicators.is_empty() {
                            println!("  ❌ No table indicators found");
                            println!("  PyMuPDF4LLM detected tables in this PDF");
                        } else {
                            println!("  ✓ Table indicators found:");
                            for indicator in &indicators {
                                println!("    - {}", indicator);
                            }
                        }

                        // For now, this test documents the issue
                        // Once table extraction is implemented, we can assert
                        // assert!(!indicators.is_empty(), "Should detect table patterns");
                    }
                    Err(e) => {
                        println!("  ❌ Extraction error: {}", e);
                    }
                }
            }
            Err(e) => {
                println!("  ❌ Failed to open: {}", e);
            }
        }
    }

    println!("\n⚠️  Table extraction not yet implemented");
    println!("    This test documents the feature gap");
}

#[test]
fn test_table_vs_pymupdf4llm() {
    // Compare our output with PyMuPDF4LLM for table-heavy PDFs
    println!("\n=== Comparing Table Extraction ===");

    let test_file = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.26610v1.pdf";

    if !std::path::Path::new(test_file).exists() {
        println!("⚠️  Test file not found");
        return;
    }

    let mut doc = PdfDocument::open(test_file)
        .expect("Failed to open PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to extract markdown");

    // Check if PyMuPDF4LLM output exists
    let pymupdf_output = "../pdf_oxide_tests/benchmark_outputs/pymupdf4llm/arxiv_2510.26610v1.md";

    if std::path::Path::new(pymupdf_output).exists() {
        let pymupdf_markdown = std::fs::read_to_string(pymupdf_output)
            .expect("Failed to read PyMuPDF4LLM output");

        let our_indicators = detect_table_patterns(&markdown);
        let their_indicators = detect_table_patterns(&pymupdf_markdown);

        println!("\nOur table indicators: {}", our_indicators.len());
        println!("PyMuPDF4LLM indicators: {}", their_indicators.len());

        if !their_indicators.is_empty() && our_indicators.is_empty() {
            println!("\n❌ PyMuPDF4LLM detected tables, we didn't");
            println!("   This confirms the table extraction gap");
        }
    }

    println!("\n📋 Table extraction feature needed");
}

#[test]
fn test_table_column_alignment() {
    // Test if we preserve column structure in tables
    println!("\n=== Testing Column Alignment ===");

    let test_file = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25502v1.pdf";

    if !std::path::Path::new(test_file).exists() {
        println!("⚠️  Test file not found");
        return;
    }

    let mut doc = PdfDocument::open(test_file)
        .expect("Failed to open PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Group spans by Y position (rows)
    let mut rows: std::collections::HashMap<i32, Vec<&str>> = std::collections::HashMap::new();

    for span in &spans {
        let y_key = (span.bbox.y * 10.0) as i32; // Round to nearest 0.1
        rows.entry(y_key).or_insert_with(Vec::new).push(&span.text);
    }

    // Find rows with multiple text spans (potential table rows)
    let table_like_rows: Vec<_> = rows.iter()
        .filter(|(_, texts)| texts.len() >= 3)
        .collect();

    println!("Found {} rows with 3+ text spans", table_like_rows.len());

    if table_like_rows.len() > 5 {
        println!("✓ Detected potential table structure in spans");
        println!("  (Table formatting in markdown conversion may be missing)");
    } else {
        println!("⚠️  No clear table structure detected");
    }

    // This test documents current behavior
    // Once table extraction works, we can assert proper formatting
}

#[test]
#[ignore] // Enable once table extraction is implemented
fn test_markdown_table_syntax() {
    // Test that we output proper markdown table syntax
    println!("\n=== Testing Markdown Table Syntax ===");

    let test_file = "../pdf_oxide_tests/pdfs/diverse/2Z5VOQ6G6CMR5GMVSAAXULXHXTMJPTM2.pdf";

    if !std::path::Path::new(test_file).exists() {
        println!("⚠️  Test file not found");
        return;
    }

    let mut doc = PdfDocument::open(test_file)
        .expect("Failed to open PDF");

    let markdown = doc.to_markdown(0, &ConversionOptions::default())
        .expect("Failed to extract markdown");

    // Look for markdown table syntax
    let has_table_header = markdown.contains("| ");
    let has_table_separator = markdown.contains("|---") || markdown.contains("| --- |");

    println!("Has table header syntax: {}", has_table_header);
    println!("Has table separator: {}", has_table_separator);

    assert!(
        has_table_header && has_table_separator,
        "Expected markdown table syntax (| ... | and separator)"
    );

    println!("✅ Markdown table syntax detected");
}

#[test]
fn test_grid_detection() {
    // Test if we can detect grid-like structures
    println!("\n=== Testing Grid Detection ===");

    let test_file = "../pdf_oxide_tests/pdfs/academic/arxiv_2510.25440v1.pdf";

    if !std::path::Path::new(test_file).exists() {
        println!("⚠️  Test file not found");
        return;
    }

    let mut doc = PdfDocument::open(test_file)
        .expect("Failed to open PDF");

    let spans = doc.extract_spans(0)
        .expect("Failed to extract spans");

    // Analyze X coordinates for column detection
    let x_positions: Vec<i32> = spans.iter()
        .map(|s| (s.bbox.x * 10.0) as i32)
        .collect();

    let mut x_freq: std::collections::HashMap<i32, usize> = std::collections::HashMap::new();
    for x in x_positions {
        *x_freq.entry(x).or_insert(0) += 1;
    }

    // Find X positions that repeat (columns)
    let repeated_x: Vec<_> = x_freq.iter()
        .filter(|(_, &count)| count >= 5)
        .collect();

    println!("Found {} potential column positions", repeated_x.len());

    if repeated_x.len() >= 2 {
        println!("✓ Multi-column structure detected");
        println!("  Could indicate table or multi-column layout");
    }

    // Document findings
    println!("\n📋 Grid/table detection logic can be enhanced");
}
