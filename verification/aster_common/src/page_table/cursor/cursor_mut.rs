use vstd::prelude::*;

use crate::prelude::*;
use super::cursor::Cursor;

verus! {

#[rustc_has_incoherent_inherent_impls]
pub struct CursorMut<'a, M: PageTableMode>(pub Cursor<'a, M>);

} // verus!
