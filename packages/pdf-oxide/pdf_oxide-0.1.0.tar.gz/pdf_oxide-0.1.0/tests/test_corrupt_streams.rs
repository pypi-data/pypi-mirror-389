/// Integration tests for PDFs with corrupt stream data
///
/// These tests verify that the library can handle PDFs with:
/// - Corrupt FlateDecode streams (deflate decompression errors)
/// - Partial stream data extraction
/// - Best-effort text recovery from damaged files
///
/// Tests follow TDD approach: written before implementation to capture expected behavior.
use pdf_oxide::PdfDocument;

/// Test TYLWGSX5OYKE27DHTQXUJTBMKMHMKY3B.pdf - corrupt FlateDecode stream
/// Expected: Extract partial text using best-effort recovery
#[test]
fn test_corrupt_flatedecode_partial_recovery() {
    let path = "../pdf_oxide_tests/pdfs/mixed/TYLWGSX5OYKE27DHTQXUJTBMKMHMKY3B.pdf";

    // Test 1: Document opens successfully despite corrupt streams
    let mut doc = PdfDocument::open(path).expect("Should open PDF despite corrupt stream data");

    // Test 2: Correctly detects page count
    let page_count = doc
        .page_count()
        .expect("Should get page count despite corrupt streams");
    assert_eq!(page_count, 1, "Should detect 1 page");

    // Test 3: Extract text with best-effort recovery
    // PyMuPDF extracts 1,924 chars, we should get at least 50% (962 chars)
    // Currently extracts 0 chars - this test should initially FAIL
    let text = doc
        .extract_text(0)
        .expect("Should extract text with best-effort recovery");

    let char_count = text.len();
    println!("Extracted {} chars from corrupt PDF", char_count);

    // Target: At least 50% of PyMuPDF's extraction (962 out of 1,924 chars)
    assert!(
        char_count >= 962,
        "Should extract ≥50% of text (≥962 chars) using partial recovery, got {} chars",
        char_count
    );

    // Bonus: Ideally >75% (1,443 chars)
    if char_count >= 1_443 {
        println!("✓ Excellent recovery: {} chars (>75% of reference)", char_count);
    } else if char_count >= 962 {
        println!("✓ Good recovery: {} chars (50-75% of reference)", char_count);
    }
}

/// Test that we don't crash on other corrupt stream scenarios
#[test]
fn test_corrupt_stream_graceful_degradation() {
    let path = "../pdf_oxide_tests/pdfs/mixed/TYLWGSX5OYKE27DHTQXUJTBMKMHMKY3B.pdf";

    let mut doc = PdfDocument::open(path).expect("Should open corrupt PDF");

    // Should not panic, even if extraction fails
    let result = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
        let _ = doc.extract_text(0);
    }));

    assert!(result.is_ok(), "Should not panic on corrupt streams");
}
