__author__ = 'Jay Modi'

import logging
import json
from xmodule.modulestore.django import modulestore

# ORA imports
from openassessment.workflow.models import AssessmentWorkflow
from student.models import CourseAccessRole
from django.core.mail import EmailMessage
from openedx.core.djangoapps.content.course_overviews.models import \
    CourseOverview
from openedx.core.djangoapps.content.course_structures.models import \
    CourseStructure
from openassessment.workflow import api
from edxmako.shortcuts import render_to_string
from xmodule.modulestore.search import path_to_location
from opaque_keys.edx.keys import CourseKey, UsageKey
from openassessment.assessment.api import staff
from django.conf import settings

from celery import task

TASK_LOG = logging.getLogger('edx.celery.task')

@task()
def staff_notification():
    """
    To send ORA statactics to staff users of course
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
                modified_statistics = dict()
                for stat in statistics:
                    modified_statistics[stat.get('status')] = stat.get('count')

                statistics = modified_statistics

                if (( statistics['staff'] == 0 ) and ( statistics['peer'] == 0 ) and ( statistics['waiting'] == 0 )):
                    return
                    
                
                course_struct = None
                chapter_name = None
 
                try:
                    course_struct = CourseStructure.objects.get(course_id=cid.id)
                except Exception as e:
                    print "Unexpected error {0}".format(e)

                if course_struct:
                    block = json.loads(course_struct.structure_json)['blocks'][iid]
                    chapter_name = block['display_name']

                staff_users = CourseAccessRole.objects.filter(course_id=cid.id,
                                                              role='staff')
                try:
                    usage_key = UsageKey.from_string(iid).replace(course_key=cid.id)
                    (course_key, chapter, section, vertical_unused,
                    position, final_target_id
                    ) = path_to_location(modulestore(), usage_key)
                    current_site_domain = 'http://{0}'.format(settings.SITE_NAME)
                    courseware_url = current_site_domain+"/courses/"+str(cid.id)+"/courseware/"+chapter+"/"+section
                    for u in staff_users:
                        html_message = render_to_string('peer_grading/ora_report.html',
                                                        {'status_counts': modified_statistics,
                                                         'course': cid.display_name,
                                                         'chapter_name' : chapter_name,
                                                         'user': u.user,
                                                         'courseware_url':courseware_url
                                                         })
                        email = EmailMessage(
                            "LYNX Online-Training: Neue Aufgaben zur Bewertung", html_message,
                            to=[u.user.email])
                        email.send()
                        TASK_LOG.info("----------Email message sent to course admins----------")
                except Exception as e:
                    TASK_LOG.info("----------Inner Exception while sending staff notification----------")
                    import traceback
                    print traceback.format_exc()
                    print e,"Inner Exception<-------"
                    pass
    except Exception as e:
        import traceback
        print traceback.format_exc() 
        print e,"<--- Error"
