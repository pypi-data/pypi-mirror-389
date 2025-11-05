from datetime import datetime

from apscheduler.executors.pool import ThreadPoolExecutor
from apscheduler.schedulers.blocking import BlockingScheduler


class NDS_Job:

    BS = BlockingScheduler(timezone='Asia/Shanghai',
                           executors={'default': ThreadPoolExecutor()})

    @staticmethod
    def add(job, now=True, **a):
        if now:
            __class__.BS.add_job(
                job, 'cron', **a, max_instances=1, next_run_time=datetime.now())
        else:
            __class__.BS.add_job(job, 'cron', **a, max_instances=1)

    @staticmethod
    def start():
        __class__.BS.start()

    @staticmethod
    def list():
        jobs = __class__.BS.get_jobs()
        return [{"ID": job.id, "Next": job.next_run_time, "Trigger": job.trigger} for job in jobs]
