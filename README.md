# POSIX Utilities External Tests

This repository contains tests for various POSIX utiltiies imported from other repositories.  It
is intended for use by the [gd-posix-apps](https://github.com/matt-gretton-dann/gd-posix-apps)
project.  It is a separate repository to preserve a clear boundary for third-party IP purposes.

## Copyright and License

The main driver code is Copyright 2021, Matthew Gretton-Dann and licensed under the
[Apache 2.0 License](./licenses/Apache-2.0.txt)

The imported tests are copyrighted by their respected authors and licensed under the terms from
those authors.  The `test-driver.py --info` command will give information about a particular
test.

## Running tests

The Python script `test-driver.py` is used to run tests.  Basic usage is as follows:

```sh
./test-driver.py --executable "<EXE>" --tests "<TEST SPECIFIERS>"
```

Tests specifiers look like paths and have the general form: `<UTIL>/<SOURCE>/<TEST>/...`.  Not
all levels need to be specified so just specifying `--tests bc` will run all tests for the `bc`
utility.

Full command line options are:

| Option | Description |
| :----- | :---------- |
| `--list-tests` | Lists the tests that will be executed to standard output - will not run tests. |
| `--tests <TESTS>` | Tests to run, can be specified multiple times. |
| `--executable <EXE>` | Executable to pass to test drivers. |
| `--info` | Display information - including author, license, and copyright about the specified tests. |
| `--expected-fail <TEST>[:<FILE>]` | Specify that we expect <TEST> to fail.  <FILE> if specified gives the expected failure output.  May be specified multiple times. |
| `--expected-pass <TEST>[:<FILE>]` | We expect <TEST> to have different (but valid) output as given in <FILE>. |

## Further Documentations

The [docs](./docs/index.md) directory contains further documentation.
