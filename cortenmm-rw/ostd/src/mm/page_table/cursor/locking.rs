// SPDX-License-Identifier: MPL-2.0

//! Implementation of the locking protocol.

use core::{marker::PhantomData, mem::ManuallyDrop, ops::Range};

use super::Cursor;
use crate::{
    mm::{
        page_table::{
            cursor::{GuardInPath, MAX_NR_LEVELS},
            pte_index, ChildRef, PageTable, PageTableConfig, PagingConstsTrait,
        },
        Vaddr,
    },
    task::atomic_mode::InAtomicMode,
};

pub(super) fn lock_range<'a, C: PageTableConfig>(
    pt: &'a PageTable<C>,
    guard: &'a dyn InAtomicMode,
    va: &Range<Vaddr>,
) -> Cursor<'a, C> {
    let mut path: [GuardInPath<'a, C>; MAX_NR_LEVELS] =
        core::array::from_fn(|_| GuardInPath::Unlocked);

    let mut cur_pt = pt.root.borrow();

    // Go down and get proper locks. The cursor should hold a write lock of a
    // page table node containing the virtual address range.
    //
    // While going down, we will hold read locks of previous path of too-high levels.
    loop {
        let cur_level = cur_pt.level();

        let start_idx = pte_index::<C>(va.start, cur_level);
        let level_too_high = {
            let end_idx = pte_index::<C>(va.end - 1, cur_level);
            cur_level > 1 && start_idx == end_idx
        };
        if !level_too_high {
            break;
        }

        let mut cur_pt_rlockguard = cur_pt.clone_ref().lock_read(guard);

        let entry = cur_pt_rlockguard.entry(start_idx);
        let child_ref = entry.to_ref();
        match child_ref {
            ChildRef::PageTable(pt) => {
                path[cur_level as usize - 1] = GuardInPath::Read(cur_pt_rlockguard);
                cur_pt = pt;
                continue;
            }
            _ => {
                break;
            }
        }
    }

    // Get write lock of the current page table node.
    let cur_level = cur_pt.level();
    let cur_wlock = cur_pt.lock_write(guard);
    path[cur_level as usize - 1] = GuardInPath::Write(cur_wlock);

    #[cfg(debug_assertions)]
    {
        for i in (C::NR_LEVELS..cur_level).rev() {
            assert!(matches!(&path[i as usize - 1], GuardInPath::Read(_)));
        }
    }

    Cursor::<'a, C> {
        path,
        rcu_guard: guard,
        level: cur_level,
        guard_level: cur_level,
        va: va.start,
        barrier_va: va.clone(),
        _phantom: PhantomData,
    }
}

pub(super) fn unlock_range<C: PageTableConfig>(cursor: &mut Cursor<'_, C>) {
    #[cfg(debug_assertions)]
    {
        for i in 1..cursor.level {
            debug_assert!(matches!(
                cursor.path[i as usize - 1].take(),
                GuardInPath::Unlocked
            ))
        }
    }

    for i in cursor.level..cursor.guard_level {
        let GuardInPath::ImplicitWrite(guard) = cursor.path[i as usize - 1].take() else {
            panic!(
                "Expected implicitly locked guard at level {}, found {:?}",
                i,
                cursor.path[i as usize - 1]
            );
        };
        // This is implicitly write locked. Don't drop (unlock) it.
        let _ = ManuallyDrop::new(guard);
    }

    let GuardInPath::Write(guard_node) = cursor.path[cursor.guard_level as usize - 1].take() else {
        panic!("Expected write lock");
    };

    drop(guard_node);

    for i in (cursor.guard_level + 1)..=C::NR_LEVELS {
        let GuardInPath::Read(rguard) = cursor.path[i as usize - 1].take() else {
            panic!(
                "Expected read lock at level {}, found {:?}",
                i,
                cursor.path[i as usize - 1]
            );
        };
        drop(rguard);
    }
}
