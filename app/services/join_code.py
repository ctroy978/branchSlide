import re
import secrets

from sqlalchemy.orm import Session

from app.models import Session as InquirySession

JOIN_CODE_LENGTH = 4
JOIN_CODE_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
JOIN_CODE_PATTERN = re.compile(rf"^[{JOIN_CODE_ALPHABET}]{{{JOIN_CODE_LENGTH}}}$")


def normalize_join_code(code: str) -> str:
    return code.strip().upper()


def is_valid_join_code(code: str) -> bool:
    return bool(JOIN_CODE_PATTERN.match(normalize_join_code(code)))


def generate_join_code(db: Session) -> str:
    for _ in range(200):
        code = "".join(
            secrets.choice(JOIN_CODE_ALPHABET) for _ in range(JOIN_CODE_LENGTH)
        )
        exists = (
            db.query(InquirySession.id)
            .filter(InquirySession.join_code == code)
            .first()
        )
        if not exists:
            return code
    raise RuntimeError("Could not allocate a unique join code")


def backfill_missing_join_codes(db: Session) -> int:
    sessions = (
        db.query(InquirySession)
        .filter(
            (InquirySession.join_code.is_(None)) | (InquirySession.join_code == "")
        )
        .all()
    )
    for inquiry_session in sessions:
        inquiry_session.join_code = generate_join_code(db)
    return len(sessions)