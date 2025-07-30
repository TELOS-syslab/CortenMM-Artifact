use vstd::prelude::*;

verus! {

/// Virtual addresses.
pub type Vaddr = usize;

/// Physical addresses.
pub type Paddr = usize;

/// The level of a page table node or a frame.
pub type PagingLevel = u8;

} // verus!
