from errbot import BotPlugin, botcmd
from config import JENKINS_URL, JENKINS_USERNAME, JENKINS_PASSWORD

from jenkins import Jenkins, NotFoundException


class JenkinsBot(BotPlugin):
    """JenkinsBot is an Err plugin to manage Jenkins CI jobs from your chat platform like Slack."""

    def __init__(self, bot):
        self.jenkins = Jenkins(JENKINS_URL, JENKINS_USERNAME, JENKINS_PASSWORD)
        super().__init__(bot)


    @botcmd(split_args_with=None)
    def jenkins_build(self, msg, args):
        """Build the job specified by jobName. You can add params!"""

        # Params are passed like "key1=value1 key2=value2"
        params = {}
        try:
            for arg in args[1:]:
                params[arg.split('=', 1)[0]] = arg.split('=', 1)[1]
        except IndexError:
            return "I don't like that params! Try with this format: key1=value1 key2=value2..."

        try:
            self.jenkins.build_job(args[0].strip(), params)
        except NotFoundException:
            return "Sorry, I can't find the job. Typo maybe?"

        return ' '.join(["The job", args[0].strip(), "has been sent to the queue to be built."])


    @botcmd
    def jenkins_cancel(self, msg, args):
        """Cancel a job in the queue by jobId."""

        try:
            self.jenkins.cancel_queue(args.strip())
        except NotFoundException:
            return "Sorry, I can't find the job. Maybe the ID does not exist."

        return "Job canceled from the queue."


    @botcmd
    def jenkins_list(self, msg, args):
        """List Jenkins jobs. You can filter with strings."""

        self.send(msg.frm, "I'm getting the jobs list from Jenkins...")

        search_term = args.strip().lower()
        jobs = [job for job in self.jenkins.get_jobs()
                if search_term.lower() in job['name'].lower()]

        return self.format_jobs(jobs)


    @botcmd
    def jenkins_describe(self, msg, args):
        """Describe the job specified by jobName."""

        try:
            job = self.jenkins.get_job_info(args.strip())
        except NotFoundException:
            return "Sorry, I can't find the job. Typo maybe?"

        return ''.join([
            'Name: ', job['name'], '\n',
            'URL: ', job['url'], '\n',
            'Description: ', 'None' if job['description'] is None else job['description'], '\n',
            'Next Build Number: ',
            str('None' if job['nextBuildNumber'] is None else job['nextBuildNumber']), '\n',
            'Last Successful Build Number: ',
            str('None' if job['lastBuild'] is None else job['lastBuild']['number']), '\n',
            'Last Successful Build URL: ',
            'None' if job['lastBuild'] is None else job['lastBuild']['url'], '\n'
        ])


    @botcmd
    def jenkins_running(self, msg, args):
        """List running jobs."""

        self.send(msg.frm, "I will ask for the current running builds list!")

        jobs = self.jenkins.get_running_builds()

        return self.format_running_jobs(jobs)


    @botcmd(split_args_with=None)
    def jenkins_stop(self, msg, args):
        """Stop the building job specified by jobName and jobNumber."""

        try:
            int(args[1].strip())
        except ValueError:
            return "You have to specify the jobNumber: \"!jenkins stop <jobName> <jobNumber>"

        try:
            self.jenkins.stop_build(args[0].strip(), int(args[1].strip()))
        except NotFoundException:
            return "Sorry, I can't find the job. Typo maybe?"

        return ' '.join(["The job", args[0].strip(), "has been stopped."])


    @botcmd
    def jenkins_queue(self, msg, args):
        """List jobs in queue."""

        self.send(msg.frm, "Getting the job queue...")

        jobs = self.jenkins.get_queue_info()

        return self.format_queue_jobs(jobs)


    def format_jobs(self, jobs):
        """Format jobs list"""

        if len(jobs) == 0:
            return "I haven't found any job."

        max_length = max([len(job['name']) for job in jobs])
        return '\n'.join(['%s (%s)' % (job['name'].ljust(max_length),
                                       job['url']) for job in jobs]).strip()


    def format_queue_jobs(self, jobs):
        """Format queue jobs list"""

        if len(jobs) == 0:
            return "It seems that there is not jobs in queue."

        return '\n'.join(['%s - %s (%s)' % (str(job['id']),
                                            job['task']['name'],
                                            job['task']['url']) for job in jobs]).strip()


    def format_running_jobs(self, jobs):
        """Format running jobs list"""

        if len(jobs) == 0:
            return "There is no running jobs!"

        return '\n'.join(['%s - %s (%s) - %s' % (str(job['number']),
                                                 job['name'],
                                                 job['url'],
                                                 job['executor']) for job in jobs]).strip()

