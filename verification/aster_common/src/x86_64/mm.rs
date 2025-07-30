use vstd::prelude::*;
use vstd_extra::prelude::*;
use crate::mm::Vaddr;
use core::ops::Range;
use crate::prelude::{Paddr, CachePolicy};

extern_const!(
/// Page size.
pub PAGE_SIZE [PAGE_SIZE_SPEC, CONST_PAGE_SIZE]: usize = 4096);

extern_const!(
/// The maximum number of entries in a page table node
pub NR_ENTRIES [NR_ENTRIES_SPEC, CONST_NR_ENTRIES]: usize = 512);

extern_const!(
/// The maximum level of a page table node.
pub NR_LEVELS [NR_LEVELS_SPEC, CONST_NR_LEVELS]: usize = 4);

extern_const!(
/// Parameterized maximum physical address.
pub MAX_PADDR [MAX_PADDR_SPEC, CONST_MAX_PADDR]: usize = 0x8000_0000);

extern_const!(
pub MAX_NR_PAGES [MAX_NR_PAGES_SPEC, CONST_MAX_NR_PAGES]: u64 = (CONST_MAX_PADDR / CONST_PAGE_SIZE) as u64);

extern_const!(
/// The maximum virtual address of user space (non inclusive).
pub MAX_USERSPACE_VADDR
    [MAX_USERSPACE_VADDR_SPEC, CONST_MAX_USERSPACE_VADDR] : Vaddr =
    0x0000_8000_0000_0000_usize - CONST_PAGE_SIZE);

extern_const!(
/// The kernel address space.
/// There are the high canonical addresses defined in most 48-bit width
/// architectures.
pub KERNEL_VADDR_RANGE
    [KERNEL_VADDR_RANGE_SPEC, CONST_KERNEL_VADDR_RANGE] : Range<Vaddr> =
    0xffff_8000_0000_0000_usize..0xffff_ffff_ffff_0000_usize);

verus! {

/// Activates the given level 4 page table.
/// The cache policy of the root page table node is controlled by `root_pt_cache`.
///
/// # Safety
///
/// Changing the level 4 page table is unsafe, because it's possible to violate memory safety by
/// changing the page mapping.
#[verifier::external_body]
pub unsafe fn activate_page_table(root_paddr: Paddr, root_pt_cache: CachePolicy) {
    unimplemented!()
}

#[verifier::external_body]
pub fn current_page_table_paddr() -> Paddr {
    unimplemented!()
}

} // verus!
