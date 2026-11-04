#!/usr/bin/env python3
"""Exercise candidate init/resume recovery and failures with mocked HDA only."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
SOURCE=ROOT/'drivers/audio/pr220-0.1/codecs/cirrus/cirrus_apple.h'
text=SOURCE.read_text()
helpers=text[text.index('static bool cs_8409_apple_lost_setup('):text.index('static int cs_8409_apple_init(')]
init=text[text.index('static int cs_8409_apple_init('):text.index('static int cs_8409_apple_resume(')]
resume=text[text.index('static int cs_8409_apple_resume('):text.index('static int cs_8409_apple_suspend(')]
stub=r'''
#include <stdbool.h>
#include <stdint.h>
#include <stdio.h>
#include <assert.h>
#include <errno.h>
#include <string.h>
#define KERNEL_VERSION(a,b,c) (((a)<<16)|((b)<<8)|(c))
#define LINUX_VERSION_CODE KERNEL_VERSION(7,0,14)
#define AC_VERB_GET_GPIO_MASK 0xF15
struct cs8409_apple_spec {
 int block_unsol,jack_present,headset_type,have_mike,have_buttons,playing,capturing;
 int headset_play_format_setup_needed,headset_capture_format_setup_needed;
 int headset_presetup_done,headset_phase,headset_enable;
 int play_init,capture_init,play_init_count,capture_init_count;
 int last_play_time,first_play_time,unsol_list_sentinel;
};
struct hda_codec { struct {int afg;} core; struct cs8409_apple_spec *spec; };
static unsigned int mask;
static int boot_calls,boot_error,sync_calls,error_logs,read_calls;
static bool restore_mask;
#define myprintk(...) do {} while(0)
#define codec_info(...) do {} while(0)
#define codec_err(...) do {error_logs++;} while(0)
static void ktime_get_real_ts64(int *p) { *p=123; }
static unsigned int snd_hda_codec_read(struct hda_codec *c,int node,int direct,int verb,int parm)
{ assert(node==c->core.afg && verb==AC_VERB_GET_GPIO_MASK);read_calls++;return mask; }
static int cs_8409_boot_setup(struct hda_codec *c)
{
 struct cs8409_apple_spec *s=c->spec;
 assert(s->block_unsol==1 && s->jack_present==0 && s->playing==0 && s->capturing==0);
 assert(s->headset_phase==0 && s->headset_enable==0);
 boot_calls++;
 if(boot_error)return boot_error;
 if(restore_mask)mask=0x27;
 return 0;
}
static void snd_hda_regmap_sync(struct hda_codec *c) { (void)c;sync_calls++; }
'''
wrapper='static int snd_hda_codec_init(struct hda_codec *c) { return cs_8409_apple_init(c); }\n'
tests=r'''
static void reset(struct cs8409_apple_spec *s,struct hda_codec *c)
{
 memset(s,0,sizeof(*s));c->spec=s;c->core.afg=1;
 s->jack_present=1;s->playing=1;s->capturing=1;
 s->headset_phase=2;s->headset_enable=1;
 s->play_init=1;s->capture_init=1;s->play_init_count=9;s->capture_init_count=9;
 s->unsol_list_sentinel=77;
 boot_calls=boot_error=sync_calls=error_logs=read_calls=0;
 mask=0x27;restore_mask=true;
}
int main(void)
{
 struct cs8409_apple_spec s;struct hda_codec c;
 /* Healthy boot/idle resume must not rerun initialization or reset state. */
 reset(&s,&c);assert(cs_8409_apple_init(&c)==0);
 assert(boot_calls==0 && s.play_init==1 && s.headset_enable==1);
 assert(cs_8409_apple_resume(&c)==0 && sync_calls==1 && boot_calls==0);
 /* An unreadable all-ones response is not a blank codec. */
 reset(&s,&c);mask=UINT32_MAX;assert(cs_8409_apple_resume(&c)==0 && boot_calls==0);
 /* Lost mask restores once; next runtime resume must not replay. */
 reset(&s,&c);mask=0;assert(cs_8409_apple_resume(&c)==0);
 assert(boot_calls==1 && mask==0x27 && s.block_unsol==0 && s.headset_phase==2);
 assert(s.play_init==0 && s.capture_init==0 && s.play_init_count==0 && s.capture_init_count==0);
 assert(s.last_play_time==123 && s.first_play_time==123 && s.unsol_list_sentinel==77);
 assert(cs_8409_apple_resume(&c)==0 && boot_calls==1);
 /* A failed setup must propagate through init and resume, unblock events,
  * and skip regmap sync; do not claim the flags/phase are fully restored. */
 reset(&s,&c);mask=0;boot_error=-ETIMEDOUT;
 assert(cs_8409_apple_resume(&c)==-ETIMEDOUT);
 assert(boot_calls==1 && sync_calls==0 && s.block_unsol==0 && error_logs==1);
 assert(s.headset_phase==0 && s.unsol_list_sentinel==77);
 /* A setup that returns success but leaves GPIO blank must fail EIO. */
 reset(&s,&c);mask=0;restore_mask=false;
 assert(cs_8409_apple_resume(&c)==-EIO);
 assert(boot_calls==1 && sync_calls==0 && s.block_unsol==0 && error_logs==1);
 puts("5 offline HDA scenario groups passed; no codec, module or PM access");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='cs8409-pr220-offline-') as tmp:
    source=Path(tmp)/'test.c';binary=Path(tmp)/'test'
    source.write_text(stub+helpers+init+wrapper+resume+tests)
    subprocess.run(['cc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-variable',
                    '-Wno-unused-parameter',str(source),'-o',str(binary)],check=True,timeout=20)
    subprocess.run([str(binary)],check=True,timeout=10)
