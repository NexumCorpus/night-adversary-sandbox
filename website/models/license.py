from sqlalchemy import func

from website.web.bootstrap import db


class License(db.Model):  # type: ignore[name-defined, misc]
    """Represent a license.
    https://opensource.org/licenses/alphabetical
    """

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(), default="", nullable=False, unique=True)
    license_id = db.Column(db.String(), default="", nullable=False, unique=True)
    creation_timestamp = db.Column(
        db.DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    def __str__(self) -> str:
        return self.name
