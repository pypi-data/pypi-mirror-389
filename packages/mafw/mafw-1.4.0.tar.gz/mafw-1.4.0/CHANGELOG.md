# Changelog

"MAFw: Modular Analysis Framework"

## v1.4.0 (2025-11-05)

#### New Features

* (tools): introduce database tools module with key-value mapping and primary key utilities
* add citation file
#### Docs

* add documentation for new_only flag and processor parameters
* update type annotations and add peewee class references
* add advanced filtering tutorial with multiple column primary keys
* fix some typos
* add citing mafw section
#### Others

* bump version to 1.4.0
* add comprehensive tests for db tools functions

## v1.3.0 (2025-10-02)

#### New Features

* add a tool to automatically update the NOTICE.txt
* add LMPlot mixin
* (db): add model manipulations with dictionary
* extend the filter functionality
#### Fixes

* update the file regexp
* replace console printout with file writing
* (db): fix mypy errors
* (processor): orphan file pruning displaying the right number
* (sns_plotter): matplotlib backends are case insensitive
* remove warning for not found field
* the name of some operators were misspelled
#### Refactorings

* fix typing annotation
* move LogicalOP enum
#### Docs

* fix links
* add reference to CONTRIBUTING.md
* add note about conventional commit
* add missing import to a code example
* add note about hatch
* add API documentation
* include requirements section
* add note about the regexp operator in sqlite
* add note about matplotlib backend
* add note about lazy orphan file pruning
* expand filter documentation
* fix a typo
* improve the tutorial section
* add notes for eager readers
* fix mistyped prompt
* improve getting started instructions
* improve README
#### Others

* update version number
* fix a typo in a script
* change the unittest logic
* attempt to fix missing coverage
* update hash number of the maintenance image
* update MAFw version in NOTICE.txt
* add hook to update NOTICE.txt version
* update ruff to ruff-check
* change formatting
* change quotation mark style
* add unit tests for the explicit filtering

## v1.2.0 (2025-06-21)

#### New Features

* improve pandas grouping tools
* (cli): implement exit code
* (plotter): implement a new approach for the plotter
* (decorators): add suppress_warnings
#### Fixes

* (plugin): missing hook for standard tables
* (std_tables): fix issue with orphan file model and proper removal of files
* fix the order of a specific test
* remove useless conditions
* fix a bug in the usage of global filter as default value
* avoid double registration of parameters
* fix the PassiveProcessor repr method
* (type): fix a missing type annotation
* change handling of warnings
* fix a bug with python 3.11
* typo in the hatch-test definition
* modify the UnknownField
* fix a bug in the safe and for each setter
* fix two edge cases
* fix a bug in the bind_all of FilterRegister
* fix two bugs in Filter
* missing steering file setting
* missing steering file setting
* remove unused fixture
* fix a bug in the MAFwGroup main
* add exception for edge cases
* (decorators): add missing docstring
#### Docs

* remove sphix-prompt
* add a basic readme file to the plugin sub-project.
* add the test subsection
* add the tutorial section
* include installation instructions
* fix wrong indentation in a code-block
* Include the code snippets directly
* update db general documentation
* (db): improve filter API doc
* (db): improve filter API doc
* fix a broken reference
* update module documentation
* update references in the documentation
* (general): replace code snippet from test
#### Others

* add optional environment
* minor changes
* add sphix_prompt to the doc environment
* modify test extra dependencies and options
* improve test environment
* include coverage report
* (release): prepare for v1.2.0
* add copyright PyCharm configuration
* update copyright headers across source files
* update license
* add comments for literal include in doc
* remove unused code
* ruff format
* (type): improve typing annotation for some decorators.
* (type): add type ignore
* fix typo
* modify the import strategy
* rename SNSGenericPlotter to SNSPlotter
* add pragma no cover statements to abstract methods
* add pragme no cover statments to abstract methods
* remove test processor
* (integration): improve the integration test to make it more realistic
* minor improvements to the plugin processors
* final implementation of full integration
* change the scope of a fixture
* first version of the integration test
* mark integration test with @pytest.mark.integration_test
* improve test suite for processor
* improve test for optional dependencies
* add test suite for pandas tools
* add test suite for file_tools
* remove old test suite for db
* add test suite for wizard
* add test suite for database trigger
* add test suite for fields
* add test suite for db_model
* remove db_types from coverage
* improve test suite for toml tools
* improve test suite for db filter
* improve test suite for toml tools
* improve test suite for runner
* improve test suite for mafw_exe
* improve test suite for sns_plotter
* improve test suite for decorators
* improve test suite for optional dependencies in sns plotter
* add test suite for abstract_plotter module
* improve test suite for plotter
* improve test suite for std table
* improve test suite for plugin manager
* add test suite for the console ui interface
* add test suite for the abstract ui interface
* improve test suite for rich based ui interface
* improve test suite for timer
* improve test suite for importer
* improve test suite for enumerators
* improve test suite for decorators
* improve test suite for active

## v1.1.0 (2025-05-28)

#### New Features

* (db): extension to other DBs
#### Fixes

* (test): add sorted to the file list
#### Others

* (env): add a types environment, set uv as installer
* (deps): loose the dependency requirements
* bump version number to 1.1.0

## v1.0.0 (2025-04-07)

#### Others

* update version number
* remove old CEE CI config file

## v1.0.0rc6 (2025-04-07)

#### New Features

* add auto-commit argument
* add function to commit changelog changes
* add function to retrieve last tag
* add function to retrieve last commit message
* change return values
* add silent option
* add CLI options
* add retry condition to the basic jobs
* add logic to skip unittest when no relevant changes.
* add unittest partial exclusion from merge request.
#### Fixes

* change master to main as target branch.
#### Others

* update version number
* remove debug print outs
* typing and documentation
* modify hook name

## v1.0.0rc5 (2025-04-04)

#### Fixes

* disabling SSL verification
#### Others

* version update

## v1.0.0rc4 (2025-04-04)

#### Fixes

* add missing proxy declaration for JRC
#### Others

* version update

## v1.0.0rc3 (2025-04-04)

#### New Features

* add release cloning job
#### Others

* version update

## v1.0.0rc2 (2025-04-04)

#### New Features

* add rules as in CEE
* add package_local_publishing
* add package_build job
* restore the LISA jobs
* try to run unit-test with hatch
* debug private CI/CD
* implement the maintenance stage
#### Fixes

* scans not scan
* re-add scan
* move the before_script in the job definition.
* stage order
* add missing export of PROXY variables
* change the name of the scheduled pipelines token
* adjust page rule
* change order of conditions
* add sha signature
* debug retry_pipelines
* add exclusion criteria to all not maintenance jobs
* add private token
#### Others

* version update
* restore full unittest
* rename some jobs for consistency
* remove debug ls

## v1.0.0rc1 (2025-03-31)

#### New Features

* add latest release and modify coverage badge
* add the possibility to generate URL from code.europa.eu
* add the cov-xml command
* add latex target document
#### Fixes

* wrong path
#### Refactorings

* (test): improve some plotter tests
* (plotter): modify the keyword attributes
#### Docs

* add badges and remove todo
* fix conflict
* revise the general and the API documentation
* polish general documentation
* typo fixing
* add reference to the PDF documentation
* fix issue with missing reflection image
* update documentation
* change from code block to screenshot
* change tabs to tab-set
* add external links
* add introduction
* change footnotes to autonumbering
* Remove unexpected word
* improve general documentation
#### Others

* update version number
* add version number (~=) to direct dependencies
* add types stubs
* add sphinx-design
* update license
* update version number to 0.0.5
* add coverage regexp
* implement the CI for the code.europa.eu
* fix licence declaration
* update the issue base link
* update the project urls
* update version number
* update documentation link
* ruff format
* update copyright statement
* (documentation): fix typos and style
* (plotter): implement seaborn mocking

## v0.0.4 (2025-01-21)

#### New Features

* add pages deployment
* add pages deployment
* (db): add file delete trigger to PlotterOutput
* (db): change OrphanFile model
* (db): change OrphanFile model
* (plotter): implement customize_plot
* (plotter): implement the CatPlot
* (plotter): implement the DisPlot
* (plotter): implement the RelPlotter
* (plotter): add facet_grid attribute
* (plotter): add FromDataset data retriever
* (plotter): implement HDF data retriever, slicing and grouping
* (db): add new_only setter
* (plotter): preliminary implementation
* (decorators): add decorators for optional dependencies
* (examples): add an example of concrete file importer
* (library): add the basic importer processor
* (library): implement the FilenameParser
* (library): implement FilenameElement
* (mafw_exe): add warning catcher
* (examples): add examples to compare for and while loop
* (processor): implement the _execute_while_loop
* (decorators): implement looper decorators
* (processor): implement the check for overloaded and super methods.
* (processor): implement the use of loop type enumerator
* (enumerators): add the LoopType enumerator
#### Fixes

* (library): fix a bug in the FilenameElement
* (toml_tools): fixing bug with boolean items
* (coverage): change the test scripts
* fix a static typing issue
#### Performance improvements

* ci
#### Refactorings

* (documentation): include svg instead of dot files
* replace pytest with hatch test
* (plotter): modify test suite
* (plotter): modify test suite
* (plotter): change inheritance metaclass
* (plotter): improve code quality
* (plotter): Modify the SQL retriever mixin
* (processor): change the method with super check
* (plugin_manager): remove the load_external_plugin flag
* (plugin_manager): make the plugin_manager singleton
* (processor): replace log.warning with warnings.warn
#### Docs

* (plotter): add the general documentation about plotter
* add some API documentation.
* add doc_plotting page
* (plotter): API documentation
* fix some references
* fix typo in Optional parameter type
* (importer): implement the general documentation
* add the general documentation about execution workflow
* (examples): modify the description of the looper parameter.
* (processor): modify the execution workflow
#### Others

* (pyproject): add explicit types-seaborn to dev
* include pandas[hdf5] to seaborn feature
* (tests): add seaborn extra dep to hatch-test
* add seaborn optional dependency
* add coverage html report
* bump version number to v0.0.4
* (ci): remove two todos
* (documentation): remove todo about PlotterOutput
* add external links
* add nitpick_ignore
* (processor): API documentation
* (test): add missing looper to a processor
* (documentation): add mafw logo
* apply ruff format
* remove unused type ignore
* doc type
* (test): remove unused imports
* (toml_tools): remove white spaces
* (plotter): add test for standard table PlotterOutput
* (plotter): add test for looping plotter
* (plotter): add direct plot
* (plotter): mixin arguments in constructor and existing output
* (importer): add test for documentation purpose
* (mafw_exe): additional processor and warning catcher
* (plugin_manager): inclusion of additional processors

## v0.0.3 (2024-12-17)

#### New Features

* improve the update changelog script
#### Fixes

* (ci): fix a bug related to the removal of the type env
* fix a typo in the script entry point
#### Refactorings

* improve quality.
#### Docs

* add contributing section
#### Others

* modify the pre-push command
* removed pyproject-pre-commit
* change the pre-commit config
* update version number
* attempt to use pip cache

## v0.0.2 (2024-12-15)

#### New Features

* (mafw_exe): add db group and wizard command
* (db): add db_wizard module
* (decorators): implement a orphan_protector decorator
* (db): modify the PlotterOutput table
* (db): implement the FileNameListField
* (db): implement std_upsert and std_upsert_many
* (db): implement external library standard tables
* (db): add standard tables
* (processor): remove filter_list and rename get_item_list
* (db): change signature of FileChecksumField
* (db): implement the automatic linking a fields
* (db): add the FilterRegister
* (processor): modify filter loading
* (db): improve the Filter
* (processor): add support for filter registration
* (db): implement the Filter
* (db): implement the FileChecksumField
* (db): implement the FileNameField
* (db): add possibility to add when conditions to triggers
* (db): add helper function to and and or conditions
* (db): add support for trigger generation to MAFwBaseModel
* (db): add the trigger drop
* (mafw_errors): add exception for missing SQL statements
* (db): add Trigger class
* (examples): modify the FillTableProcessor
* (doc): add sphinx_code_tabs to the extensions
* (plugins): add FillTableProcessor
* (processor): implement parameter type conversion
* (examples): add an example of DB processor
* (tools): add toml encoder for Path
* (runner): add database configuration to the ProcessorList
* (toml): add generate_hexdigest_from_files
* (decorators): add database required decorator
* (mafw_errors): add MissingDatabase
* (processor): add database to the ProcessorList class
* (processor): add database to the Processor class
* (mafw_exe): add db configuration options to steering command
* (db): add db_scheme
* (db): add test for db configuration to toml
* (db): add test for db configuration to toml
* (db): add default configuration parameters
* (mafw_errors): add UnknownDBEngine
* (db): Implement the basic db model
#### Fixes

* (db): fix a small bug in the multi_primary example
* (decorators): fix wrong wrapping of database_required.
* (db): fix a bug with the trigger status
* (db): fix a bug in the drop table
* (processor): fix a bug with the closure of the database
* (tests): fix several SqliteDatabase connection
* (db): fix add_when that was not returin self.
* (db): fix a bug with the implementation og getattr
* typo in the doc dependency
* (toml): fix problem with escaping of windows path
* (tools): add missing hashlib import
* (processor): fixed creation of a db instance
* (processor): fix a bug in the assignement of database_conf
* (processor): fix a bug in the validate_database_conf
* (processor): fix missing validate_database_conf meth
* (db): set no inspection for playhouse
* (db): set no inspection for playhouse
#### Refactorings

* (db): change dump_models signature
* add view for testing
* (db): move the dump model test to a separate test unit
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* add typing hints
* (active): add typing hints
* change the definition of foreign key
* (filter): change the definition of the advanced model
* (timer): add typing hints
* (processor): improve decorator annotation
* (processor): implement changes for static typing
* (processor): implement changes for static typing
* (processor): implement changes for static typing
* (processor): implement changes for static typing
* (processor): implement changes for static typing
* (decorators): annotating ensure_parameter_registration
* (processor): change to comply to static typing
* (processor): apply no_implict_optional
* (processor): change annotation
* (db): adapt remove_widow and verify_checksum
* (db): improve the std_upsert signature
* (db): improve trigger interface
* (db): change the add_sql signature
* (processor): change the way the filters are loaded from conf file
* (db): move Trigger to trigger module
* (db): adopt new naming convention for tables
* (db): move Trigger to trigger module
* (db): adopt new naming convention for tables
* (db): change the MAFwBaseModel
* (db): rename to_sql in create
* (db): rename to_sql in create
* (doc): add a substitutions.rst
* (plugins): change the name of a processor
* (doc): add external links extension
* (processor): remove the atomic transaction creation
* (processor): add database and database_conf to Processor constructor
* (processor): add database and database_conf to Processor constructor
#### Docs

* remove todo concerning mafw db wizard
* (db): add section on the database reflection
* fix typo
* (mafw_exe): add API documentation
* (db): improve api doc of db_wizard
* fix nitpicky missing refs
* fix a missing docstring
* (db): add general documentation about orphan files
* (toml): update documentation.
* update general documentation
* fix typos
* update API documentation
* (db): add documentation about multi column pk / fk
* (db): update standard table documentation
* (db): add documentation about standard tables
* (db): update the documentation
* (filter): add documentation image
* (filter): update the API documentation
* (db): add section on filters
* (db): add documentation to the db_filter module
* (db): add documentation about Filter api
* (db): add section on custom fields
* (db): add warning box about triggers with MySQL and PostreSQL
* (db): add section on triggers
* add extlinks for gitlab issue
* (db): add signal example
* (db): add a section about triggers.
* (db): add missing docstring
* (database): add the section about running the FillFileTableProcessor
* (database): add section about database processors
* (database): add description of peewee
* (tutorial): add some text
* (examples): add documentation to FillTableProcessor
* add a tutorial page
* add note about the use of custom types as parameters
* fix nitpicky warnings
* fix nitpicky warnings
* add section about parameter typing
* (processor): improve module doc
#### Others

* add pre-commit config
* add pre-commit config
* add pre-push script
* add ruff scripts
* add scripts and dependency
* add mypy to CI
* include different version of python
* modify the pyproject.toml
* make the dev environment a matrix with different python versions.
* remove hardcoded env path
* update gitlab-ci
* add Deprecation
* add changelog file
* (doc): add external links extension
* (doc): add sphinx_code_tabs
* add peewee
* update changelog
* fix nitpick missing refs
* update repo version to v0.3.6
* update changelog
* update changelog
* update changelog
* update changelog
* add todo
* update changelog
* update changelog
* update changelog
* update changelog
* (doc): add classes to the nitpicky list
* update changelog
* (doc): add UserDict to nitpick_ignore
* update changelog
* (doc): update some line numbers
* updated changelog
* updated changelog
* (doc): use :link: role
* (db): add warning message
* (doc): add peewee link
* (processor): add database property
* (db): add automatically generated exception
* (doc): add some missing classes to nitpick_ignore
* (doc): add peewee.Model to nitpick_ignore
* (test_mafw_exe): remove useless duplicated assert
* (test_mafw_exe): remove useless runner
* bumped version number
* apply ruff format
* apply ruff format
* apply ruff format to all project files.
* apply ruff format to all project files
* apply ruff check to all projects
* add some comments to disable inspections
* (tools): fix wrong link in docstring
* (tools): rename widowed in widow
* (db): remove some warnings
* (db): remove unresolvedreferences for playhouse
* (db): add noinspection for _meta
* (examples): change formatting
* (mafw_exe): add test for the db wizard
* (db): add test suite for the db wizard
* (db): add full funcionality of orphan file removal
* (db): add test for FileNameListField
* (db): implement test for file_tools
* (filter): adapt to new default behavior of filter
* (filter): adapt to the new filter
* (db): add additional test on signals.
* (db): add test of the signal functionality
* (db): add test on trigger with when conditions
* (db): add test for automatic trigger creation
* (db): add test for drop and modification of triggers
* (db): add trigger tests
* (toml): add test for encoding of Path
* (processor): add test for processors with database required decorator
* (decorators): add test for database_required
* (processor): test the validate_database_conf
* (db): add test to check connection failure
* (test_mafw_exe): add test for steering options
* (db): add tests for the basic functionality

## v0.0.1 (2024-11-22)

