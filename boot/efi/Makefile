# SPDX-License-Identifier: MIT
# Build EFI applications only. No installation, firmware write or reboot target.
SOURCE_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
OUTPUT ?= $(CURDIR)/build/efi
CC := gcc
LD := x86_64-w64-mingw32-ld
EFI_INCLUDE ?= /usr/include/efi
CFLAGS := -I$(EFI_INCLUDE) -I$(EFI_INCLUDE)/x86_64 \
	-ffreestanding -fshort-wchar -mno-red-zone -fno-stack-protector \
	-fno-asynchronous-unwind-tables -fno-ident -DHAVE_USE_MS_ABI \
	-Wall -Wextra -Werror
LDFLAGS := -mi386pep --subsystem 10 --entry efi_main \
	--image-base 0 --file-alignment 512 --section-alignment 4096 \
	--enable-reloc-section --strip-all

.PHONY: all
all: $(OUTPUT)/mbp143-set-igd.efi $(OUTPUT)/mbp143-set-dis.efi $(OUTPUT)/mbp143-windows-radeon.efi

$(OUTPUT):
	mkdir -p "$@"

$(OUTPUT)/igd.o: $(SOURCE_DIR)/mbp143-gpu-switch.c | $(OUTPUT)
	$(CC) $(CFLAGS) -DGPU_INTEGRATED=1 -c "$<" -o "$@"

$(OUTPUT)/dis.o: $(SOURCE_DIR)/mbp143-gpu-switch.c | $(OUTPUT)
	$(CC) $(CFLAGS) -DGPU_INTEGRATED=0 -c "$<" -o "$@"

$(OUTPUT)/windows-radeon.o: $(SOURCE_DIR)/mbp143-gpu-switch.c | $(OUTPUT)
	$(CC) $(CFLAGS) -DGPU_INTEGRATED=0 -DBOOT_WINDOWS=1 -c "$<" -o "$@"

$(OUTPUT)/mbp143-set-igd.efi: $(OUTPUT)/igd.o
	$(LD) $(LDFLAGS) "$<" -o "$@"

$(OUTPUT)/mbp143-set-dis.efi: $(OUTPUT)/dis.o
	$(LD) $(LDFLAGS) "$<" -o "$@"

$(OUTPUT)/mbp143-windows-radeon.efi: $(OUTPUT)/windows-radeon.o
	$(LD) $(LDFLAGS) "$<" -o "$@"
