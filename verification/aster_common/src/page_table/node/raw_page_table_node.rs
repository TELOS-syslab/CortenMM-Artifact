use vstd::prelude::*;

use core::marker::PhantomData;

use crate::prelude::{PageTableEntry, PagingConsts, PagingLevel};
use crate::prelude::Paddr;

verus! {

#[rustc_has_incoherent_inherent_impls]
#[derive(Debug)]
pub struct RawPageTableNode {
    pub raw: Paddr,
    pub level: PagingLevel,
    pub _phantom: PhantomData<(PageTableEntry, PagingConsts)>,
}

impl RawPageTableNode {
    pub open spec fn inv(self) -> bool {
        true
    }

    #[verifier::inline]
    pub open spec fn paddr_spec(&self) -> Paddr {
        self.raw
    }

    #[verifier::when_used_as_spec(paddr_spec)]
    pub fn paddr(&self) -> (res: Paddr)
        ensures
            res == self.paddr_spec(),
    {
        self.raw
    }

    #[verifier::inline]
    pub open spec fn level_spec(&self) -> PagingLevel {
        self.level
    }

    #[verifier::when_used_as_spec(level_spec)]
    pub fn level(&self) -> (res: PagingLevel)
        ensures
            res == self.level_spec(),
    {
        self.level
    }
}

} // verus!
