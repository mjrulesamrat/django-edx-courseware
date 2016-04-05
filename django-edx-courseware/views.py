__author__ = 'Jay Modi'

import logging
import json

from django.conf import settings
from django.views.decorators.csrf import ensure_csrf_cookie, csrf_exempt
from django.contrib.auth.models import User, AnonymousUser
from django.db import transaction
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_control

from xmodule.modulestore.django import modulestore
from xmodule.x_module import STUDENT_VIEW

from util.views import ensure_valid_course_key
from util.json_request import JsonResponse, JsonResponseBadRequest
from util.date_utils import strftime_localized
from util.db import outer_atomic

from courseware.module_render import get_module
from courseware import grades
from courseware.access_response import StartDateError
from courseware.access import has_access, _adjust_start_date_for_beta_testers
from courseware.courses import (
    get_course_by_id,
    get_course_with_access
)
from courseware.model_data import FieldDataCache, ScoresClient

from opaque_keys.edx.locations import SlashSeparatedCourseKey
from opaque_keys.edx.keys import CourseKey, UsageKey

from openedx.core.lib.courses import course_image_url

@transaction.non_atomic_requests
@login_required
@cache_control(no_cache=True, no_store=True, must_revalidate=True)
@ensure_valid_course_key
def course_data(request, course_id):
    """
    Get course's data(title, short description), Total Points/Earned Points
    or 404 if there is no such course.

    Assumes the course_id is in a valid format.
    """
    course_key = SlashSeparatedCourseKey.from_deprecated_string(course_id)
    with modulestore().bulk_operations(course_key):
        course = get_course_with_access(request.user, 'load', course_key, depth=None, check_if_enrolled=True)
        access_response = has_access(request.user, 'load', course, course_key)

        staff_access = bool(has_access(request.user, 'staff', course))

        student = request.user

        # NOTE: To make sure impersonation by instructor works, use
        # student instead of request.user in the rest of the function.

        # The pre-fetching of groups is done to make auth checks not require an
        # additional DB lookup (this kills the Progress page in particular).
        student = User.objects.prefetch_related("groups").get(id=student.id)

        with outer_atomic():
            field_data_cache = grades.field_data_cache_for_grading(course, student)
            scores_client = ScoresClient.from_field_data_cache(field_data_cache)

        title = course.display_name_with_default
        loc = course.location.replace(category='about', name='short_description')
        about_module = get_module(
                    request.user,
                    request,
                    loc,
                    field_data_cache,
                    log_if_not_found=False,
                    wrap_xmodule_display=False,
                    static_asset_path=course.static_asset_path,
                    course=course
                )
        short_description = about_module.render(STUDENT_VIEW).content

        courseware_summary = grades.progress_summary(
            student, request, course, field_data_cache=field_data_cache, scores_client=scores_client
        )

        grade_summary = grades.grade(
            student, request, course, field_data_cache=field_data_cache, scores_client=scores_client
        )

        total_points = 0
        earned_points = 0
        for chapter in courseware_summary:
            for section in chapter['sections']:
                total_points += section['section_total'].possible
                earned_points += section['section_total'].earned

        percentage_points = float(earned_points)*(100.0/float(total_points))

        context = {
            "course_image": course_image_url(course),
            "total": total_points,
            "earned": earned_points,
            "percentage": percentage_points,
            'title': title,
            'short_description' : short_description,
            'staff_access': staff_access,
            'student': student.id,
            'passed': is_course_passed(course, grade_summary),
        }

        return JsonResponse(context)

def is_course_passed(course, grade_summary=None, student=None, request=None):
    """
    check user's course passing status. return True if passed

    Arguments:
        course : course object
        grade_summary (dict) : contains student grade details.
        student : user object
        request (HttpRequest)

    Returns:
        returns bool value
    """
    nonzero_cutoffs = [cutoff for cutoff in course.grade_cutoffs.values() if cutoff > 0]
    success_cutoff = min(nonzero_cutoffs) if nonzero_cutoffs else None

    if grade_summary is None:
        grade_summary = grades.grade(student, request, course)

    return success_cutoff and grade_summary['percent'] >= success_cutoff
