__author__ = 'Jay Modi'

import logging
from xmodule.modulestore.django import modulestore

# ORA imports
from openassessment.workflow.models import AssessmentWorkflow
from student.models import CourseAccessRole
from django.core.mail import EmailMessage
from openedx.core.djangoapps.content.course_overviews.models import \
    CourseOverview
from openassessment.workflow import api
from edxmako.shortcuts import render_to_string
from xmodule.modulestore.search import path_to_location
from opaque_keys.edx.keys import CourseKey, UsageKey
from django.contrib.sites.shortcuts import get_current_site
from openassessment.assessment.api import staff

from celery import task

TASK_LOG = logging.getLogger('edx.celery.task')

@task()
def staff_notification(request):
    """
    To send ORA statactics to staff users of course
    :param request:
    """
    try:
        course_data = CourseOverview.objects.all()
        for cid in course_data:
            assessment_data = AssessmentWorkflow.objects.filter(
                course_id=cid.id)
            item_data = []
            for sid in assessment_data:
                if not bool(staff.get_latest_staff_assessment(sid.submission_uuid)):
                    if sid.item_id not in item_data:
                        item_data.append(sid.item_id)
            # item_data = AssessmentWorkflow.objects.filter(
            #     course_id=cid.id).values_list('item_id', flat=True)
            # item_data = list(set(item_data))
            for iid in item_data:
                statistics = api.get_status_counts(cid.id, iid,
                                                   ["staff", "peer", "done",
                                                    "waiting"])
                staff_users = CourseAccessRole.objects.filter(course_id=cid.id,
                                                              role='staff')
                try:
                    usage_key = UsageKey.from_string(iid).replace(course_key=cid.id)
                    (course_key, chapter, section, vertical_unused,
                    position, final_target_id
                    ) = path_to_location(modulestore(), usage_key)
                    current_site = get_current_site(request)
                    courseware_url = current_site.domain+"/courses/"+str(cid.id)+"/courseware/"+chapter+"/"+section
                    for u in staff_users:
                        html_message = render_to_string('peer_grading/ora_report.html',
                                                        {'status_counts': statistics,
                                                         'course': cid.display_name,
                                                         'user': u.user,
                                                         'courseware_url':courseware_url
                                                         })
                        email = EmailMessage(
                            "LYNX Online-Training: New Submissions for Staff Review", html_message,
                            to=[u.user.email])
                        email.send()
                        TASK_LOG.info("----------Email message sent to course admins----------")
                except Exception as e:
                    TASK_LOG.info("----------Inner Exception while sending staff notification----------")
                    print e,"Inner Exception<-------"
                    pass
    except Exception as e:
        print e,"<--- Error"