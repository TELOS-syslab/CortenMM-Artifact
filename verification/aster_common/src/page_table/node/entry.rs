use vstd::prelude::*;
use vstd::simple_pptr;
use vstd::cell;

use crate::prelude::{
    PageTableEntry, PageTableEntryTrait, PageTableNode, MetaSlot, MetaSlotInner,
    PageTablePageMetaInner,
};

verus! {

#[rustc_has_incoherent_inherent_impls]
pub struct Entry<'a> {
    /// The page table entry.
    ///
    /// We store the page table entry here to optimize the number of reads from
    /// the node. We cannot hold a `&mut E` reference to the entry because that
    /// other CPUs may modify the memory location for accessed/dirty bits. Such
    /// accesses will violate the aliasing rules of Rust and cause undefined
    /// behaviors.
    pub pte: PageTableEntry,
    /// The index of the entry in the node.
    pub idx: usize,
    /// The node that contains the entry.
    pub node: &'a PageTableNode,
}

impl<'a> Entry<'a> {
    pub open spec fn new_spec(pte: PageTableEntry, idx: usize, node: &'a PageTableNode) -> Self {
        Self { pte, idx, node }
    }

    #[verifier::when_used_as_spec(new_spec)]
    pub fn new(pte: PageTableEntry, idx: usize, node: &'a PageTableNode) -> Self {
        Self { pte, idx, node }
    }

    pub fn is_node(
        &self,
        Tracked(p_slot): Tracked<&simple_pptr::PointsTo<MetaSlot>>,
        Tracked(p_inner): Tracked<&cell::PointsTo<MetaSlotInner>>,
        Tracked(pt_inner): Tracked<&cell::PointsTo<PageTablePageMetaInner>>,
    ) -> bool
        requires
            self.node.inv(),
            p_slot.pptr() == self.node.page.ptr,
            p_slot.is_init(),
            p_slot.value().wf(),
            p_inner.id() == p_slot.value()._inner.id(),
            p_inner.is_init(),
            is_variant(p_inner.value(), "_pt"),
            pt_inner.id() == p_slot.value().borrow_pt_spec(p_inner).inner.id(),
            pt_inner.is_init(),
    {
        self.pte.is_present() && !self.pte.is_last(
            self.node.level(Tracked(p_slot), Tracked(p_inner), Tracked(pt_inner)),
        )
    }
}

} // verus!
