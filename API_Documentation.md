# Dokumentasi API — Face Attendance Backend

Dokumen ini merangkum endpoint yang tersedia pada service backend.

## Base URL

- Default prefix API: `/api/v1` (dapat diubah via env `API_V1_PREFIX`)

## Format Response Umum

Semua endpoint (yang sudah diimplementasikan) membungkus payload dalam format:

```json
{
  "status": 200,
  "data": {},
  "message": "ok",
  "meta": {}
}
```

Keterangan:

- `status`: HTTP status code (angka)
- `data`: payload utama (object)
- `message`: pesan singkat (string)
- `meta`: metadata (object), biasanya untuk pagination

## Pagination

Endpoint list menggunakan query:

- `page` (default `1`, minimal `1`)
- `page_size` (default `20`, minimal `1`, maksimal `100`)

Dan mengembalikan `meta`:

```json
{
  "count": 20,
  "page": 1,
  "page_size": 20,
  "total": 123
}
```

## Authentication

Saat ini tersedia endpoint untuk login dan menghasilkan JWT. Namun, endpoint lain belum menerapkan proteksi `Authorization: Bearer <token>` pada level route.

---

# Endpoints

## Root

### GET `/`

Deskripsi: cek service root.

Response `data`:

```json
{ "service": "face-attendance-backend" }
```

## Health

### GET `/api/v1/health`

Deskripsi: health check.

Response `data`:

```json
{ "status": "ok" }
```

## Auth

### POST `/api/v1/auth/login`

Deskripsi: login user dan dapatkan access token.

Request body (JSON):

- `email` (string)
- `password` (string)

Response `data`:

```json
{
  "token": {
    "access_token": "jwt-string",
    "token_type": "bearer"
  }
}
```

Error:

- `401` jika kredensial tidak valid
- `403` jika user non-aktif

## Users

### POST `/api/v1/users`

Deskripsi: buat user baru.

Request body (JSON):

- `email` (string)
- `password` (string)
- `role` (string) — nilai yang dipakai saat ini: `ADMIN` atau `TEACHER`
- `is_active` (boolean, default `true`)

Response `data`:

```json
{
  "item": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "ADMIN",
    "is_active": true,
    "created_at": "timestamp",
    "updated_at": "timestamp"
  }
}
```

Error:

- `409` jika email sudah terpakai

### GET `/api/v1/users`

Deskripsi: list user (paginated).

Query:

- `page`
- `page_size`

Response `data`:

```json
{
  "items": [
    /* UserRead[] */
  ]
}
```

## Teachers

### POST `/api/v1/teachers`

Deskripsi: buat data guru (Teacher) dan mengaitkan ke `users`.

Catatan: user yang direferensikan harus ada dan `role`-nya harus `TEACHER`.

Request body (JSON):

- `user_id` (uuid)
- `name` (string)
- `nip` (string | null, optional)
- `phone` (string | null, optional)

Response `data`:

```json
{
  "item": {
    "id": "uuid",
    "user_id": "uuid",
    "name": "Nama Guru",
    "nip": null,
    "phone": null,
    "created_at": "timestamp"
  }
}
```

Error:

- `404` jika user tidak ditemukan
- `409` jika user role bukan `TEACHER`
- `409` jika teacher untuk user tersebut sudah ada

### GET `/api/v1/teachers`

Deskripsi: list teacher (paginated).

Query:

- `page`
- `page_size`

Response `data`:

```json
{
  "items": [
    /* TeacherRead[] */
  ]
}
```

## Subjects (Mata Pelajaran)

### POST `/api/v1/subjects`

Deskripsi: buat mata pelajaran dan mengaitkan ke guru pengampu.

Request body (JSON):

- `code` (string | null, optional)
- `name` (string)
- `teacher_id` (uuid)

Response `data`:

```json
{
  "item": {
    "id": "uuid",
    "code": "MAT",
    "name": "Matematika",
    "teacher_id": "uuid",
    "created_at": "timestamp"
  }
}
```

Error:

- `404` jika teacher tidak ditemukan

### GET `/api/v1/subjects`

Deskripsi: list mata pelajaran (paginated).

Query:

- `page`
- `page_size`
- `teacher_id` (uuid, optional) — filter berdasarkan guru pengampu

Response `data`:

```json
{
  "items": [
    /* SubjectRead[] */
  ]
}
```

## Academic Years (Tahun Ajaran)

### POST `/api/v1/academic-years`

Deskripsi: buat tahun ajaran.

Request body (JSON):

- `name` (string)
- `start_date` (date, format `YYYY-MM-DD`)
- `end_date` (date, format `YYYY-MM-DD`)
- `is_active` (boolean, default `false`)

Response `data`:

```json
{
  "item": {
    /* AcademicYearRead */
  }
}
```

### GET `/api/v1/academic-years`

Deskripsi: list tahun ajaran (paginated).

Query:

- `page`
- `page_size`

Response `data`:

```json
{
  "items": [
    /* AcademicYearRead[] */
  ]
}
```

### POST `/api/v1/academic-years/{academic_year_id}/activate`

Deskripsi: set satu tahun ajaran sebagai aktif.

Path param:

- `academic_year_id` (uuid)

Response `data`:

```json
{
  "item": {
    /* AcademicYearRead */
  }
}
```

Error:

- `404` jika academic year tidak ditemukan

## Classes (Master Kelas)

### POST `/api/v1/classes`

Deskripsi: buat master kelas (template kelas).

Request body (JSON):

- `name` (string)
- `grade` (int)
- `homeroom_teacher_id` (uuid | null, optional) — wali kelas

Response `data`:

```json
{
  "item": {
    "id": "uuid",
    "name": "A",
    "grade": 1,
    "homeroom_teacher_id": "uuid-or-null"
  }
}
```

### GET `/api/v1/classes`

Deskripsi: list master kelas (paginated).

Query:

- `page`
- `page_size`

Response `data`:

```json
{
  "items": [
    /* ClassRead[] */
  ]
}
```

## Students

### POST `/api/v1/students`

Deskripsi: buat student.

Request body (JSON):

- `nis` (string)
- `name` (string)

Response `data`:

```json
{
  "item": {
    "id": "uuid",
    "nis": "S001",
    "name": "Nama Siswa",
    "created_at": "timestamp"
  }
}
```

### GET `/api/v1/students`

Deskripsi: list student (paginated).

Query:

- `page`
- `page_size`

Response `data`:

```json
{
  "items": [
    /* StudentRead[] */
  ]
}
```

## Enrollments (Assign Siswa ke Kelas)

### POST `/api/v1/enrollments`

Deskripsi: assign/enroll siswa ke `class_instance` (kelas untuk tahun ajaran tertentu).

Request body (JSON):

- `student_id` (uuid)
- `class_instance_id` (uuid)

Response `data`:

```json
{
  "item": {
    "id": "uuid",
    "student_id": "uuid",
    "class_instance_id": "uuid",
    "created_at": "timestamp"
  }
}
```

Error:

- `404` jika student tidak ditemukan
- `404` jika class instance tidak ditemukan
- `409` jika student sudah ter-enroll di class instance tersebut

### POST `/api/v1/students/{student_id}/faces/enroll`

Deskripsi: pendaftaran wajah siswa (face enrollment) dengan menyimpan embedding ke `student_faces`.

Request:

- Content-Type: `multipart/form-data`
- Path param:
  - `student_id` (uuid)
- Form field:
  - `images` (file, multiple) — disarankan 3–5 foto

Response `data`:

```json
{
  "item": {
    "student_id": "uuid",
    "stored_count": 3,
    "results": [
      {
        "filename": "a.jpg",
        "stored": true,
        "face_id": "uuid",
        "error": null
      }
    ]
  }
}
```

Error:

- `404` jika student tidak ditemukan
- `422` jika semua gambar tidak valid (contoh: tidak ada wajah / >1 wajah / wajah terlalu kecil)

### GET `/api/v1/students/{student_id}/faces`

Deskripsi: list embedding wajah milik siswa.

Path param:

- `student_id` (uuid)

Response `data`:

```json
{
  "items": [
    {
      "id": "uuid",
      "student_id": "uuid",
      "created_at": "timestamp"
    }
  ]
}
```

Error:

- `404` jika student tidak ditemukan

### DELETE `/api/v1/students/{student_id}/faces/{face_id}`

Deskripsi: hapus embedding wajah tertentu milik siswa.

Path param:

- `student_id` (uuid)
- `face_id` (uuid)

Response:

- `200` (message: `deleted`)

Error:

- `404` jika student tidak ditemukan
- `404` jika student face tidak ditemukan (atau bukan milik student tersebut)

## Jadwal Mata Pelajaran (Class Subject Schedules)

### POST `/api/v1/class-subject-schedules`

Deskripsi: buat jadwal mata pelajaran per `class_instance` (tahun ajaran tertentu).

Aturan penting (business rules):

- `day_of_week` harus `0..6`
- `teacher_id` harus sama dengan `subject.teacher_id`
- Slot jadwal unik per `(class_instance_id, day_of_week, start_time)`

Request body (JSON):

- `class_instance_id` (uuid)
- `subject_id` (uuid)
- `teacher_id` (uuid)
- `day_of_week` (int, 0..6)
- `start_time` (time, format `HH:MM[:SS]`)
- `end_time` (time, format `HH:MM[:SS]`)
- `room` (string | null, optional)

Response `data`:

```json
{
  "item": {
    /* ClassSubjectScheduleRead */
  }
}
```

Error:

- `404` jika teacher tidak ditemukan
- `404` jika subject tidak ditemukan
- `409` jika teacher tidak match dengan subject
- `409` jika slot jadwal bentrok

### GET `/api/v1/class-subject-schedules`

Deskripsi: list jadwal (paginated).

Query:

- `page`
- `page_size`
- `class_instance_id` (uuid, optional)
- `teacher_id` (uuid, optional)
- `day_of_week` (int 0..6, optional)

Response `data`:

```json
{
  "items": [
    /* ClassSubjectScheduleRead[] */
  ]
}
```

## Attendance

### POST `/api/v1/attendance/verify`

Deskripsi: verifikasi absensi berbasis face recognition.

Request:

- Content-Type: `multipart/form-data`
- Form field:
  - `schedule_id` (uuid)
  - `image` (file)

Response `data`:

```json
{
  "item": {
    "matched": true,
    "reason": "recorded",
    "confidence": 0.9,
    "student_id": "uuid-or-null",
    "attendance_id": "uuid-or-null",
    "already_recorded": false
  }
}
```

Keterangan field:

- `matched`: `true` jika verifikasi match dan dianggap valid
- `reason`: salah satu nilai umum: `recorded`, `already recorded`, `below threshold`, `ambiguous match`, `no enrolled students`, `no enrolled faces`
- `confidence`: nilai similarity (perkiraan), bisa `null` jika tidak ada kandidat
- `student_id`: terisi hanya jika match
- `attendance_id`: terisi jika attendance tercatat atau sudah ada sebelumnya
- `already_recorded`: `true` jika attendance untuk hari ini sudah ada (idempotent)

Error:

- `404` jika schedule tidak ditemukan
- `422` jika gambar tidak valid / tidak tepat 1 wajah terdeteksi
