#!/usr/bin/env python3
"""Exercise actual candidate state machine and cache-committing worker in C."""
from pathlib import Path
import subprocess
import tempfile

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'drivers/t1/automatic-0.6'
bridge=(BASE/'apple-ibridge.c').read_text()
assert 's3_notify_once' not in bridge and 's3_notify_repeat' not in bridge
enabled=bridge[bridge.index('static bool appleib_has_s3_quirk'):bridge.index('/* One physical T1')]
gate=bridge[bridge.index('static DEFINE_MUTEX(appleib_tb_io_lock)'):bridge.index('struct appleib_device {')]
functions=bridge[bridge.index('static int appleib_trace_pm_event('):bridge.index('\nstruct appleib_hid_dev_info')]
tb=(BASE/'apple-touchbar.c').read_text()
direct=tb[tb.index('static int appletb_set_tb_mode(struct'):tb.index('static bool appletb_any_tb_key_pressed')]
workers=tb[tb.index('static void appletb_set_tb_worker_ungated'):tb.index('static u16 appletb_fn_to_special')]
refresh=tb[tb.index('static int appletb_s3_wake('):tb.index('static void appletb_update_touchbar(struct')]
stub=r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdio.h>
#include <errno.h>
#include <string.h>
#include <pthread.h>
#include <stdatomic.h>
typedef unsigned int acpi_status;
typedef long long s64;
typedef unsigned long long u64;
struct notifier_block { int (*notifier_call)(struct notifier_block *, unsigned long, void *); };
struct mutex { pthread_mutex_t native; };
#define DEFINE_MUTEX(n) struct mutex n = { PTHREAD_MUTEX_INITIALIZER }
#define BLOCKING_NOTIFIER_HEAD(n) struct notifier_block *n
#define EXPORT_SYMBOL_GPL(n)
#define READ_ONCE(n) (n)
#define WRITE_ONCE(n,v) ((n)=(v))
#define lockdep_assert_held(m) assert(pthread_mutex_trylock(&(m)->native)==EBUSY)
#define container_of(p,t,m) ((t *)((char *)(p)-offsetof(t,m)))
#define PM_SUSPEND_MEM 3
#define ACPI_STATE_S3 3
#define PM_SUSPEND_PREPARE 1
#define PM_POST_SUSPEND 4
#define NOTIFY_DONE 0
#define NOTIFY_OK 1
#define NOTIFY_BAD 2
#define ACPI_SUCCESS(x) ((x)==0)
#define ACPI_FAILURE(x) ((x)!=0)
#define APPLETB_CMD_MODE_UPD 254
#define APPLETB_CMD_DISP_UPD 254
#define APPLETB_CMD_MODE_NONE 255
#define APPLETB_CMD_DISP_NONE 255
#define APPLETB_CMD_DISP_OFF 0
#define APPLETB_CMD_DISP_DIM 2
#define pr_info(...) do {if(0)printf(__VA_ARGS__);} while (0)
#define pr_err(...) do {if(0)printf(__VA_ARGS__);} while (0)
#define dev_dbg(dev,...) do {(void)(dev);if(0)printf(__VA_ARGS__);} while (0)
#define min(a,b) ((a)<(b)?(a):(b))
#define max(a,b) ((a)>(b)?(a):(b))
#define spin_lock_irqsave(lock,flags) do {(void)(lock);(flags)=0;} while(0)
#define spin_unlock_irqrestore(lock,flags) do {(void)(lock);(void)(flags);} while(0)
static bool pm_trace, model_supported, firmware_return;
#define DMI_PRODUCT_NAME 1
static bool dmi_match(int slot,const char *name) {(void)slot;(void)name;return model_supported;}
static int appleib_s3_status;
static unsigned int appleib_s3_completed;
static int pm_suspend_target_state=3, acpi_target=3;
static unsigned int fail_command=99, sequence[2048], seq_count, queued, scheduled;
static int mode_rc, display_rc, mode_calls, display_calls;
static atomic_int reached_gate;
static struct mutex *observed_gate;
static void mutex_lock(struct mutex *m) {
 if(m==observed_gate) atomic_store(&reached_gate,1);
 assert(pthread_mutex_lock(&m->native)==0);
}
static void mutex_unlock(struct mutex *m) {assert(pthread_mutex_unlock(&m->native)==0);}
static int blocking_notifier_chain_register(struct notifier_block **h,struct notifier_block *n)
{assert(!*h);*h=n;return 0;}
static int blocking_notifier_chain_unregister(struct notifier_block **h,struct notifier_block *n)
{assert(*h==n);*h=NULL;return 0;}
static int blocking_notifier_call_chain(struct notifier_block **h,unsigned long ev,void *data)
{return *h?(*h)->notifier_call(*h,ev,data):0;}
struct appleib_device {
 void *asoc_socw;
 struct notifier_block trace_notifier;
 bool trace_prepared,trace_s3_seen;
 unsigned int original_pm_flags;
 struct mutex s3_lock;
 bool s3_used,s3_wake_pending,s3_wake_attempted,s3_sleep_failed,s3_cycle_ok;
};
static bool pm_resume_via_firmware(void) {return firmware_return;}
static int acpi_target_system_state(void) {return acpi_target;}
static acpi_status acpi_execute_simple_method(void *h,void *p,unsigned int cmd)
{(void)h;(void)p;sequence[seq_count++]=cmd;return cmd==fail_command?5:0;}
struct work_struct {int unused;};
struct appletb_device {
 struct notifier_block s3_wake_notifier;
 bool is_t1,active,restore_autopm,tb_autopm_off;
 int tb_lock,last_event_time,idle_timeout,dim_timeout;
 void *log_dev;
 unsigned char cur_tb_mode,cur_tb_disp,pnd_tb_mode,pnd_tb_disp;
 struct {void *hdev;bool suspended;} mode_iface;
 struct {struct {void *device;} *report;} *disp_field;
 struct {struct work_struct work;} tb_work;
};
static int ktime_get(void) {return 123;}
static u64 ktime_get_ns(void) {return 123;}
static s64 ktime_ms_delta(int a,int b) {(void)a;(void)b;return 2000;}
static void msleep(int ms) {(void)ms;}
static void appletb_disable_autopm(void *p) {(void)p;}
static bool appletb_any_tb_key_pressed(struct appletb_device *d) {(void)d;return false;}
static void appletb_schedule_tb_update(struct appletb_device *d,s64 delay)
{(void)d;(void)delay;scheduled++;}
static int appletb_set_tb_mode_ungated(struct appletb_device *d,unsigned char mode)
{(void)d;(void)mode;sequence[seq_count++]=3;mode_calls++;return mode_rc;}
static int appletb_set_tb_disp_ungated(struct appletb_device *d,unsigned char disp)
{(void)d;(void)disp;sequence[seq_count++]=4;display_calls++;return display_rc;}
static void appletb_update_touchbar_no_lock(struct appletb_device *d,bool force)
{
 assert(force && d->cur_tb_mode==254 && d->pnd_tb_mode==255);
 d->pnd_tb_mode=2;d->pnd_tb_disp=1;sequence[seq_count++]=2;queued++;
}
'''
tests=r'''
static void init(struct appleib_device *d,struct appletb_device *tb)
{
 memset(d,0,sizeof(*d));assert(pthread_mutex_init(&d->s3_lock.native,NULL)==0);
 memset(tb,0,sizeof(*tb));tb->is_t1=true;tb->active=true;tb->mode_iface.hdev=tb;
 tb->pnd_tb_mode=tb->pnd_tb_disp=255;
 tb->s3_wake_notifier.notifier_call=appletb_s3_wake;
 assert(appleib_tb_register_wake(&tb->s3_wake_notifier)==0);
 pm_trace=false;model_supported=true;firmware_return=false;
 fail_command=99;mode_rc=display_rc=0;mode_calls=display_calls=0;
 seq_count=queued=scheduled=0;pm_suspend_target_state=acpi_target=3;
 appleib_tb_blocked=appleib_tb_refresh_pending=false;
 appleib_s3_status=0;appleib_s3_completed=0;
}
static void finish(struct appleib_device *d,struct appletb_device *tb)
{appleib_tb_unregister_wake(&tb->s3_wake_notifier);assert(pthread_mutex_destroy(&d->s3_lock.native)==0);}
static int event(struct appleib_device *d,unsigned long ev)
{return appleib_trace_pm_event(&d->trace_notifier,ev,NULL);}
static void begin(struct appleib_device *d)
{firmware_return=false;assert(event(d,1)==NOTIFY_OK);assert(appleib_s3_prepare(d)==0);}
static void wake(struct appleib_device *d,bool actual_firmware_return)
{firmware_return=actual_firmware_return;event(d,4);}
static void *prepare_thread(void *arg)
{assert(event(arg,1)==NOTIFY_OK);return NULL;}
int main(void)
{
 struct appleib_device d;struct appletb_device tb;pthread_t thread;
 /* Automatic S3 success runs actual cache-committing workers, five cycles. */
 init(&d,&tb);
 for(unsigned int cycle=1;cycle<=5;cycle++) {
  begin(&d);assert(appleib_s3_status==1);
  unsigned int count=seq_count;appletb_set_tb_worker(&tb.tb_work.work);assert(seq_count==count);
  wake(&d,true);assert(appleib_s3_status==2 && appleib_tb_refresh_pending);
  assert(event(&d,1)==NOTIFY_BAD); /* cannot race ahead of the refresh */
  appletb_set_tb_worker(&tb.tb_work.work);
  assert(appleib_s3_status==4 && appleib_s3_completed==cycle);
  assert(tb.cur_tb_mode==2 && tb.cur_tb_disp==1);
  assert(!appleib_tb_refresh_pending && !appleib_tb_blocked);
  count=seq_count;event(&d,4);assert(seq_count==count); /* no duplicate wake */
 }
 assert(queued==5 && mode_calls==5 && display_calls==5);finish(&d,&tb);
 /* Unsupported models neither issue SOCW nor acquire the S3 I/O gate. */
 init(&d,&tb);model_supported=false;
 assert(appleib_tb_io_begin()==0);appleib_tb_io_end();
 event(&d,1);assert(appleib_s3_prepare(&d)==0);event(&d,4);
 assert(seq_count==0 && appleib_s3_completed==0);finish(&d,&tb);
 /* Failed sleep is paired once for recovery, never rearmed even if wake works. */
 init(&d,&tb);fail_command=0;event(&d,1);assert(appleib_s3_prepare(&d)==-EIO);
 wake(&d,true);appletb_set_tb_worker(&tb.tb_work.work);
 assert(appleib_s3_status==3 && appleib_s3_completed==0 && event(&d,1)==NOTIFY_BAD);finish(&d,&tb);
 /* Failed wake stays closed with no callback/USB retries. */
 init(&d,&tb);begin(&d);fail_command=1;wake(&d,true);
 assert(appleib_s3_status==3 && appleib_tb_blocked && d.s3_wake_pending);
 unsigned int count=seq_count;event(&d,4);appletb_set_tb_worker(&tb.tb_work.work);
 assert(seq_count==count && event(&d,1)==NOTIFY_BAD);finish(&d,&tb);
 /* PM unwind without firmware return cannot qualify a repeat cycle. */
 init(&d,&tb);begin(&d);wake(&d,false);appletb_set_tb_worker(&tb.tb_work.work);
 assert(appleib_s3_status==3 && appleib_s3_completed==0 && event(&d,1)==NOTIFY_BAD);finish(&d,&tb);
 /* Mode/display errors after wake stop the worker and all later USB writes. */
 for(int which=0;which<2;which++) {
  init(&d,&tb);begin(&d);wake(&d,true);
  if(which) display_rc=-EIO;else mode_rc=-EIO;
  appletb_set_tb_worker(&tb.tb_work.work);
  assert(appleib_s3_status==3 && appleib_tb_blocked && appleib_s3_completed==0);
  count=seq_count;appletb_set_tb_worker(&tb.tb_work.work);
  assert(seq_count==count && event(&d,1)==NOTIFY_BAD);finish(&d,&tb);
 }
 /* Missing or still-suspended Touch Bar never fabricates refresh completion. */
 for(int which=0;which<2;which++) {
  init(&d,&tb);if(which)tb.mode_iface.suspended=true;else tb.active=false;
  begin(&d);wake(&d,true);
  assert(!queued && appleib_s3_status==2 && event(&d,1)==NOTIFY_BAD);finish(&d,&tb);
 }
 /* Late direct/idle write failures are sticky even after a completed cycle. */
 init(&d,&tb);begin(&d);wake(&d,true);appletb_set_tb_worker(&tb.tb_work.work);
 mode_rc=-EIO;assert(appletb_set_tb_mode(&tb,2)==-EIO);
 assert(appleib_s3_status==3 && event(&d,1)==NOTIFY_BAD);
 count=seq_count;assert(appletb_set_tb_disp(&tb,1)==-EAGAIN && seq_count==count);finish(&d,&tb);
 init(&d,&tb);begin(&d);wake(&d,true);appletb_set_tb_worker(&tb.tb_work.work);
 tb.idle_timeout=1;display_rc=-EIO;appletb_set_tb_worker(&tb.tb_work.work);
 assert(appleib_s3_status==3 && appleib_tb_blocked && event(&d,1)==NOTIFY_BAD);finish(&d,&tb);
 /* Actual mutex handshake: new PRE waits for prior worker/cache commit. */
 init(&d,&tb);begin(&d);wake(&d,true);assert(appleib_tb_io_begin()==0);
 observed_gate=&appleib_tb_io_lock;atomic_store(&reached_gate,0);
 assert(pthread_create(&thread,NULL,prepare_thread,&d)==0);
 while(!atomic_load(&reached_gate)) {}
 appletb_set_tb_worker_ungated(&tb.tb_work.work);assert(appleib_s3_status==4);
 appleib_tb_io_end();assert(pthread_join(thread,NULL)==0);observed_gate=NULL;
 assert(!d.s3_used && appleib_s3_status==0);
 assert(appleib_s3_prepare(&d)==0);wake(&d,true);appletb_set_tb_worker(&tb.tb_work.work);
 assert(appleib_s3_completed==2);finish(&d,&tb);
 /* No PRE or non-S3 target cannot request firmware. */
 init(&d,&tb);assert(appleib_s3_prepare(&d)==-EPERM);event(&d,1);acpi_target=4;
 assert(appleib_s3_prepare(&d)==0 && seq_count==0);finish(&d,&tb);
 puts("Automatic S3 C tests passed: five cycles, gated cache commit, automatic/model-scoped, failures, abort, missing interfaces, late errors and threaded drain.");
 return 0;
}
'''
with tempfile.TemporaryDirectory(prefix='T1-repeat-offline-',dir='/tmp') as tmp:
    src=Path(tmp)/'test.c';binary=Path(tmp)/'test'
    src.write_text(stub+enabled+gate+functions+direct+workers+refresh+tests)
    subprocess.run(['cc','-std=gnu11','-Wall','-Wextra','-Werror','-Wno-unused-parameter',
                    '-pthread',str(src),'-o',str(binary)],check=True,timeout=30)
    subprocess.run([str(binary)],check=True,timeout=15)
print('Actual candidate functions ran with mocked AML/USB and local pthreads only; no host PM operation.')
