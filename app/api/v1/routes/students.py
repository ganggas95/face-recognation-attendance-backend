import uuid

from app.core.deps import get_student_face_repository, get_student_repository
from app.repositories.student_faces import StudentFaceRepository
from app.repositories.students import StudentRepository
from app.schemas.api_response import ApiResponse, build_response
from app.schemas.pagination import PaginationParams
from app.schemas.student_faces import StudentFaceEnrollSummary, StudentFaceRead
from app.schemas.students import StudentCreate, StudentRead, StudentUpdate
from app.services.student_faces import (delete_student_face,
                                        enroll_student_faces,
                                        list_student_faces)
from app.services.students import (create_student, get_student, list_students,
                                   update_student)
from fastapi import APIRouter, Depends, File, Query, UploadFile, status

router = APIRouter()


@router.post(
    "",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: StudentCreate,
    repo: StudentRepository = Depends(get_student_repository),
) -> ApiResponse:
    student = create_student(repo, payload)
    item = StudentRead.model_validate(student).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": item},
        message="created",
        meta={},
    )


@router.get("", response_model=ApiResponse)
def list_all(
    repo: StudentRepository = Depends(get_student_repository),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
) -> ApiResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    students, total = list_students(
        repo,
        offset=pagination.offset,
        limit=pagination.page_size,
    )
    items = [
        StudentRead.model_validate(student).model_dump()
        for student in students
    ]
    return build_response(
        status=status.HTTP_200_OK,
        data={"items": items},
        message="ok",
        meta={
            "count": len(items),
            "page": pagination.page,
            "page_size": pagination.page_size,
            "total": total,
        },
    )


@router.get("/{student_id}", response_model=ApiResponse)
def get_one(
    student_id: uuid.UUID,
    repo: StudentRepository = Depends(get_student_repository),
) -> ApiResponse:
    student = get_student(repo, student_id)
    item = StudentRead.model_validate(student).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="ok",
        meta={},
    )


@router.patch("/{student_id}", response_model=ApiResponse)
def update(
    student_id: uuid.UUID,
    payload: StudentUpdate,
    repo: StudentRepository = Depends(get_student_repository),
) -> ApiResponse:
    student = update_student(repo, student_id=student_id, payload=payload)
    item = StudentRead.model_validate(student).model_dump()
    return build_response(
        status=status.HTTP_200_OK,
        data={"item": item},
        message="updated",
        meta={},
    )


@router.post(
    "/{student_id}/faces/enroll",
    response_model=ApiResponse,
    status_code=status.HTTP_201_CREATED,
)
async def enroll_faces(
    student_id: uuid.UUID,
    images: list[UploadFile] = File(...),
    student_repo: StudentRepository = Depends(get_student_repository),
    face_repo: StudentFaceRepository = Depends(get_student_face_repository),
) -> ApiResponse:
    payload_images: list[tuple[str, bytes]] = []
    print(images)
    for image in images:
        payload_images.append((image.filename or "image", await image.read()))
    summary = enroll_student_faces(
        student_repo=student_repo,
        face_repo=face_repo,
        student_id=student_id,
        images=payload_images,
    )
    data = StudentFaceEnrollSummary.model_validate(summary).model_dump()
    return build_response(
        status=status.HTTP_201_CREATED,
        data={"item": data},
        message="created",
        meta={},
    )


@router.get("/{student_id}/faces", response_model=ApiResponse)
def list_faces(
    student_id: uuid.UUID,
    student_repo: StudentRepository = Depends(get_student_repository),
    face_repo: StudentFaceRepository = Depends(get_student_face_repository),
) -> ApiResponse:
    faces = list_student_faces(
        student_repo=student_repo,
        face_repo=face_repo,
        student_id=student_id,
    )
    items = [
        StudentFaceRead.model_validate(face).model_dump() for face in faces
    ]
    return build_response(
        status=status.HTTP_200_OK,
        data={"items": items},
        message="ok",
        meta={"count": len(items)},
    )


@router.delete("/{student_id}/faces/{face_id}", response_model=ApiResponse)
def delete_face(
    student_id: uuid.UUID,
    face_id: uuid.UUID,
    student_repo: StudentRepository = Depends(get_student_repository),
    face_repo: StudentFaceRepository = Depends(get_student_face_repository),
) -> ApiResponse:
    delete_student_face(
        student_repo=student_repo,
        face_repo=face_repo,
        student_id=student_id,
        face_id=face_id,
    )
    return build_response(
        status=status.HTTP_200_OK,
        data={},
        message="deleted",
        meta={},
    )
