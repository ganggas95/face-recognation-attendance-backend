# PRD - Face Recognition Attendance System (Backend)

Academic Year Based Architecture

Updated on: 2026-03-04

---

# 1. Overview

Backend system for school face-recognition attendance using:

- FastAPI
- PostgreSQL
- pgvector
- InsightFace (ArcFace)
- Academic Year Based Structure
- Role-based access (Admin, Teacher)
- Schedule-based attendance (per subject session)

System designed for 300 students, 6 classes, scalable for multi-year
usage.

---

# 2. Core Architecture Concept

Entities:

- User (Auth + Role)
- Teacher (Profile data, linked to User)
- Student (Permanent)
- Academic Year (Period-based)
- Class (Template)
- Class Instance (Per Academic Year)
- Homeroom Teacher (Teacher assigned to Class)
- Enrollment (Student membership per class instance)
- Subject (Mata pelajaran, assigned to a Teacher)
- Class Subject Schedule (Subject sessions scheduled per class instance)
- Face Embedding (Permanent)
- Attendance (Per schedule session per date)

---

# 3. ERD (Entity Relationship Diagram)

```mermaid
erDiagram

    ACADEMIC_YEARS {
        uuid id PK
        string name
        date start_date
        date end_date
        boolean is_active
        datetime created_at
    }

    CLASSES {
        uuid id PK
        string name
        int grade
        uuid homeroom_teacher_id FK
    }

    CLASS_INSTANCES {
        uuid id PK
        uuid class_id FK
        uuid academic_year_id FK
        datetime created_at
    }

    STUDENTS {
        uuid id PK
        string nis
        string name
        datetime created_at
    }

    STUDENT_CLASS_ENROLLMENTS {
        uuid id PK
        uuid student_id FK
        uuid class_instance_id FK
        datetime created_at
    }

    STUDENT_FACES {
        uuid id PK
        uuid student_id FK
        vector embedding
        datetime created_at
    }

    USERS {
        uuid id PK
        string email
        string password_hash
        string role
        boolean is_active
        datetime created_at
        datetime updated_at
    }

    TEACHERS {
        uuid id PK
        uuid user_id FK
        string name
        string nip
        string phone
        datetime created_at
    }

    SUBJECTS {
        uuid id PK
        string code
        string name
        uuid teacher_id FK
        datetime created_at
    }

    CLASS_SUBJECT_SCHEDULES {
        uuid id PK
        uuid class_instance_id FK
        uuid subject_id FK
        uuid teacher_id FK
        int day_of_week
        time start_time
        time end_time
        string room
        datetime created_at
    }

    ATTENDANCES {
        uuid id PK
        uuid student_id FK
        uuid schedule_id FK
        date date
        time time
        string status
        float confidence
        datetime created_at
    }

    ACADEMIC_YEARS ||--o{{ CLASS_INSTANCES : contains
    CLASSES ||--o{{ CLASS_INSTANCES : generates
    USERS ||--o| TEACHERS : owns
    TEACHERS ||--o{{ SUBJECTS : teaches
    TEACHERS ||--o{{ CLASS_SUBJECT_SCHEDULES : handles
    SUBJECTS ||--o{{ CLASS_SUBJECT_SCHEDULES : scheduled
    CLASS_INSTANCES ||--o{{ CLASS_SUBJECT_SCHEDULES : schedules
    CLASS_INSTANCES ||--o{{ STUDENT_CLASS_ENROLLMENTS : includes
    STUDENTS ||--o{{ STUDENT_CLASS_ENROLLMENTS : enrolled_in
    STUDENTS ||--o{{ STUDENT_FACES : has
    STUDENTS ||--o{{ ATTENDANCES : records
    CLASS_SUBJECT_SCHEDULES ||--o{{ ATTENDANCES : session
    TEACHERS ||--o{{ CLASSES : homeroom
```

---

# 4. Database Structure (Detailed)

## academic_years

- id (PK)
- name
- start_date
- end_date
- is_active
- created_at

Constraint: - Only one academic year can be active.

## users

- id (PK)
- email (unique)
- password_hash
- role (ADMIN | TEACHER)
- is_active
- created_at
- updated_at

## teachers

- id (PK)
- user_id (FK, unique)
- name
- nip (optional)
- phone (optional)
- created_at

## classes

- id (PK)
- name (A, B)
- grade (1--6)
- homeroom_teacher_id (FK -> teachers.id, optional)

## class_instances

- id (PK)
- class_id (FK)
- academic_year_id (FK)
- created_at

## students

- id (PK)
- nis (unique)
- name
- created_at

## student_class_enrollments

- id (PK)
- student_id (FK)
- class_instance_id (FK)
- created_at

Unique constraint: (student_id, class_instance_id)

## student_faces

- id (PK)
- student_id (FK)
- embedding VECTOR(512)
- created_at

## subjects (mata_pelajaran)

- id (PK)
- code (optional)
- name
- teacher_id (FK -> teachers.id)
- created_at

## class_subject_schedules (jadwal mata pelajaran)

- id (PK)
- class_instance_id (FK -> class_instances.id)
- subject_id (FK -> subjects.id)
- teacher_id (FK -> teachers.id)
- day_of_week (0-6)
- start_time
- end_time
- room (optional)
- created_at

Unique constraint (suggested): (class_instance_id, day_of_week, start_time)

## attendances

- id (PK)
- student_id (FK)
- schedule_id (FK -> class_subject_schedules.id)
- date
- time
- status
- confidence
- created_at

Unique constraint: (student_id, schedule_id, date)

---

# 5. Academic Year Lifecycle

### Year Transition Flow

1.  Create new academic year
2.  Generate new class instances
3.  Promote students to next grade
4.  Insert new enrollments
5.  Create/adjust subject schedules per class instance
6.  Keep embeddings unchanged

Embeddings remain permanent and are not regenerated yearly.

---

# 6. Face Enrollment & Attendance Flow

## 6.1 Pendaftaran Wajah Siswa (Face Enrollment)

Tujuan: menyimpan embedding wajah siswa yang bersifat permanen (lintas tahun ajaran).

Aktor:

- Admin
- Teacher (wali kelas / guru mapel) sesuai kebutuhan operasional sekolah

Request input yang disarankan:

- `student_id`
- 3–5 foto wajah (multipart/form-data) atau 1 foto berurutan (diulang)

Flow:

1.  Frontend memilih siswa yang akan didaftarkan wajahnya
2.  Frontend mengirim 3–5 foto wajah (multi-angle ringan) ke backend
3.  Backend melakukan face detection dan memastikan tepat 1 wajah per foto
4.  Backend melakukan alignment/cropping wajah (InsightFace pipeline)
5.  Backend menghasilkan embedding 512-dim (ArcFace)
6.  Backend menyimpan embedding ke `student_faces` (boleh >1 embedding per siswa)
7.  Backend mengembalikan ringkasan hasil (jumlah embedding yang tersimpan, id embedding)

Quality gates (minimum):

- Tepat 1 wajah terdeteksi (reject jika 0 atau >1)
- Ukuran wajah minimum (mis. min face bbox >= 80px)
- Pose tidak ekstrem (mis. yaw/pitch di bawah batas)
- Tidak terlalu blur/gelap (reject jika kualitas sangat rendah)

Catatan:

- Raw image tidak disimpan (hanya embedding)
- Embedding tidak diregenerasi ketika tahun ajaran berganti

## 6.2 Absensi (Verifikasi Wajah / Face Recognition Attendance)

Tujuan: mencatat absensi berbasis sesi pelajaran (`schedule_id`) per tanggal.

Flow:

1.  Frontend memilih tahun ajaran aktif, kelas instance, dan sesi pelajaran (schedule)
2.  Frontend mengirim `schedule_id` + foto wajah (multipart/form-data)
3.  Backend melakukan face detection (tepat 1 wajah), lalu membuat embedding
4.  Backend resolve `class_instance_id` dari `schedule_id`
5.  Backend ambil daftar siswa pada `class_instance_id` (enrollment)
6.  Backend melakukan similarity search di `student_faces` untuk kandidat siswa tersebut
7.  Backend memilih kandidat terbaik (best match)
8.  Jika melewati threshold → insert `attendances` (student_id, schedule_id, date, time, status, confidence)
9.  Jika tidak match → response “not matched” tanpa insert attendance

Aturan match yang disarankan:

- Threshold similarity (mis. cosine similarity >= 0.35–0.45, dituning)
- Optional: margin ke kandidat #2 (mis. best - second_best >= 0.05)

Idempotensi:

- Unique constraint: (student_id, schedule_id, date)
- Jika absensi untuk kombinasi tersebut sudah ada: response dapat mengembalikan record yang ada (tanpa membuat data baru)

Performance target:

- < 1 detik per verifikasi end-to-end
- < 0.3 detik matching per kelas (≈50 siswa) dengan optimasi query & index

## 6.3 API yang Dibutuhkan (Untuk Implementasi Flow di Atas)

Pendaftaran wajah:

- `POST /api/v1/students/{student_id}/faces/enroll` (multipart/form-data)
  - form: `images[]` (file, 3–5 file)
  - response: embedding_ids + count + per-image status
- `GET /api/v1/students/{student_id}/faces` (list embedding milik siswa)
- `DELETE /api/v1/students/{student_id}/faces/{face_id}` (hapus embedding tertentu)

Absensi:

- `POST /api/v1/attendance/verify` (multipart/form-data)
  - form: `schedule_id` (uuid), `image` (file)
  - response: matched/unmatched, student_id (jika match), confidence, attendance_id (jika tercatat)

---

# 7. Security Considerations

- Store embeddings only (no raw image storage)
- JWT authentication
- Role-based access (Admin, Teacher)
- Daily database backup
- HTTPS mandatory

---

# 8. Deployment Architecture

Ubuntu Server → Docker → FastAPI → PostgreSQL + pgvector

---

# 9. Scalability

Current: 300 students\
Scalable to: 2000+ students with indexing optimization

Embedding search optimized per class_instance (schedule resolves to class_instance).

---

# 10. Development Plan (PRD untuk Proses Pengembangan)

## Phase 1 — Face Enrollment (Student Faces)

Deliverables:

- Endpoint enroll wajah siswa (3–5 foto) + validasi kualitas minimum
- Penyimpanan embedding ke `student_faces`
- Endpoint list/delete embedding siswa

Acceptance criteria:

- Upload 3–5 foto valid menghasilkan ≥1 embedding tersimpan untuk siswa
- Upload foto tanpa wajah / >1 wajah ditolak dengan error yang jelas
- Tidak ada penyimpanan raw image di server

## Phase 2 — Attendance Verification (Recognition + Insert Attendance)

Deliverables:

- Implementasi `/attendance/verify` menghasilkan embedding dan melakukan matching
- Filter kandidat siswa berdasarkan enrollment dari schedule → class_instance
- Insert attendance sesuai unique constraint per hari

Acceptance criteria:

- Foto siswa terdaftar menghasilkan match yang konsisten dan mencatat attendance
- Foto siswa tidak terdaftar menghasilkan response unmatched dan tidak menulis attendance
- Pemanggilan berulang di tanggal yang sama tidak menduplikasi data

## Phase 3 — Performance & Hardening

Deliverables:

- Optimasi query similarity search (pgvector) dan strategi index
- Rate limiting dasar untuk endpoint upload/verifikasi
- Observability sederhana (logging, latency metrics)

Acceptance criteria:

- Matching per kelas ≈50 siswa konsisten <0.3 detik pada server target
- Error handling konsisten dan tidak membocorkan informasi sensitif

END OF DOCUMENT
