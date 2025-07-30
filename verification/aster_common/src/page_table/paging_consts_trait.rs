use vstd::prelude::*;
use vstd::layout::is_power_2;

use crate::prelude::*;
use core::fmt::Debug;

verus! {

#[allow(non_snake_case)]
pub trait PagingConstsTrait: Debug + Sync {
    spec fn BASE_PAGE_SIZE_spec() -> usize;

    proof fn lemma_BASE_PAGE_SIZE_properties()
        ensures
            0 < Self::BASE_PAGE_SIZE_spec(),
            is_power_2(Self::BASE_PAGE_SIZE_spec() as int),
    ;

    /// The smallest page size.
    /// This is also the page size at level 1 page tables.
    #[inline(always)]
    #[verifier::when_used_as_spec(BASE_PAGE_SIZE_spec)]
    fn BASE_PAGE_SIZE() -> (res: usize)
        ensures
            res == Self::BASE_PAGE_SIZE_spec(),
            0 < res,
            is_power_2(res as int),
    ;

    spec fn NR_LEVELS_spec() -> PagingLevel;

    /// The number of levels in the page table.
    /// The numbering of levels goes from deepest node to the root node. For example,
    /// the level 1 to 5 on AMD64 corresponds to Page Tables, Page Directory Tables,
    /// Page Directory Pointer Tables, Page-Map Level-4 Table, and Page-Map Level-5
    /// Table, respectively.
    #[inline(always)]
    #[verifier::when_used_as_spec(NR_LEVELS_spec)]
    fn NR_LEVELS() -> (res: PagingLevel)
        ensures
            res == NR_LEVELS(),
            res == Self::NR_LEVELS_spec(),
            res > 0,
    ;

    spec fn HIGHEST_TRANSLATION_LEVEL_spec() -> PagingLevel;

    /// The highest level that a PTE can be directly used to translate a VA.
    /// This affects the the largest page size supported by the page table.
    #[inline(always)]
    #[verifier::when_used_as_spec(HIGHEST_TRANSLATION_LEVEL_spec)]
    fn HIGHEST_TRANSLATION_LEVEL() -> (res: PagingLevel)
        ensures
            res == Self::HIGHEST_TRANSLATION_LEVEL_spec(),
    ;

    spec fn PTE_SIZE_spec() -> usize;

    /// The size of a PTE.
    #[inline(always)]
    #[verifier::when_used_as_spec(PTE_SIZE_spec)]
    fn PTE_SIZE() -> (res: usize)
        ensures
            res == Self::PTE_SIZE_spec(),
            is_power_2(res as int),
            0 < res <= Self::BASE_PAGE_SIZE(),
    ;

    proof fn lemma_PTE_SIZE_properties()
        ensures
            0 < Self::PTE_SIZE_spec() <= Self::BASE_PAGE_SIZE(),
            is_power_2(Self::PTE_SIZE_spec() as int),
    ;

    spec fn ADDRESS_WIDTH_spec() -> usize;

    /// The address width may be BASE_PAGE_SIZE.ilog2() + NR_LEVELS * IN_FRAME_INDEX_BITS.
    /// If it is shorter than that, the higher bits in the highest level are ignored.
    #[inline(always)]
    #[verifier::when_used_as_spec(ADDRESS_WIDTH_spec)]
    fn ADDRESS_WIDTH() -> (res: usize)
        ensures
            res == Self::ADDRESS_WIDTH_spec(),
    ;
}

} // verus!
