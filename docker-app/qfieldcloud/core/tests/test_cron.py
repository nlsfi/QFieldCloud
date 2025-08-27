import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone

from qfieldcloud.core.cron import RescheduleFailedApplyJobs
from qfieldcloud.core.models import (
    ApplyJob,
    ApplyJobDelta,
    Delta,
    Organization,
    Person,
    Project,
    ProjectCollaborator,
)

from .utils import set_subscription, setup_subscription_plans


class RescheduleFailedApplyJobsTestCase(TestCase):
    def setUp(self):
        setup_subscription_plans()
        self.user = Person.objects.create_user(username="user", password="abc123")
        set_subscription(self.user, "default_user")
        self.org1 = Organization.objects.create(
            username="org1", organization_owner=self.user
        )

        self.project1 = Project.objects.create(
            name="project1",
            is_public=False,
            owner=self.org1,
        )
        ProjectCollaborator.objects.create(
            project=self.project1,
            collaborator=self.user,
            role=ProjectCollaborator.Roles.ADMIN,
        )

    def _make_delta(self, status: str, created_at_offset: int):
        d = Delta.objects.create(
            project=self.project1,
            created_by=self.user,
            last_status=status,
            content={"op": "test"},
            deltafile_id=uuid.uuid4(),
            client_id=uuid.uuid4(),
        )
        # control ordering by tweaking created_at
        Delta.objects.filter(id=d.id).update(
            created_at=timezone.now() - timedelta(seconds=created_at_offset)
        )
        d.refresh_from_db()
        return d

    def test_no_failed_apply_jobs(self):
        job_count_before = ApplyJob.objects.count()
        RescheduleFailedApplyJobs().do()
        self.assertEqual(ApplyJob.objects.count(), job_count_before)

    def test_reschedule_only_failed_deltas_and_reset_status(self):
        # Prepare one failed apply job with mixed delta outcomes
        aj = ApplyJob.objects.create(
            project=self.project1,
            created_by=self.user,
            overwrite_conflicts=False,
            status=ApplyJob.Status.FAILED,
        )

        d1 = self._make_delta(Delta.Status.APPLIED, created_at_offset=30)
        d2 = self._make_delta(Delta.Status.ERROR, created_at_offset=20)
        d3 = self._make_delta(Delta.Status.ERROR, created_at_offset=10)
        d4 = self._make_delta(Delta.Status.APPLIED, created_at_offset=0)

        # attach deltas to job via through table to mimic an executed job
        ApplyJobDelta.objects.bulk_create(
            [
                ApplyJobDelta(apply_job=aj, delta=d1, status=Delta.Status.APPLIED),
                ApplyJobDelta(apply_job=aj, delta=d2, status=Delta.Status.ERROR),
                ApplyJobDelta(apply_job=aj, delta=d3, status=Delta.Status.ERROR),
                ApplyJobDelta(apply_job=aj, delta=d4, status=Delta.Status.APPLIED),
            ]
        )

        # Run cron
        RescheduleFailedApplyJobs().do()

        # A new apply job should be created
        self.assertEqual(ApplyJob.objects.count(), 2)
        new_job = ApplyJob.objects.exclude(id=aj.id).first()
        self.assertIsNotNone(new_job)

        # Only failed deltas should be scheduled in created_at order (d2 older than d3)
        new_job_deltas = list(
            ApplyJobDelta.objects.filter(apply_job=new_job)
            .select_related("delta")
            .order_by("id")
        )
        self.assertEqual(len(new_job_deltas), 2)
        self.assertEqual(new_job_deltas[0].delta_id, d2.id)
        self.assertEqual(new_job_deltas[1].delta_id, d3.id)

        # The original failed deltas last_status should be reset to PENDING
        d2.refresh_from_db()
        d3.refresh_from_db()
        self.assertEqual(d2.last_status, Delta.Status.PENDING)
        self.assertEqual(d3.last_status, Delta.Status.PENDING)

        # Non-failed deltas should remain APPLIED
        d1.refresh_from_db()
        d4.refresh_from_db()
        self.assertEqual(d1.last_status, Delta.Status.APPLIED)
        self.assertEqual(d4.last_status, Delta.Status.APPLIED)

    def test_multiple_failed_apply_jobs(self):
        # First failed job
        aj1 = ApplyJob.objects.create(
            project=self.project1,
            created_by=self.user,
            overwrite_conflicts=True,
            status=ApplyJob.Status.FAILED,
        )
        e1 = self._make_delta(Delta.Status.ERROR, created_at_offset=5)
        ApplyJobDelta.objects.create(apply_job=aj1, delta=e1, status=Delta.Status.ERROR)

        # Second failed job
        aj2 = ApplyJob.objects.create(
            project=self.project1,
            created_by=self.user,
            overwrite_conflicts=False,
            status=ApplyJob.Status.FAILED,
        )
        e2 = self._make_delta(Delta.Status.ERROR, created_at_offset=3)
        ApplyJobDelta.objects.create(apply_job=aj2, delta=e2, status=Delta.Status.ERROR)

        RescheduleFailedApplyJobs().do()

        # Two new apply jobs should be created
        self.assertEqual(
            ApplyJob.objects.filter(status=ApplyJob.Status.FAILED).count(), 2
        )
        self.assertEqual(
            ApplyJob.objects.exclude(status=ApplyJob.Status.FAILED).count(), 2
        )

        # Ensure each new job has exactly one delta corresponding to its original failed one
        new_jobs = list(
            ApplyJob.objects.exclude(status=ApplyJob.Status.FAILED).order_by(
                "created_at"
            )
        )
        deltas_per_job = [
            list(ApplyJobDelta.objects.filter(apply_job=nj)) for nj in new_jobs
        ]
        self.assertTrue(all(len(lst) == 1 for lst in deltas_per_job))
        self.assertSetEqual(
            {deltas_per_job[0][0].delta_id, deltas_per_job[1][0].delta_id},
            {e1.id, e2.id},
        )
