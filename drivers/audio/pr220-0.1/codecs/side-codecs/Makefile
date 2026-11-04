# SPDX-License-Identifier: GPL-2.0
subdir-ccflags-y += -I$(src)/../../common

# Only build the component manager needed by cs8409 in kernel 7.0
snd-hda-scodec-component-y :=	hda_component.o

obj-$(CONFIG_SND_HDA_SCODEC_COMPONENT) += snd-hda-scodec-component.o

# Fallback: if CONFIG_SND_HDA_SCODEC_COMPONENT is not set, build it anyway
# as it is required by the Apple cs8409 driver
ifeq ($(CONFIG_SND_HDA_SCODEC_COMPONENT),)
obj-y += snd-hda-scodec-component.o
endif
