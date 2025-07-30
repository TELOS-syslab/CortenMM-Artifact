use vstd::prelude::*;
use crate::page_table::PageTable;
use crate::page_table::UserMode;

verus! {

#[derive(Debug)]
#[rustc_has_incoherent_inherent_impls]
pub struct VmSpace {
    pt: PageTable<UserMode>,
}

} // verus!
