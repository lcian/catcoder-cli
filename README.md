# catcoder-cli

This is a Python package that provides the `ccc` CLI tool to interact with the Catcoder platform for the [Cloudflight Coding Contest](https://register.codingcontest.org/).

## Installation

```
pip install ccc
```

## Usage

1. Use `ccc setup` to set up your credentials for CatCoder:

```
ccc setup <contest_id> <session_cookie> <xsrf_token>
```

where:

- `contest_id` is the ID of the contest you are participating in (can be found in the URL when you access the contest from CatCoder),
- `session_cookie` is the value of the `SESSION` cookie in your browser (can be found using the developer tools),
- `xsrf_token` is the value of the `XSRF-TOKEN` cookie in your browser (can be found using the developer tools) – could be empty, sometimes it's not enabled.

2. Use `ccc gen` to start working on a new level of the current contest.

   This will detect the current level you are working on, create a new directory containing the input files and a Python solution template, and open the problem statement in your browser.

3. Implement your solution and run it to produce the `.out` files.

4. Use `ccc submit` to submit your solutions to CatCoder.

   You will get immediate feedback on whether or not your submissions are accepted.

   You will also be able to upload your code if you want to.
