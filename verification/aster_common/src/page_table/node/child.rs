use vstd::prelude::*;

use crate::prelude::{RawPageTableNode, PageProperty, Paddr, PagingLevel, DynPage};

verus! {

/// A child of a page table node.
///
/// This is a owning handle to a child of a page table node. If the child is
/// either a page table node or a page, it holds a reference count to the
/// corresponding page.
#[rustc_has_incoherent_inherent_impls]
pub enum Child {
    PageTable(RawPageTableNode),
    Page(DynPage, PageProperty),
    /// Pages not tracked by handles.
    Untracked(Paddr, PagingLevel, PageProperty),
    None,
}

impl Child {
    #[verifier::inline]
    pub open spec fn is_none_spec(&self) -> bool {
        match self {
            Child::None => true,
            _ => false,
        }
    }

    #[verifier::when_used_as_spec(is_none_spec)]
    pub fn is_none(&self) -> bool {
        match self {
            Child::None => true,
            _ => false,
        }
    }
}

} // verus!
