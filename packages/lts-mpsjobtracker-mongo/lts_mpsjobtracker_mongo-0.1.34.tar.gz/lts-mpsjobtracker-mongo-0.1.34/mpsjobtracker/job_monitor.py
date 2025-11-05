import json, time, traceback
import datetime
from datetime import timedelta
# MQ utilities package
from mpsmqutils import mqutils
# Job tracker module
from mpsjobtracker.trackers.jobtracker import JobTracker, log_error_and_reraise
from mpsjobtracker.log_wrapper import LogWrapper
import celery as celeryapp
import os

from urllib.parse import urlparse

job_tracker = JobTracker()
log = LogWrapper()
_success_queue = os.getenv("SUCCESS_QUEUE")
_failure_queue = os.getenv("FAILURE_QUEUE")
_max_child_errors = int(os.getenv("CHILD_ERROR_LIMIT", 10))
_max_retries_override = int(os.getenv("MAX_RETRIES_OVERRIDE", None))
_child_job_timeout = int(os.getenv("CHILD_JOB_TIMEOUT", 21600))

class JobMonitor():
    def __init__(self, progress_check_duration):
        self.progress_check_duration = timedelta(seconds=progress_check_duration)
        self.child_job_timeout = timedelta(seconds=_child_job_timeout)

    def run(self):
        while True:
            self.check_inprocess_jobs()
            time.sleep(self.progress_check_duration.seconds)


    def check_inprocess_jobs(self):
        current_time = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc, microsecond=0)
        log.info('Checking running jobs ' + str(current_time))
        running_jobs = job_tracker.get_jobs('running')
        self.attempt_to_resolve_jobs(running_jobs, current_time)

        log.info("Checking for stalled queued parent jobs...")
        queued_jobs = job_tracker.get_jobs('queued', {
            'parent_job_ref': {"$exists": False},
            'context.child_job_spawning_status': 'failure'
        })
        self.attempt_to_resolve_jobs(queued_jobs, current_time)

        # We need to check child jobs that are stuck as queued....
        log.info("Checking for stalled queued child jobs...")
        queued_child_jobs = job_tracker.get_jobs('queued', {
            'parent_job_ref': {"$exists": True}
        })
        self.attempt_to_resolve_jobs(queued_child_jobs, current_time)


    def attempt_to_resolve_jobs(self, inprocess_jobs, current_time):
        for job_doc in inprocess_jobs:
            job_id = job_doc["_id"]
            log.info(f"inprocess job {str(job_id)}")
            parent_ref = job_doc.get('parent_job_ref')
            child_job_spawning_status = 'unfinished'

            drsObjectId = None
            if 'context' in job_doc:
                child_job_spawning_status = job_doc['context'].get('child_job_spawning_status', 'unfinished')
                drsObjectId = job_doc['context'].get('drsObjectId')

            # Check for tracker_doc child_job_spawning_status success, failure, unfinished
            if (parent_ref is None and child_job_spawning_status and child_job_spawning_status != 'unfinished'):
                # Check if this job is complete by seeing if all child jobs are failed or successful
                log.info("Attempting to resolve parent job " + str(job_id))
                child_jobs = job_tracker.get_child_jobs(job_id)
                job_finished = True
                total_child_job_count = 0
                failed_job_count = 0

                for child_job in child_jobs:
                    jm = child_job['job_management']
                    child_job_status = jm['job_status']
                    tries_left = self.get_tries_left(jm['numberOfTries'], jm['maxNumberOfTries'])
                    total_child_job_count += 1
                    if child_job_status not in ('success', 'failed'):
                        job_finished = False
                    elif child_job_status == 'failed' and tries_left <= 0:
                        failed_job_count += 1

                # If all child jobs have failed, or failures are greater than a configurable threshold, do fail the parent job
                if child_job_spawning_status == 'failure' or failed_job_count >= _max_child_errors or failed_job_count >= total_child_job_count:
                    log.info("Found a failed parent job..." + str(job_id))
                    job_tracker.set_job_status('failed', job_id)
                    space = job_doc.get('context', {}).get('globalSettings', {}).get('spaceDefault', None)
                    manifest_id = job_doc.get('context', {}).get('manifest', {}).get('@id', None)
                    urn = parse_urn(manifest_id) if manifest_id else None
                    log.info("Set the parent job's status to failed..." + str(job_id))
                    celeryapp.execute.send_task("tasks.tasks.failed_job", args=[{'job_id': str(job_id), 'status': 'failed', 'space': space, 'manifest_urn': urn, 'drsObjectId': drsObjectId}], kwargs={}, queue=_failure_queue)
                # if job is finished (and not failed) we mark it as successful
                elif job_finished and total_child_job_count > 0:
                    log.info("Found a complete parent job..." + str(job_id))
                    job_tracker.set_job_status('success', job_id)
                    log.info("Resolved the completed job..." + str(job_id))
                    # We skip the time comparison if we resolve a job
                    space = job_doc.get('context', {}).get('globalSettings', {}).get('spaceDefault', None)
                    manifest_id = job_doc.get('context', {}).get('manifest', {}).get('@id', None)
                    urn = parse_urn(manifest_id) if manifest_id else None
                    celeryapp.execute.send_task("tasks.tasks.successful_job", args=[{'job_id': str(job_id), 'status': 'success', 'space': space, 'manifest_urn': urn, 'drsObjectId': drsObjectId}], kwargs={}, queue=_success_queue)
                else:
                    log.info("Job is not finished...")
            elif (parent_ref is None and child_job_spawning_status == 'unfinished'):
                log.info("Parent job has not finished spawning children " + str(job_id))
            else:
                # Check for stalled child jobs
                log.info("Checking status of child job " + str(job_id))
                try:
                    job_doc_time = job_doc['last_modified_date'].replace(tzinfo=datetime.timezone.utc)
                    diff = current_time - job_doc_time
                    #If it has been more than the expected duration, we assume
                    #that the process has stalled.
                    if diff >= self.child_job_timeout:
                        self.handle_stalled_job(job_doc)
                except Exception as e:
                    # TODO: This doesn't actually print the error, we get "exception: 'event'" in all cases
                    log.error('exception: {}'.format(e))


    def handle_stalled_job(self, job_doc):
        job_management = job_doc.get("job_management")
        if (job_management is None):
            #TODO what to do here - what does this mean?
            return False
        number_of_tries = job_management["numberOfTries"]
        max_number_of_tries = job_management["maxNumberOfTries"]
        if self.get_tries_left(number_of_tries, max_number_of_tries) > 0:
            #Requeue
            log.info("Requeued child job id" + str(job_doc["_id"]))
            return self.requeue(job_doc, number_of_tries+1)
        else:
            log.error("Failed stalled child job id" + str(job_doc["_id"]))
            return job_tracker.set_job_status('failed', job_doc["_id"])
            # TODO: Revert will happen here once it's been developed

    def requeue(self, job_doc, trial_number):
        #Update the number of tries in the tracker file
        job_doc["job_management"]["numberOfTries"] = trial_number
        try:
            updated_job_doc = job_tracker.replace_tracker_doc(job_doc)
        except Exception as e:
            #TODO what to do here - what does this mean if the tracker retrieval fails?
            return False
        #Log message
        #Queue the step again
        ticket_id = str(job_doc['_id'])
        parent_ticket_id = str(job_doc.get('parent_job_ref', ''))

        message = mqutils.create_requeue_message(ticket_id, parent_ticket_id)
        try:
            json_message = json.loads(message)
        except ValueError as e:
            log_error_and_reraise("JSON loading failed in requeue")
        job_name = json_message["event"]

        celeryapp.execute.send_task("tasks.tasks.do_task", args=[message], kwargs={}, queue=job_name)
        job_tracker.set_job_status('queued', ticket_id, job_doc['job_management']['job_status'])

        return True

    def revert(self, job_doc):
        # TODO in future: currently no-op
        pass

    def get_tries_left(self, current_tries, max_tries):
        if _max_retries_override or _max_retries_override == 0:
            return _max_retries_override - current_tries
        else:
            return max_tries - current_tries

# From iiif-services urn-name module
def parse_urn(manifest_id):
    try:
        if "://" in manifest_id:
            parsed_url = urlparse(manifest_id)
            value = parsed_url.path.split("/")[-1].upper()

            manifest_tags = [":MANIFEST:2", ":MANIFEST:3"]
            for manifest_tag in manifest_tags:
                if manifest_tag in value:
                    value = value.split(manifest_tag)[0]
        return value.upper()
    except:
        return "Unable to parse urn"
