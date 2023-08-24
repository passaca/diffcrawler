"""
ORM class definitions for the database model: resource (website/URL)
and revision (retrieved source at specific time).
"""

from __future__ import annotations

import datetime

from typing import List

from sqlalchemy import ForeignKey
from sqlalchemy import String
from sqlalchemy import Integer
from sqlalchemy import DateTime
from sqlalchemy import Boolean
from sqlalchemy import UnicodeText
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy.orm import Mapped

from diffcrawler.utils.misc import SiteDiff


class Base(DeclarativeBase):
    pass

class Resource(Base):
    """
    Resource table. Containing the individual to-be-tracked resources (websites/URLs).
    """

    __tablename__ = 'resource'

    id_ = mapped_column(Integer, primary_key=True)
    # Order of the resources in list (for display purposes)
    order = mapped_column(Integer)
    url = mapped_column(String(2000), default=None)
    # Marked as favorite or not
    is_fav = mapped_column(Boolean, nullable=False, default=False)
    # Timeout in seconds
    timeout = mapped_column(Integer, default=2)
    # Thereshold from which the changes are considered "significant"
    diff_thresh = mapped_column(Integer, default=2)
    # Have significant changes beed reviewed? (open URL or mark unread)
    is_unread = mapped_column(Boolean, nullable=False, default=False)
    added_date = mapped_column(DateTime, default=datetime.datetime.now)
    # Did the last fetch succeed without error?
    fetch_successful = mapped_column(Boolean, default=None)
    # Number of changed lines (diff) between last two revisions
    diff_lines = mapped_column(Integer, default=None)
    # Revisions (retrieved sources) associated with this resource
    revisions = relationship('Revision', back_populates='resource')


    # Fetch is currently in process? (not a mapped value!)
    in_process = False

    @property
    def cur_date(self) -> datetime.datetime | None:
        """Return fetch date of newest revision"""
        if len(self.revisions) >= 1:
            return (sorted(self.revisions)[-1].fetch_date)
        else:
            return None

    @property
    def prev_date(self) -> datetime.datetime | None:
        """Return fetch date of previous revision"""
        if len(self.revisions) >= 2:
            return (sorted(self.revisions)[-2].fetch_date)
        else:
            return None
        
    @property
    def cur_revision(self) -> Revision | None:
        """Return newest revision"""
        sorted_revs = sorted(self.revisions)

        if len(self.revisions) >= 1:
            return sorted_revs[-1]
        else:
            return None
        
    @property
    def prev_revision(self) -> Revision | None:
        """Return previous revision"""
        sorted_revs = sorted(self.revisions)

        if len(self.revisions) >= 2:
            return sorted_revs[-2]
        else:
            return None
    
    def update_diff_lines(self):
        """Calculate and update the diff lines using the two most recent revisions."""
        if self.cur_revision and self.prev_revision:
            diff = SiteDiff(self.cur_revision.src, self.prev_revision.src)
            self.diff_lines = diff.num_changes()
        # Set diff to zero if there aren't at least two revisions available
        else:
            self.diff_lines = 0

    def get_diff(self):
        """Calculate and return the diff between the two most recent revisions."""
        if self.cur_revision and self.prev_revision:
            diff = SiteDiff(self.cur_revision.src, self.prev_revision.src)
            return diff.diff()
        # Return none of there aren't at least two revisions available
        else:
            return None
            

class Revision(Base):
    """
    Revision table. Containing the individually retrieved sources/snapshots (e.g. 'revisions').
    """

    __tablename__ = 'revision'

    id_ = mapped_column(Integer, primary_key=True)
    # Resource ID to which this revision corresponds
    resource_id = mapped_column(ForeignKey('resource.id_'))
    # Resource object to which this revision belongs
    resource = relationship('Resource', back_populates='revisions')
    fetch_date = mapped_column(DateTime, default=datetime.datetime.now)
    # Retrieved website source
    src = mapped_column(UnicodeText, nullable=False, default='')

    # Allow comparing revisions by date
    def __lt__(self, other: Revision) -> bool:
        return (self.fetch_date < other.fetch_date)
    
    def __gt__(self, other: Revision) -> bool:
        return (self.fetch_date > other.fetch_date)

