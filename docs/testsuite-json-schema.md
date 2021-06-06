# Testsuite JSON Schema

The testsuites are described by a set of JSON files.  This document describes those JSON files.

## Mapping Utilities to their testsuites

In the top level directory the [testsuites.json](../testsuites.json) file describes a mapping from
each utility to the testsuites for that utility.

This is a fairly simple schema.  Each element in the top-level JSON array is an object with the
following properties:

| Property | Description |
| :------- | :---------- |
| utility  | Name of the utility. |
| testsuites | Array of testsuite names. |

Testsuite names should match to a directory of the same name in the [testsuites](../testsuites/)
directory.

All fields are mandatory.

The schema file is at [schema/testsuites.schema.json](../schema/testsuites.schema.json).

## Listing tests in a testsuite

In each testsuite directory there is a `testsuite.json` file which describes the contents of the
testsuite.  It contains a top-level object with the following properties:

| Property | Mandatory/Optional | Description |
| :------- | :----------------- | :---------- |
| title | Mandatory | Human readable title. |
| copyright | Mandatory | Copyright string. |
| license | Mandatory | SPDX License identifier |
| license-file | Optional | Path to license file if not a standard license text. |
| url | Mandatory | URL of original source |
| hash | Optional | Hash or other identifier of revision of code used to import. |
| command | Optional | Array of command line components to call to run tests. |
| expected-output | Optional | Path to file of expected output. |
| expected-error | Optional | Path to file of expected error. |
| tests | Mandatory | Array of test names, or fuller test details. |
| shell | Optional | Should the command be passed to the shell.  Default: false |

The `tests` property is an array of testname strings, or test objects which have the following
properties:

| Property | Mandatory/Optional | Description |
| :------- | :----------------- | :---------- |
| command | Optional | Array of command line components to call to run tests, overrides any higher level. |
| expected-output | Optional | Path to file of expected output, overrides any higher level. |
| expected-error | Optional | Path to file of expected error, overrides any higher level. |
| error-test | Optional | Boolean to indicate if this is an error test, default false. |
| tests | Optional | Array of subtests. |
| shell | Optional | Should the command be passed to the shell.  Default: false |

The schema file is at [schema/testsuite.schema.json](../schema/testsuite.schema.json).

## Variable expansion

The values of the properties `license-file`, `command`, `expected-output`, `expected-error` are
all subject to variable expansion.

Variables are named as per standard UNIX Shell naming by `${name}`.

The following variables are defined:

| Variable name | Contents |
| :------------ | :------- |
| ${utility} | Utility executable path.  |
| ${python} | Python path  |
| ${dir_sep} | Directory separator  |
| ${test_suite_path} | Path to the testsuite root.  |
| ${test_full_name} | Full name of the test.  |
| ${test_leaf_name} | Lead name of the test.  |

## Calculating test properties

Every test has the following properties - even though they may not be identified directly alongside
the test:

 * command
 * expected-output
 * expected-error
 * error-test
 * shell

To find the value of a property for a particular test a walk up the tree of containing objects is
done starting at the test's definition.  The first definition of that property's value is then
used.

## Test names

Test names are calculated as the path from the root of the testsuite to the test name using
${dirsep} to separate the components.
