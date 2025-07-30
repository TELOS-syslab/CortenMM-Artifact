use vstd::prelude::*;

use crate::prelude::*;

verus! {

#[rustc_has_incoherent_inherent_impls]
pub tracked struct AbstractState {
    //pub ghost meta_slots: Map<int, MetaSlotModel>,
    pub ghost pages: Map<int, PageModel>,
    pub page_table: PageTableModel,
    pub tracked perms: Map<int, PagePerm>,
    pub ghost max_pages: int,
    pub ghost errors: Seq<&'static str>,
    pub ghost context_id: int,
    pub ghost thread_id: int,
}

} // verus!
verus! {

impl AbstractState {
    pub open spec fn ghost_eq(self, other: AbstractState) -> bool {
        &&& self.pages == other.pages
        &&& self.max_pages == other.max_pages
        &&& self.page_table == other.page_table
        &&& self.errors == other.errors
        &&& self.context_id == other.context_id
        &&& self.thread_id == other.thread_id
    }

    pub open spec fn max_page_invariants(self) -> bool {
        0 < self.max_pages && self.max_pages <= MAX_NR_PAGES()
    }

    pub open spec fn pages_invariants(self) -> bool {
        &&& forall|i: int|
            {
                0 <= i && i < MAX_NR_PAGES() ==> {
                    #[trigger] self.pages.dom().contains(i) && self.pages[i].index == i
                        && self.pages[i].invariants()
                }
            }
    }

    pub open spec fn page_table_invariants(self) -> bool {
        self.page_table.inv()
    }

    /* pub open spec fn meta_slots_invariants(&self) -> bool {
    &&& forall|i: int| {
        0 <= i && i < MAX_NR_PAGES() ==> {
                #[trigger] self.meta_slots.dom().contains(i) &&
                self.meta_slots[i].address@ == i * PAGE_SIZE() &&
                self.meta_slots[i].invariants()
            }
        }
    }*/
    pub open spec fn perms_invariants(self) -> bool {
        &&& forall|i: int|
            {
                0 <= i < MAX_NR_PAGES() ==> {
                    &&& #[trigger] self.perms.dom().contains(i)
                    &&& self.perms[i].invariants()
                    &&& self.pages[i].relate_perm(self.perms[i])
                }
            }
    }

    pub open spec fn invariants(self) -> bool {
        &&& self.max_page_invariants()
        &&& self.pages_invariants()
        &&& self.page_table_invariants()
        //&&& self.meta_slots_invariants()
        &&& self.perms_invariants()
        &&& self.pt_nodes_usage_invariant()
    }

    pub open spec fn get_page(&self, paddr: Paddr) -> (res: PageModel) {
        self.pages[paddr as int / PAGE_SIZE() as int]
    }

    pub open spec fn get_perm(self, paddr: Paddr) -> (res: PagePerm) {
        self.perms[paddr as int / PAGE_SIZE_SPEC() as int]
    }

    pub open spec fn is_node(self, paddr: Paddr) -> bool {
        exists|node: PageTableNodeModel| #[trigger] self.page_table.tree@.on_tree(node@)
    }

    pub open spec fn pt_nodes_usage_invariant(self) -> bool {
        forall|paddr: Paddr| #[trigger]
            self.is_node(paddr) ==> self.get_page(paddr).usage == PageUsage::PageTable
    }

    #[verifier::returns(proof)]
    pub proof fn borrow_pt_model(
        #[verifier::proof]
        &self,
    ) -> (res: Tracked<&PageTableModel>) {
        Tracked(&self.page_table)
    }

    /* pub open spec fn get_meta_slot(&self, paddr: Paddr) -> (res: MetaSlotModel)
    {
        self.meta_slots[paddr as int / PAGE_SIZE() as int]
    } */
    pub proof fn get_page_relate_to_paddr(&self, paddr: Paddr)
        requires
            self.invariants(),
            paddr < MAX_PADDR(),
            paddr % PAGE_SIZE() == 0,
        ensures
            self.get_page(paddr).relate_paddr(paddr),
    {
        let page = self.get_page(paddr);
        let idx = paddr as int / PAGE_SIZE() as int;
        assert(page == &self.pages[idx]);
        assert(self.pages.dom().contains(idx));
        assert(self.pages[idx].index == idx);
        assert(page.index == idx);
        assert(page.index == paddr as int / PAGE_SIZE() as int);
        assert(page.index * PAGE_SIZE() as int == paddr as int);
        assert(page.relate_paddr(paddr));
    }

    /*
    pub proof fn get_meta_slot_relate_to_paddr(&self, paddr: Paddr)
        requires
            self.invariants(),
            paddr < MAX_PADDR(),
            paddr % PAGE_SIZE() == 0,
        ensures
            self.get_meta_slot(paddr).address@ == paddr,
    {
        let slot = self.get_meta_slot(paddr);
        let idx = paddr as int / PAGE_SIZE() as int;
        assert(slot == &self.meta_slots[idx]);
        assert(self.meta_slots.dom().contains(idx));
        assert(self.meta_slots[idx].address@ == idx * PAGE_SIZE());
        assert(slot.address@ == idx * PAGE_SIZE());
        assert(slot.address@ == paddr);
    }*/
    pub open spec fn panic_spec(&self, msg: &str) -> AbstractState {
        AbstractState { errors: self.errors.push(msg), ..*self }
    }

    pub open spec fn failed(&self, initial: AbstractState) -> bool {
        self.errors.len() > initial.errors.len()
    }

    /*    pub open spec fn update_page_table_idx(&self, idx: int, pte:PageTableEntry) -> Self
    {
        Self {
            meta_slots: self.meta_slots,
            pages: self.pages,
            page_table: self.page_table.update_idx(idx, pte),
            max_pages: self.max_pages,
            errors: self.errors,
            context_id: self.context_id,
            thread_id: self.thread_id,
        }
    } */
    pub open spec fn update_page_model_spec(self, paddr: Paddr, model: PageModel) -> AbstractState {
        let index = page_to_index_spec(paddr as int);
        AbstractState { pages: self.pages.insert(index, model), ..self }
    }

    pub proof fn lemma_get_page_satisfies_invariants(&self, paddr: Paddr)
        requires
            self.invariants(),
            paddr < MAX_PADDR_SPEC(),
            paddr % PAGE_SIZE_SPEC() == 0,
        ensures
            self.get_page(paddr).invariants(),
    {
        let idx = page_to_index(paddr);
        assert(self.pages.dom().contains(idx));
    }

    pub proof fn lemma_get_page_has_valid_index(&self, paddr: Paddr)
        requires
            self.invariants(),
            paddr < MAX_PADDR_SPEC(),
            paddr % PAGE_SIZE_SPEC() == 0,
        ensures
            self.get_page(paddr).has_valid_index(),
    {
        let idx = page_to_index(paddr);
        assert(self.pages.dom().contains(idx));
    }
}

pub fn panic(Tracked(s): Tracked<AbstractState>, msg: &str) -> (res: Tracked<AbstractState>)
    ensures
        res@ == s.panic_spec(msg),
{
    Tracked(AbstractState { errors: s.errors.push(msg), ..s })
}

} // verus!
