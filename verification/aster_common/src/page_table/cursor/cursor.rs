use vstd::prelude::*;

use core::marker::PhantomData;
use core::ops::Range;

use crate::prelude::*;

verus! {

#[rustc_has_incoherent_inherent_impls]
pub struct Cursor<'a, M: PageTableMode> {
    /// The lock guards of the cursor. The level 1 page table lock guard is at
    /// index 0, and the level N page table lock guard is at index N - 1.
    ///
    /// When destructing the cursor, the locks will be released in the order
    /// from low to high, exactly the reverse order of the acquisition.
    /// This behavior is ensured by the default drop implementation of Rust:
    /// <https://doc.rust-lang.org/reference/destructors.html>.
    pub guards: [Option<PageTableNode>; 4],
    /// The level of the page table that the cursor points to.
    pub level: PagingLevel,
    /// From `guard_level` to `level`, the locks are held in `guards`.
    pub guard_level: PagingLevel,
    /// The current virtual address that the cursor points to.
    pub va: Vaddr,
    /// The virtual address range that is locked.
    pub barrier_va: Range<Vaddr>,
    pub preempt_guard: DisabledPreemptGuard,
    pub phantom: PhantomData<&'a PageTable<M>>,
}

pub enum PageTableItem {
    NotMapped { va: Vaddr, len: usize },
    Mapped { va: Vaddr, page: DynPage, prop: PageProperty },
    PageTableNode { page: DynPage },
    #[allow(dead_code)]
    MappedUntracked { va: Vaddr, pa: Paddr, len: usize, prop: PageProperty },
}

} // verus!
