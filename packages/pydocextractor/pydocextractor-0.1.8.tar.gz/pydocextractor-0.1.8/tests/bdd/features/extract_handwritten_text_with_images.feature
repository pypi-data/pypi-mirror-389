# ============================================
# Feature — Extract Handwritten Text and Images from PDF
# ============================================
Feature: Extract PDF with handwritten text and images to Markdown
  As a user of the pyDocExtractor library
  I want PDFs containing handwritten text and images to be converted to Markdown
  So that I can capture OCR-extracted handwritten content along with visual context

  Background:
    Given I have the pyDocExtractor service configured with LLM enabled
    And the precision level is set to 2 (BALANCED with LLM image description)

  @handwritten @llm @images
  Scenario: Convert PDF with handwritten text and images to Markdown
    Given I have a PDF file "handwriten_text_and_image.pdf" with MIME "application/pdf"
    And the PDF contains handwritten text and embedded images
    When I convert the file to Markdown with LLM enabled
    Then the converter produces a Markdown document
    And the Markdown output contains the word "leonardo" (case-insensitive)
    And the Markdown output contains the word "hate" (case-insensitive)
    And the Markdown output contains the word "meeting" (case-insensitive)
    And the Markdown output contains the word "like" (case-insensitive)
    And the Markdown output contains the word "skate" (case-insensitive)

  @handwritten @llm @content_verification
  Scenario: Verify all required keywords are extracted from handwritten PDF
    Given I have a PDF file "handwriten_text_and_image.pdf" with MIME "application/pdf"
    When I convert the file to Markdown with LLM enabled
    Then the Markdown output should contain all of the following keywords:
      | keyword   |
      | leonardo  |
      | hate      |
      | meeting   |
      | like      |
      | skate     |

  @handwritten @structure
  Scenario: Verify structure preservation in handwritten PDF conversion
    Given I have a PDF file "handwriten_text_and_image.pdf" with MIME "application/pdf"
    When I convert the file to Markdown with LLM enabled
    Then the Markdown output contains text content
    And the Markdown output contains image references or descriptions
    And the document structure is preserved with proper formatting

  @handwritten @quality
  Scenario: Convert handwritten PDF with LLM image description
    Given I have a PDF file "handwriten_text_and_image.pdf" with MIME "application/pdf"
    When I convert the file to Markdown with LLM enabled
    Then the Markdown output contains the word "leonardo" (case-insensitive)
    And the Markdown output contains the word "hate" (case-insensitive)
    And the Markdown output contains the word "meeting" (case-insensitive)
    And the Markdown output contains the word "like" (case-insensitive)
    And the Markdown output contains the word "skate" (case-insensitive)
    And the conversion quality is acceptable for LLM-described content
