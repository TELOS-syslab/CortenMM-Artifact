# Verification Walkthrough

## Overview

CortenMM is a memory management system implemented in Rust with Verus formal verification. It provides a page table architecture supporting RCU (Read-Copy Update) and read-write lock concurrency strategies, with strong guarantees about memory safety and thread safety.

## Project structure

The code mostly lies in the lock-protocol folder.

```
lock-protocol/
├── src/
│   ├── exec/                     # Execution implementations
│   │   ├── mod.rs                # Mock implementations and test utilities
│   │   ├── rcu/                  # RCU (Read-Copy Update) implementation
│   │   └── rw/                   # Read-Write lock implementation
│   ├── spec/                     # Specifications
│   │   ├── mod.rs
│   │   ├── common.rs             # Common utilities
│   │   ├── rcu/                  # RCU specifications
│   │   ├── rw/                   # Read-write lock specifications
│   │   ├── sub_pt/               # Sub-page table specifications
│   │   └── utils.rs              # Specification utilities
│   ├── mm/                       # Memory management core
│   │   ├── mod.rs                # Memory management module definitions
│   │   ├── frame/                # Physical frame management
│   │   ├── page_table/           # Page table operations implementation
│   │   ├── page_prop.rs          # Page properties and permissions
│   │   └── vm_space.rs           # Virtual memory space management
│   ├── sync/                     # Synchronization primitives
│   ├── task/                     # Task and preemption management
│   └── x86_64/                   # x86-specific code
│   ├── lib.rs                    # Module declarations
│   ├── prelude.rs                # Common definitions
│   ├── helpers/                  # Utility functions
├── Cargo.toml
└── README.md
```

### Core Components

1. **Read-Write locks**

    * Specifications and proof for executable code for read-write locks are in `src/spec/rw` and `src/exec/rw/` respectively.
    * The tree specification is at `src/spec/rw/tree.rs,` and the atomic (mutual-exclusion) specification is at `src/spec/rw/atomic.rs`. Specifications of the current version may differ slightly from the description in the paper, as we have made numerous updates to our proof.
    * We prove that the tree specification refines the atomic spec in `src/spec/tree_refines_atomic.rs` by showing that the transitions in the tree specs correspond to the atomic spec's transitions or no_op.

2. **RCU** (`src/exec/rcu/`, `src/spec/rcu`)

    * Specifications and proof for executable code for RCU (Read-Copy Update) are in `src/spec/rcu` and `src/exec/rcu/` respectively.
    * The tree specification is at `src/spec/rcu/tree.rs`, and the atomic (mutual-exclusion) specification is at `src/spec/rcu/atomic.rs`.
      The RCU implementation provides lock-free read access while ensuring thread safety through copy-on-write semantics. For example, the possible states of PT pages are changed to `WriteUnlocked`, `WriteLocked`, or `InProtocolWriteLocked`. `WriteUnlocked` is a combination of `Unlocked` and `ReadLocked` in the paper. The `Unallocated` is removed because its effect can be achieved through carefully token exchange operations. We will make necessary revisions to the paper.
    * We prove that the tree specification refines the atomic spec in `src/spec/rcu/tree_refines_atomic.rs` by demonstrating that RCU operations maintain mutual exclusion properties while allowing concurrent reads.

3. **Cursor operations** (`src/mm/page_table/cursor,` `src/spec/sub_pt`)

    * Specifications and proof for executable code for cursor operations are in `src/spec/sub_pt` and `src/mm/page_table/cursor` respectively.
      We model the operations for memory on a flat array instead of the real physical memory in `src/exec/mod.rs`.
    * Cursor operations enable safe traversal and modification of page table structures:
        - **`map`**: Maps a virtual address range to a physical page, handling page table allocation and PTE updates
        - **`unmap` (take_next)**: Removes the first mapped page in a specified range, returning the unmapped page information and advancing the cursor
        - **`mark`**: Updates page properties without changing the physical mapping
    * The cursor implementation supports multi-level page table traversal and ensures that modifications maintain page table consistency.

### Run Verification

To run the verification, please refer to `README.md`. Basically, you can use the following commands:

```bash
cargo xtask bootstrap
cargo xtask compile --targets vstd_extra
cargo xtask compile --targets aster_common
cargo xtask verify --targets lock-protocol
```

### Limitations

There are unfinished proofs, but they do not break the claims in the paper. The RW, RCU, and Cursor operations are verified separately, allowing us to write verification independently. We will fix missing proofs and make them more unified in the next version, so please refer to the upstream [vostd](https://github.com/asterinas/vostd/tree/main/lock-protocol) for future updates.
