# ================================================================
# Feature 3 — Extract documents with embedded tables + surrounding text
# ================================================================
Feature: Extract documents (PDF/DOCX) that contain tables and surrounding text to Markdown
  As a knowledge engineer
  I want tables and accompanying narrative preserved in order
  So that meaning and context are not lost

  @pdf_with_tables
  Scenario: Convert a PDF with tables and descriptive paragraphs
    Given I have "Policy_Report.pdf" which includes multiple tables, captions, and paragraphs before and after each table
    When I convert it to Markdown
    Then the output Markdown preserves the original order: heading → paragraph → table → caption → paragraph
    And each table is rendered with a Markdown caption in italics directly below the table when present
    And cells with line breaks are preserved using <br> or explicit line breaks in Markdown
    And any footnotes are collected and appended after the section with reference markers
    And the metadata includes the table count and a list of table titles or inferred captions

  @docx_with_tables
  Scenario: Convert a DOCX with mixed content (text + tables + images)
    Given I have "HR_Guide.docx" containing headings, normal text, tables with merged cells, and inline images
    When I convert it to Markdown
    Then heading levels are preserved (H1..H4)
    And tables are converted to valid Markdown with merged cells flattened using repeated values or notes
    And inline images are extracted or referenced with alt text and stored URIs
    And the narrative text before and after tables is preserved in sequence

  @integrity
  Scenario: Verify consistency between table text and surrounding narrative
    Given a document contains a paragraph referencing values inside a nearby table
    When I convert it to Markdown
    Then the table appears before the paragraph that references "the table above" if that was the original order
    And numeric values in the table are kept as plain text without localization changes
    And the paragraph maintains the same reference wording

  @edge_cases
  Scenario Outline: Handle edge cases in embedded tables
    Given a document "<doc>" has a table with "<case>"
    When I convert it to Markdown
    Then the output remains valid Markdown and includes a note about "<note>"

    Examples:
      | doc                 | case                    | note                                |
      | Complex.pdf         | merged header cells     | merged cells approximated in rows   |
      | Catalog.docx        | multi-line cells        | line breaks preserved               |
      | Financials.docx     | numeric alignment       | alignment not guaranteed in MD      |
      | NarrowMargins.pdf   | very wide columns       | columns may wrap or be truncated    |

  @validation
  Scenario: Emit validation artifacts for QA
    Given the conversion finished successfully
    When I request validation artifacts
    Then I receive:
      | artifact                         |
      | a JSON index of detected tables  |
      | per-table column type inference  |
      | per-table row/column counts      |
      | a diffable Markdown file         |
      | the raw text extraction snapshot |

  @table_statistics
  Scenario: Extract statistics from tables in PDF documents
    Given I have "sample_document_airplane.pdf" containing a table with numerical and categorical data
    When I convert it to Markdown
    Then the output includes a statistics section after the table
    And the statistics include min, max, mean, and std deviation for numerical columns
    And the statistics include mode and frequency distribution for categorical columns
    And the output shows a sample of maximum 5 rows from the original table
    And the metadata includes total row count and column count

  @table_statistics @docx
  Scenario: Extract statistics from tables in Word documents
    Given I have "HR_Guide.docx" containing tables with employee data
    When I convert it to Markdown
    Then each table is followed by its computed statistics
    And numerical columns show min, max, mean, std
    And categorical columns show mode and frequency counts with percentages
    And duplicate row counts are reported if present

  @table_statistics @multiple_tables
  Scenario: Handle multiple tables with statistics in one document
    Given I have "Policy_Report.pdf" with 3 different tables
    When I convert it to Markdown
    Then each table has its own statistics section
    And the document metadata includes statistics for all 3 tables
    And each table is sampled to 5 rows maximum in the output
