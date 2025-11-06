Feature: Memtab Visualizers
  As a developer
  I want to quickly be able to see memtab output visually
  So that I know what is going on with the memory usage of my application

  Scenario Outline: Memtab Visualizers
    Given the memtab utility
    And valid ELF files
    When a <report> is requested
    Then a <report> shall be produced
    And the <report> shall contain accurate information

    Examples:
      | report          |
      | treemap         |
      | ramtreemap      |
      | memmap          |
      | categorymemmap  |
      | excel           |
      | summary         |
      | memoryprofiler  |
