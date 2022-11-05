# Python database package for rorm

This package aims to implement the Python Database API Spec v2.0 from
[PEP 249](https://peps.python.org/pep-0249/) using the Rust ORM
[`rorm`](https://github.com/myOmikron/drorm) together with
[Maturin](https://www.maturin.rs/) in pure Rust. It's designed as a
async database driver for SQLite, MySQL and Postgres. However, sync
functions of the async functions will be provided, too.
