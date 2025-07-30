pub mod dyn_page;
pub mod meta;
pub mod model;

pub use meta::*;
pub use dyn_page::*;
pub use model::*;

use vstd::prelude::*;
use vstd::simple_pptr;
use vstd::cell;
use core::marker::PhantomData;
use crate::mm::Paddr;
use crate::x86_64::mm::{MAX_NR_PAGES, MAX_PADDR, PAGE_SIZE};

verus! {

#[rustc_has_incoherent_inherent_impls]
pub struct Page<M: PageMeta> {
    pub ptr: simple_pptr::PPtr<MetaSlot>,
    pub _marker: PhantomData<M>,
}

impl<M: PageMeta> Page<M> {
    pub open spec fn inv_ptr(self) -> bool {
        let addr = self.ptr.addr();
        FRAME_METADATA_RANGE().start <= addr && addr < FRAME_METADATA_RANGE().start + MAX_NR_PAGES()
            * META_SLOT_SIZE() && addr % META_SLOT_SIZE() == 0
    }

    #[verifier::inline]
    pub open spec fn paddr_spec(&self) -> Paddr
        recommends
            self.inv_ptr(),
    {
        meta_to_page(self.ptr.addr())
    }

    #[verifier::when_used_as_spec(paddr_spec)]
    pub fn paddr(&self) -> (res: Paddr)
        requires
            self.inv_ptr(),
        ensures
            res == self.paddr_spec(),
            res % PAGE_SIZE() == 0,
            res < MAX_PADDR(),
    {
        meta_to_page(self.ptr.addr())
    }

    pub fn meta_pt<'a>(
        &'a self,
        Tracked(p_slot): Tracked<&'a simple_pptr::PointsTo<MetaSlot>>,
        Tracked(p_inner): Tracked<&'a cell::PointsTo<MetaSlotInner>>,
    ) -> (res: &'a PageTablePageMeta)
        requires
            self.inv_ptr(),
            p_slot.pptr() == self.ptr,
            p_slot.is_init(),
            p_slot.value().wf(),
            p_inner.id() == p_slot.value()._inner.id(),
            p_inner.is_init(),
            is_variant(p_inner.value(), "_pt"),
        ensures
            *res == p_slot.value().borrow_pt_spec(p_inner),
    {
        let slot = self.ptr.borrow(Tracked(p_slot));
        slot.borrow_pt(Tracked(p_inner))
    }

    pub fn meta_frame<'a>(
        &'a self,
        Tracked(p_slot): Tracked<&'a simple_pptr::PointsTo<MetaSlot>>,
        Tracked(p_inner): Tracked<&'a cell::PointsTo<MetaSlotInner>>,
    ) -> (res: &'a FrameMeta)
        requires
            self.inv_ptr(),
            p_slot.pptr() == self.ptr,
            p_slot.is_init(),
            p_slot.value().wf(),
            p_inner.id() == p_slot.value()._inner.id(),
            p_inner.is_init(),
            is_variant(p_inner.value(), "_frame"),
        ensures
            *res == p_slot.value().borrow_frame_spec(p_inner),
    {
        let slot = self.ptr.borrow(Tracked(p_slot));
        slot.borrow_frame(Tracked(p_inner))
    }
}

} // verus!
