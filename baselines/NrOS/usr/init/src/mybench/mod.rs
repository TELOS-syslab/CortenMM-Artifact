// MMAP microbenchmark

use vibrio::rumprt::crt;
use vibrio::syscalls::*;
use alloc::vec;
use core::ptr::null_mut;
use alloc::string::String;
use crate::alloc::string::ToString;
use alloc::sync::Arc;
use spin::Mutex;
use alloc::vec::Vec;
use core::convert::TryInto;
use core::ptr;
use core::sync::atomic::{AtomicUsize, Ordering};
use log::{error, info};
use x86::bits64::paging::{VAddr, BASE_PAGE_SIZE, PML4_SLOT_SIZE};
use lineup::tls2::{Environment, SchedulerControlBlock};

pub const TOT_THREAD_RUNS: usize = 96;


static POOR_MANS_BARRIER: AtomicUsize = AtomicUsize::new(0);
pub const PAGE_SIZE: i32 = 4096;
pub const PROT_READ: i32 = 1;
pub const PROT_WRITE: i32 = 2;
pub const MAP_PRIVATE: i32 = 2;
pub const MAP_ANONYMOUS: i32 = 32;
pub const NUM_MMAPS: i32 = 10;
pub const LARGE_REGION_PAGES: i32 = 16384;

#[derive(Clone)]
#[derive(Debug)]
pub struct ThreadData {
    pub region: *mut u8,    
    pub region_size: i32,   
    pub thread_id: i32,      
    pub lat: i128,           
}
unsafe impl Send for ThreadData {}
unsafe impl Sync for ThreadData {}

pub struct TestResult {
    pub min_lat: i128,
    pub p5_lat: i128,  
    pub avg_lat: i128,       
    pub p95_lat: i128,       
    pub max_lat: i128,       
    pub posvar2_lat: i128,    
    pub negvar2_lat: i128,    
}

fn get_time_in_nanos(start_tsc: u64, end_tsc: u64) -> u64 {
    // Our setup is a 1.9 GHz CPU
    (end_tsc - start_tsc) * 10 / 19
}


pub fn entry_point(
    worker_thread: unsafe extern "C" fn(*mut u8) -> *mut u8,
    num_prealloc_pages: i32,
) {
    let num_threads = TOT_THREAD_RUNS as i32;
    unsafe {
        run_test_specify_threads(num_threads, worker_thread, num_prealloc_pages);
    }
}

pub fn run_test_specify_threads(
    num_threads: i32,
    worker_thread: unsafe extern "C" fn(*mut u8) -> *mut u8,
    num_prealloc_pages: i32,
) {
    // info!("num_threads is {}, num_prealloc_pages is {}", num_threads, num_prealloc_pages);
    info!("Threads, min lat (ns), p5 lat (ns), Avg lat (ns), p95 lat (ns), max lat (ns), Pos err lat (ns2), Neg err lat (ns2)");

    if num_threads == -1 {
        let threads = [1, 16, 32, 48, 64];
        for &num_threads in &threads {
            run_test_specify_rounds(num_threads, worker_thread, num_prealloc_pages);
        }
    } else {
        run_test_specify_rounds(num_threads, worker_thread, num_prealloc_pages);
    }
}

pub fn run_test_specify_rounds(
    num_threads: i32,
    worker_thread: unsafe extern "C" fn(*mut u8) -> *mut u8,
    num_prealloc_pages: i32,
) {
    let mut result = TestResult {
        min_lat: 0,
        p5_lat: 0,
        avg_lat: 0,
        p95_lat: 0,
        max_lat: 0,
        posvar2_lat: 0,
        negvar2_lat: 0,
    };
    run_test(&mut result, num_threads, worker_thread, num_prealloc_pages);

    // info!(
    //     "{}, {}, {}, {}, {}, {}, {}, {}",
    //     num_threads, result.min_lat, result.p5_lat, result.avg_lat, result.p95_lat, result.max_lat, 
    //     result.posvar2_lat, result.negvar2_lat
    // );

    Process::exit(0);
}

pub fn run_test(
    result: &mut TestResult,
    num_threads: i32,
    worker_thread: unsafe extern "C" fn(*mut u8) -> *mut u8,
    num_prealloc_pages: i32,
) {
    info!("Coming into run_test, with num_threads: {}, worker_thread: {:?}, num_prealloc_pages: {}", num_threads, worker_thread, num_prealloc_pages);
    let mut threads = vec![null_mut::<ThreadData>(); TOT_THREAD_RUNS];
    let mut thread_data = Arc::new(Mutex::new(vec![
        ThreadData {
            region: null_mut(),
            region_size: 0,
            thread_id: 0,
            lat: 0,
        };
        TOT_THREAD_RUNS
    ]));
        
    let hwthreads = vibrio::syscalls::System::threads().expect("Can't get system topology");
    // info!("The hwthreads is {:?}", hwthreads);

    let s = &vibrio::upcalls::PROCESS_SCHEDULER;
    let cores = num_threads as usize;
    let current_core = vibrio::syscalls::System::core_id().expect("Can't get core id");
    let mut core_ids = Vec::with_capacity(cores);

    // info!("runs is {}, current_core is {}", runs, current_core);
    for hwthread in hwthreads.iter().take(cores) {
        if hwthread.id != current_core {
            match vibrio::syscalls::Process::request_core(
                hwthread.id,
                VAddr::from(vibrio::upcalls::upcall_while_enabled as *const fn() as u64),
            ) {
                Ok(core_token) => {
                    core_ids.push(core_token.gtid());
                    continue;
                }
                Err(e) => {
                    error!("Can't spawn on {:?}: {:?}", hwthread.id, e);
                    break;
                }
            }
        } else {
            core_ids.push(hwthread.id);
        }
    }
    assert!(core_ids.len() == cores);
    info!("Spawned {} cores", cores);

    let mut region;
    // for run_id in 0..runs {
    unsafe {
        region = crt::mem::mmap(
            null_mut(),
            (LARGE_REGION_PAGES * PAGE_SIZE).try_into().unwrap(),
            PROT_READ | PROT_WRITE,
            MAP_PRIVATE | MAP_ANONYMOUS,
            -1,
            0,
        );
    }
    info!("region is {:?}", region);
    // loop {}
    
    for i in 0..num_threads {
        let thread_id: usize = i.try_into().unwrap();
        // info!("thread_id is {}", thread_id);
        let mut data = thread_data.lock();
        data[thread_id].region = region as *mut u8;
        data[thread_id].region_size = num_prealloc_pages * PAGE_SIZE;
        data[thread_id].thread_id = i;
    }
    let core_ids_clone = core_ids.clone();
    let thread_data_clone = Arc::clone(&thread_data);
    info!("The core_ids is {:?}", core_ids_clone);
    
    let _r = vibrio::syscalls::Process::print("-----------------Before spawn----------------------\r\n");
    s.spawn(
        32 * 4096,
        move |_| {
            // currently we'll run out of 4 KiB frames
            let mut thandles = Vec::with_capacity(cores.try_into().unwrap());
            info!("-------Coming into move. This core is {}------------", vibrio::syscalls::System::core_id().expect("Can't get core id"));
            // Set up barrier
            POOR_MANS_BARRIER.store(cores.try_into().unwrap(), Ordering::SeqCst);
            let mut i = 0;
            for core_id in core_ids_clone {
                let current_thread_id: usize = (i).try_into().unwrap();
                let thread_data_ptr = {
                    let data = thread_data_clone.lock();
                    &data[current_thread_id] as *const ThreadData as *mut u8
                };
                // info!("To spawn, core_id is {}, current_thread_id is {}, i is {}, run_id is {}.",core_id, current_thread_id, i, run_id);
                // info!("Environment::thread(): {:?}", Environment::thread());
                thandles.push(
                    Environment::thread()
                        .spawn_on_core(Some(worker_thread), thread_data_ptr, core_id)
                        .expect("Can't spawn bench thread?"),
                );
                i += 1;
            }
            info!("The thandles is {:?}", thandles);
            crt::ready();
            for thandle in thandles {
                Environment::thread().join(thandle);
            }
            info!("Leaving move");
        },
        ptr::null_mut(),
        current_core,
        None,
    );
    let _r = vibrio::syscalls::Process::print("Finish s.spawn\r\n");
    let scb: SchedulerControlBlock = SchedulerControlBlock::new(current_core);
    while s.has_active_threads() {
        // let _r = vibrio::syscalls::Process::print("This is in has_active_threads\r\n");
        s.run(&scb);
    }
    // }
    // info!("Finish all runs");
    // info!("The thread_data is {:?}", thread_data);
    
    let _r = vibrio::syscalls::Process::print("-----------------Computing result----------------------\r\n");

    // let tot_runs = num_threads;
    // let mut lat_datas = vec![0; tot_runs.try_into().unwrap()];
    // for i in 0..tot_runs {
    //     let iter: usize = i.try_into().unwrap();
    //     let data = thread_data.lock();
    //     lat_datas[iter] = data[iter].lat;
    // }
    // info!("lat_datas is {:?}", lat_datas);
    // let mut max = 0;
    // let mut min = i128::MAX;
    // let mut avg = 0;
    
    // for i in 0..tot_runs {
    //     let iter: usize = i.try_into().unwrap();
    //     let lat = lat_datas[iter];
        
    //     if lat > max {
    //         max = lat;
    //     }
    //     if lat < min {
    //         min = lat;
    //     }
    //     avg += lat;
    // }
    // avg /= tot_runs as i128;

    // let mut posvar2 = 0;
    // let mut numpos = 0;
    // let mut negvar2 = 0;
    // let mut numneg = 0;

    // for i in 0..tot_runs {
    //     let iter: usize = i.try_into().unwrap();
    //     let diff = {
    //         let data = thread_data.lock();
    //         data[iter].lat - avg
    //     };
    //     if diff > 0 {
    //         posvar2 += diff * diff;
    //         numpos += 1;
    //     } else {
    //         negvar2 += diff * diff;
    //         numneg += 1;
    //     }
    // }

    // if numpos > 0 {
    //     posvar2 /= numpos;
    // }
    // if numneg > 0 {
    //     negvar2 /= numneg;
    // }

    // for i in 0..tot_runs {
    //     for j in 0..(tot_runs - i - 1) {
    //         let iter: usize = j.try_into().unwrap();
    //         if lat_datas[iter] > lat_datas[iter + 1] {
    //             let tmp = lat_datas[iter];
    //             lat_datas[iter] = lat_datas[iter + 1];
    //             lat_datas[iter + 1] = tmp;
    //         }
    //     } 
    // }
    // info!("After sort, lat_datas is {:?}", lat_datas);
    

    // let p5 = lat_datas[<i32 as TryInto<usize>>::try_into(tot_runs / 20).unwrap()];
    // let p95 = lat_datas[<i32 as TryInto<usize>>::try_into(tot_runs * 19 / 20).unwrap()];

    // result.min_lat = min;
    // result.avg_lat = avg;
    // result.p5_lat = p5;
    // result.p95_lat = p95;
    // result.max_lat = max;
    // result.posvar2_lat = posvar2;
    // result.negvar2_lat = negvar2;
    // info!("Finish run_test!!!");
}

unsafe extern "C" fn my_worker_thread(arg: *mut u8) -> *mut u8 {
    let current_core = vibrio::syscalls::System::core_id().expect("Can't get core id");
    info!("-------Coming into my_worker_thread. This core is {}------------", current_core);

    let data = unsafe { &mut *(arg as *mut ThreadData) };

    // info!("[core {}]: Trying to allocate a frame", current_core);
    // let (frame_id, _paddr) = PhysicalMemory::allocate_base_page().expect("Can't allocate a memory obj");
    // info!("[core {}]: Got frame_id {:#?}", current_core, frame_id);
    // let vspace_offset = lineup::tls2::Environment::tid().0 + 1;
    // let mut base: u64 = (128 * PML4_SLOT_SIZE + (PML4_SLOT_SIZE * vspace_offset)) as u64;
    // info!("[core {}]: start mapping at {:#x}", current_core, base);
    

    // Synchronize with all cores
    POOR_MANS_BARRIER.fetch_sub(1, Ordering::Relaxed);
    if POOR_MANS_BARRIER.load(Ordering::Relaxed) == 0 {
        info!("[core {}]: I am the last to enter the fence.", current_core);
    }
    while POOR_MANS_BARRIER.load(Ordering::Relaxed) != 0 {
        // info!("----------------------------");
        core::hint::spin_loop();
        // Environment::thread().relinquish();
    }

    let base = data.region;
    unsafe {
        let p = base;
        for i in (0..LARGE_REGION_PAGES).step_by(PAGE_SIZE.try_into().unwrap()) {
            let c = *p.add(i.try_into().unwrap());
        }
    }

    // let start = rawtime::Instant::now();
    // let map_start = x86::time::rdtsc();

    // for i in 0..NUM_MMAPS{
    //     // unsafe {
    //     //     let region = crt::mem::mmap(
    //     //         null_mut(),
    //     //         <i32 as TryInto<usize>>::try_into(PAGE_SIZE).unwrap(),
    //     //         PROT_READ | PROT_WRITE,
    //     //         MAP_PRIVATE | MAP_ANONYMOUS,
    //     //         -1,
    //     //         0,
    //     //     );
    //     //     // info!("region is {:p}", region);
    //     // }
    //     unsafe { VSpace::map_frame(frame_id, base).expect("Map syscall failed") };
    //     info!("--------------------------------------");
    // }
    // let map_end = x86::time::rdtsc();

    // let end = rawtime::Instant::now();
    // info!("[core {}]: The start is {:?}, the end is {:?}", current_core, start, end);

    // let total_time = end - start;
    // let total_time = get_time_in_nanos(map_start, map_end);

    // data.lat = (total_time / NUM_MMAPS.try_into().unwrap()).as_nanos() as i128;
    // data.lat = (total_time / TryInto::<u64>::try_into(NUM_MMAPS).unwrap()) as i128;
    // info!("[core {}]: The data.lat is {}", current_core, data.lat);

    ptr::null_mut()
}

pub fn my_test() {
    let _r = vibrio::syscalls::Process::print("This is my function\r\n");
    entry_point(my_worker_thread, 1);
}
