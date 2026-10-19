from sqlalchemy import func

from website.web.bootstrap import db


class Tag(db.Model):  # type: ignore[name-defined, misc]
    """Represent a tag.
    Polymorphic association, where a single Tag model can be
    associated with multiple other models (Product, Comment, Bundle, etc.)."""

    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.String(), nullable=False)
    creation_timestamp = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Generic relationship fields
    target_id = db.Column(db.Integer, nullable=False)
    target_type = db.Column(db.String(50), nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "text", "target_id", "target_type", name="uq_tag_text_target"
        ),
    )

    def __repr__(self) -> str:
        return f"<Tag {self.text} on {self.target_type}({self.target_id})>"
