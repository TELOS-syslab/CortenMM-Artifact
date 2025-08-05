// Eflags register
#define FL_CF           0x00000001      // Carry Flag
#define FL_PF           0x00000004      // Parity Flag
#define FL_AF           0x00000010      // Auxiliary carry Flag
#define FL_ZF           0x00000040      // Zero Flag
#define FL_SF           0x00000080      // Sign Flag
#define FL_TF           0x00000100      // Trap Flag
#define FL_IF           0x00000200      // Interrupt Enable
#define FL_DF           0x00000400      // Direction Flag
#define FL_OF           0x00000800      // Overflow Flag
#define FL_IOPL_MASK    0x00003000      // I/O Privilege Level bitmask
#define FL_IOPL_0       0x00000000      //   IOPL == 0
#define FL_IOPL_1       0x00001000      //   IOPL == 1
#define FL_IOPL_2       0x00002000      //   IOPL == 2
#define FL_IOPL_3       0x00003000      //   IOPL == 3
#define FL_NT           0x00004000      // Nested Task
#define FL_RF           0x00010000      // Resume Flag
#define FL_VM           0x00020000      // Virtual 8086 mode
#define FL_AC           0x00040000      // Alignment Check
#define FL_VIF          0x00080000      // Virtual Interrupt Flag
#define FL_VIP          0x00100000      // Virtual Interrupt Pending
#define FL_ID           0x00200000      // ID flag

// Page fault error codes
#define FEC_PR          0x1     // Page fault caused by protection violation
#define FEC_WR          0x2     // Page fault caused by a write
#define FEC_U           0x4     // Page fault occured while in user mode

// Control Register flags
#define CR0_PE		0x00000001	// Protection Enable
#define CR0_MP		0x00000002	// Monitor coProcessor
#define CR0_EM		0x00000004	// Emulation
#define CR0_TS		0x00000008	// Task Switched
#define CR0_ET		0x00000010	// Extension Type
#define CR0_NE		0x00000020	// Numeric Errror
#define CR0_WP		0x00010000	// Write Protect
#define CR0_AM		0x00040000	// Alignment Mask
#define CR0_NW		0x20000000	// Not Writethrough
#define CR0_CD		0x40000000	// Cache Disable
#define CR0_PG		0x80000000	// Paging

#define CR4_PGE         0x00000080      // Page global enable
#define CR4_PCE         0x100           // RDPMC at CPL > 0

// FS/GS base registers
#define MSR_FS_BASE     0xc0000100
#define MSR_GS_BASE     0xc0000101
#define MSR_GS_KERNBASE 0xc0000102

// SYSCALL and SYSRET registers
#define MSR_STAR        0xc0000081
#define MSR_LSTAR       0xc0000082
#define MSR_CSTAR       0xc0000083
#define MSR_SFMASK      0xc0000084

#define MSR_INTEL_MISC_ENABLE 0x1a0
#define MISC_ENABLE_PEBS_UNAVAILABLE (1<<12) // Read-only

// AMD performance event-select registers
#define MSR_AMD_PERF_SEL0  0xC0010000
#define MSR_AMD_PERF_SEL1  0xC0010001
#define MSR_AMD_PERF_SEL2  0xC0010002
#define MSR_AMD_PERF_SEL3  0xC0010003
// AMD performance event-count registers
#define MSR_AMD_PERF_CNT0  0xC0010004
#define MSR_AMD_PERF_CNT1  0xC0010005
#define MSR_AMD_PERF_CNT2  0xC0010006
#define MSR_AMD_PERF_CNT3  0xC0010007

// Intel performance event-select registers
#define MSR_INTEL_PERF_SEL0 0x00000186
// Intel performance event-count registers
#define MSR_INTEL_PERF_CNT0 0x000000c1
#define MSR_INTEL_PERF_GLOBAL_STATUS   0x38e
#define PERF_GLOBAL_STATUS_PEBS        (1ull << 62)
#define MSR_INTEL_PERF_GLOBAL_CTRL     0x38f
#define MSR_INTEL_PERF_GLOBAL_OVF_CTRL 0x390

#define MSR_INTEL_PERF_CAPABILITIES 0x345 // RO
#define MSR_INTEL_PEBS_ENABLE       0x3f1
#define MSR_INTEL_PEBS_LD_LAT       0x3f6
#define MSR_INTEL_DS_AREA           0x600

// Common event-select bits
#define PERF_SEL_USR        (1ULL << 16)
#define PERF_SEL_OS         (1ULL << 17)
#define PERF_SEL_EDGE       (1ULL << 18)
#define PERF_SEL_INT        (1ULL << 20)
#define PERF_SEL_ENABLE     (1ULL << 22)
#define PERF_SEL_INV        (1ULL << 23)
#define PERF_SEL_CMASK_SHIFT 24

// CPUID function 0x00000001
#define CPUID_FEATURES      0x00000001
#define FEATURE_EAX_FAMILY(x) \
  ((((x) >> 8) & 0xF) + (((x) & 0xf00) == 0xf00 ? (((x) >> 20) & 0xFF) : 0))
#define FEATURE_ECX_MWAIT   (1 << 3)
#define FEATURE_ECX_PDCM    (1 << 15) // Perfmon and debug
#define FEATURE_ECX_X2APIC  (1 << 21)
#define FEATURE_EBX_APIC(x) (((x) >> 24) & 0xff)
#define FEATURE_EDX_APIC    (1 << 9) // "APIC on chip"
#define FEATURE_EDX_DS      (1 << 21) // Debug store

// CPUID function 0x00000005
#define CPUID_MWAIT         0x00000005

#define CPUID_PERFMON       0x0000000a
#define PERFMON_EAX_VERSION(x)      ((x) & 0xFF)
#define PERFMON_EAX_NUM_COUNTERS(x) (((x) >> 8) & 0xFF)

// CPUID function 0x80000001
#define CPUID_EXTENDED_1 0x80000001
#define CPUID_EXTENDED_1_EDX_Page1GB (1 << 26)

// APIC Base Address Register MSR
#define MSR_APIC_BAR        0x0000001b
#define APIC_BAR_XAPIC_EN   (1 << 11)
#define APIC_BAR_X2APIC_EN  (1 << 10)
