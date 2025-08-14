.DEFAULT_GOAL := all
.PHONY: lock-protocol all compile verify verify-parallel clean fmt

VERIFICATION_TARGETS := \
	lock-protocol

COMPILE_TARGETS := vstd_extra

# Pattern rule for individual FVT targets
fvt%:
	cargo xtask verify --targets $(filter fvt$*-%, $(VERIFICATION_TARGETS))

lock-protocol:
	cargo xtask verify --targets lock-protocol

fmt:
	cargo xtask fmt

all: compile verify

compile:
	cargo xtask compile --targets $(COMPILE_TARGETS)

verify:
	cargo xtask verify --targets $(VERIFICATION_TARGETS) $(if $(VOSTD_VERIFY_PARALLEL),--parallel)

verify-parallel:
	VOSTD_VERIFY_PARALLEL=1 $(MAKE) verify

clean:
	cargo clean