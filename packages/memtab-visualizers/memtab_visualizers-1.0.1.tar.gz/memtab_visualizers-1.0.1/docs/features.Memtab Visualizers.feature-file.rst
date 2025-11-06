.. role:: gherkin-step-keyword
.. role:: gherkin-step-content
.. role:: gherkin-feature-description
.. role:: gherkin-scenario-description
.. role:: gherkin-feature-keyword
.. role:: gherkin-feature-content
.. role:: gherkin-background-keyword
.. role:: gherkin-background-content
.. role:: gherkin-scenario-keyword
.. role:: gherkin-scenario-content
.. role:: gherkin-scenario-outline-keyword
.. role:: gherkin-scenario-outline-content
.. role:: gherkin-examples-keyword
.. role:: gherkin-examples-content
.. role:: gherkin-tag-keyword
.. role:: gherkin-tag-content

:gherkin-feature-keyword:`Feature:` :gherkin-feature-content:`Memtab Visualizers`
=================================================================================

    :gherkin-feature-description:`As a developer`
    :gherkin-feature-description:`I want to quickly be able to see memtab output visually`
    :gherkin-feature-description:`So that I know what is going on with the memory usage of my application`

:gherkin-scenario-outline-keyword:`Scenario Outline:` :gherkin-scenario-outline-content:`Memtab Visualizers`
------------------------------------------------------------------------------------------------------------

| :gherkin-step-keyword:`Given` the memtab utility
| :gherkin-step-keyword:`And` valid ELF files
| :gherkin-step-keyword:`When` a **\<report\>** is requested
| :gherkin-step-keyword:`Then` a **\<report\>** shall be produced
| :gherkin-step-keyword:`And` the **\<report\>** shall contain accurate information

:gherkin-examples-keyword:`Examples:`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. csv-table::
    :header: "report"
    :quote: “

    “treemap“
    “ramtreemap“
    “memmap“
    “categorymemmap“
    “excel“
    “summary“
    “memoryprofiler“

