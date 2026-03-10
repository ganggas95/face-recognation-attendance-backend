from app.api.v1.routes import (academic_years, attendance, auth,
                               class_instances, class_subject_assignments,
                               class_subject_schedules, classes, dashboard,
                               enrollments, gate_attendance, health,
                               school_settings, student_attendance, students,
                               subjects, teachers, users)
from app.core.deps import get_current_user
from fastapi import APIRouter, Depends

api_router = APIRouter()

api_router.include_router(health.router, tags=["health"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
protected = [Depends(get_current_user)]
api_router.include_router(
    dashboard.router,
    prefix="/dashboard",
    tags=["dashboard"],
    dependencies=protected,
)
api_router.include_router(
    academic_years.router,
    prefix="/academic-years",
    tags=["academic-years"],
    dependencies=protected,
)
api_router.include_router(
    classes.router,
    prefix="/classes",
    tags=["classes"],
    dependencies=protected,
)
api_router.include_router(
    class_instances.router,
    prefix="/class-instances",
    tags=["class-instances"],
    dependencies=protected,
)
api_router.include_router(
    attendance.router,
    prefix="/attendance",
    tags=["attendance"],
    dependencies=protected,
)
api_router.include_router(
    gate_attendance.router,
    prefix="/gate-attendance",
    tags=["gate-attendance"],
    dependencies=protected,
)
api_router.include_router(
    students.router,
    prefix="/students",
    tags=["students"],
    dependencies=protected,
)
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["users"],
    dependencies=protected,
)
api_router.include_router(
    teachers.router,
    prefix="/teachers",
    tags=["teachers"],
    dependencies=protected,
)
api_router.include_router(
    subjects.router,
    prefix="/subjects",
    tags=["subjects"],
    dependencies=protected,
)
api_router.include_router(
    class_subject_assignments.router,
    prefix="/class-subject-assignments",
    tags=["class-subject-assignments"],
    dependencies=protected,
)
api_router.include_router(
    class_subject_schedules.router,
    prefix="/class-subject-schedules",
    tags=["class-subject-schedules"],
    dependencies=protected,
)
api_router.include_router(
    enrollments.router,
    prefix="/enrollments",
    tags=["enrollments"],
    dependencies=protected,
)
api_router.include_router(
    school_settings.router,
    prefix="/school-settings",
    tags=["school-settings"],
    dependencies=protected,
)
api_router.include_router(
    student_attendance.router,
    prefix="/student-attendance",
    tags=["student-attendance"],
    dependencies=protected,
)
