"""
Central controller object responsible for all data-related tasks.
"""

from __future__ import annotations
from typing import List
from typing import TYPE_CHECKING
import shutil
import os
import webbrowser

from sqlalchemy import create_engine, select, text
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool
from sqlalchemy.sql.expression import func
from sqlalchemy import event

from diffcrawler.utils.dbscheme import Base, Resource, Revision
from diffcrawler.utils.requester import Requester
from diffcrawler.utils.misc import IncorrectFileFormatError
from diffcrawler.utils.misc import is_valid_url

if TYPE_CHECKING:
    from diffcrawler.widgets.main_window import MainWindow
from diffcrawler.widgets.list_pane import ListPane
from diffcrawler.widgets.property_pane import PropertyPane
from diffcrawler.widgets.action_pane import ActionPane
from diffcrawler.widgets.text_window import TextWindow

class DataController:
    """
    The data controller performs all tasks related to working with underlying data and gets/gives feedback from/to the UI elements
    to reflect changes. UI formatting is separated out entirely to the individual UI widgets.

    There is one data controller per file/main window.
    """

    def __init__(self, path: str, main_wdw: MainWindow, list_pane: ListPane, property_pane: PropertyPane, action_pane: ActionPane) -> None:
        
        self._main_wdw = main_wdw
        self.list_pane = list_pane
        self.property_pane = property_pane
        self.action_pane = action_pane
        
        # Register this controller in the corresponding UI widgets so that they can communicate with it
        self.list_pane.controller = self
        self.property_pane.controller = self
        self.action_pane.controller = self

        
        self._selected_resources = []

        # If no path to a file is given, this is an empty in-memory db
        self.path = path if path else ':memory:'
        
        self._check_file_format(self.path)

        self.session = self._setup_session(self.path)

        if self.is_memory_db:
            Base.metadata.create_all(self.session.get_bind())
            self.session.commit()
        # Load saved resources
        else:
            stmt = select(Resource).order_by(Resource.order)
            res_from_file = list(self.session.scalars(stmt))
            for res in res_from_file:
                self.list_pane.insert_resource(res)
        
        # Instantiate requester object
        self.requester = Requester(max_workers=5)

    @property
    def path(self) -> str:
        return self._path
    
    @path.setter
    def path(self, new_path) -> None:
        """Set the path and adjust the title of the main window accordingly."""
        self._path = new_path

        wdw_title_suffix = 'DiffCrawler'

        if self.is_memory_db:
            wdw_title_prefix = 'Untitled'
        else:
            wdw_title_prefix = os.path.basename(new_path)

        self._main_wdw.title(f'{wdw_title_prefix} - {wdw_title_suffix}')

    def new_resource(self, url: str | None = None) -> None:
        """Create a new resource and append it to the DB and the resources list."""
        if url is not None:
            # Return if passed URL is invalid
            if not is_valid_url(url):
                return

        # If there is a selection of resources, insert the new one right below the selection.
        # Otherwise at end of list.        
        max_order_val = self.session.query(func.max(Resource.order)).scalar()
        if self._selected_resources:
            new_order_val = self._selected_resources[-1].order + 1
            self.session.query(Resource).where(Resource.order >= new_order_val).update({Resource.order: Resource.order + 1})
        elif max_order_val is not None:
            new_order_val = max_order_val + 1
        # First item in list (list was empty)
        else:
            new_order_val = 0

        new_res = Resource(order=new_order_val, url=url) 
        self.session.add(new_res)
        self.session.flush()

        self.list_pane.insert_resource(new_res)
        self.list_pane.select_resource(new_res)

        # If no url was passed, focus field for user to directly enter it
        if not url:
            self.property_pane.focus_url_field()

    def remove_resource(self) -> None:
        """Remove a resource from DB and list."""
        for resource in self._selected_resources:
            self.session.query(Resource).where(Resource.order > resource.order).update({Resource.order: Resource.order - 1})
            self.session.delete(resource)
            self.session.flush()

            self.list_pane.remove_resource(resource)
    
    def property_changed(self, property: str, new_value: str | int | bool) -> None:
        """Change a property of resource and update list."""
        for resource in self._selected_resources:
           setattr(resource, property, new_value)
           self.list_pane.update_resource(resource)
        
        self.session.flush()

    def selection_changed(self, new_sel: list) -> None:
        """Handle change of selected resources and update property pane."""
        self._selected_resources = self._query_resources_from_list(new_sel)

        self.property_pane.show_properties(self._selected_resources)
        
    def _query_resources_from_list(self, sel: list) -> List[Resource]:
        """Get a list of resource objects from a list of IDs."""
        stmt = select(Resource).where(Resource.id_.in_(sel)).order_by(Resource.order)

        return list(self.session.scalars(stmt))

    def fetch(self) -> None:
        """Fetch (retrieve) the current version of the selected resource(s) and update DB and UI.""" 
        fetch_list = []

        for resource in self._selected_resources:
            # Exclude empty URLs
            if resource.url == '':
                continue
            url_dict = {
                'id': resource.id_,
                'url': resource.url,
                'timeout': resource.timeout
            }
            fetch_list.append(url_dict)
            # Set that the process of fetching has started for resource
            resource.in_process = True
            self.list_pane.update_resource(resource)

        # Hand list of to-be-fetched URLs to the requester
        self.requester.fetch_concurrently(fetch_list, self.fetch_done)
    
    def fetch_done(self, id_: int, success: bool, content: str | None) -> None:
        """Callback for requester to be notified when fetching has been donde for a resource (URL)"""

        # Get resource correspondig to ID
        stmt = select(Resource).where(Resource.id_ == id_)
        resource = self.session.scalars(stmt).one()
        # Set that process has finished
        resource.in_process = False
        
        # Fetching was successful and there is source code in the payload
        if success and content is not None:
            resource.fetch_successful = True
            new_rev = Revision(resource=resource, src=content)
            self.session.add(new_rev)
            self.session.flush()

            # Remove oldest revision if there are more than 3 (only 3 are kept)
            sorted_revs = sorted(resource.revisions)
            if len(resource.revisions) > 3:
                resource.revisions.remove(sorted_revs[0])
                
            # Calculate diff lines for resource
            resource.update_diff_lines()

            # Set resource to unread if more lines changed than defined in threshold
            if resource.diff_lines >= resource.diff_thresh:
                resource.is_unread = True
            
        # In case of network error (probably DNS error or timeout)
        else:
            resource.fetch_successful = False

        self.session.flush()
        self.list_pane.update_resource(resource)
    
    def undo_fetch(self) -> None:
        """Revert last fetch (useful if new fetch contains a maintenance message, for example)."""
        for resource in self._selected_resources:
            if resource.cur_revision:
                resource.revisions.remove(resource.cur_revision)
                resource.update_diff_lines()
                self.session.flush()
                self.list_pane.update_resource(resource)

    def show_diff(self) -> None:
        """Open window showing the diff between the last two revisions."""

        for resource in self._selected_resources:
            diff = resource.get_diff()
            if diff:
                TextWindow(self._main_wdw, diff, title=resource.url)

    def open_url(self) -> None:
        """Open URLs of selected resources in new browser tabs and mark resources as read."""
        for resource in self._selected_resources:
            if resource.url:
                webbrowser.open(resource.url, new=2)
                resource.is_unread = False
                self.session.flush()
                self.list_pane.update_resource(resource)
                
    def mark_read(self) -> None:
        """Mark selected resources as read."""
        for resource in self._selected_resources:
            resource.is_unread = False
            self.session.flush()
            self.list_pane.update_resource(resource)
        

    def save_as(self, path: str) -> None:
        """Save open file (or memory DB) to a new file and change path to that new file."""
        # No "Save as" if paths are equal
        if path == self.path:
            return self.save()
        
        # Ugly hack to allow "Save as":
        # Commiting to the DB overwrites old file, but "Save as" needs to preserve old file
        # and write into new file. So old file is copied to temp file before committing:
        if not self.is_memory_db:
            oldpath = self.path
            tempfile = self.path + '-tmp'
            shutil.copy2(oldpath, tempfile)

        self.session.commit()

        # Get ids of selected resources to repopulate with updated session later.
        sel_res_ids = [res.id_ for res in self._selected_resources]

        # Allow "overwriting" destination location by deleting existing file.
        # Check to "really want to overwrite" must be done by save file dialog before!
        if os.path.exists(path):
            os.remove(path)

        # Old file is now updated and can be moved to new location:
        if not self.is_memory_db:
            os.rename(oldpath, path)
        # Or new file is created from memory db:
        else:
            self.session.execute(text('VACUUM main INTO :path'), {'path': path})

        # Replace session with new session for new path
        self.session = self._setup_session(path)

        # Move tempfile back to old location
        if not self.is_memory_db:
            os.rename(tempfile, oldpath)

        # Update current path to new path and repopulate selected resources with new session
        self.path = path
        self._selected_resources = self._query_resources_from_list(sel_res_ids)

        return True
            
    def save(self) -> None:
        """Save current file to disk."""
        self.session.commit()
        return True

    @property    
    def has_unsaved_changes(self) -> bool:
        """Return if the file as unsaved changes."""
        return self.session.info['commit_pending']
    
    @property
    def is_memory_db(self) -> bool:
        """Return of the open window is just 'saved' in a memory DB"""
        return True if self.path == ':memory:' else False
    
    def selected_urls(self) -> str:
        """Return a comma-separated string of the URLs of the selected resources."""
        return ','.join([res.url for res in self._selected_resources])
    
    def _check_file_format(self, path: str):
        """Check if the file format is correct and if not, raise exception."""
        # TODO: Implement better way to check if file is of correct format
        if not path.endswith('.dfc') and not path == ':memory:':
            raise IncorrectFileFormatError('Cannot open file: incorrect file format detected')
            
    def _setup_session(self, path: str) -> Session:
        """Setup everything needed for the SQLite session and start it."""
        # Thread checking needs to be switched off because after fetching, session is accessed from worker
        # threads (not from main thread). Using StaticPool (one global connection) should solve problem
        # of possible data corruption in case of concurrent connections.        
        engine = create_engine(f'sqlite:///{path}',
                               connect_args={'check_same_thread': False},
                               poolclass=StaticPool)

        session = Session(engine)

        # Keep the rollback journal in memory only (avoids writing '-journal' files to disk)
        session.execute(text('PRAGMA journal_mode = MEMORY'))

        # No commits are pending when session is 'fresh'
        session.info['commit_pending'] = False

        # Setup event listeners to keep info on wheteher or not there is any commit pending (unsaved changes)
        @event.listens_for(session, 'after_flush')
        def flush_happened(session, flush_context):
            session.info['commit_pending'] = True

        @event.listens_for(session, 'after_commit')
        def commit_happened(session):
            session.info['commit_pending'] = False

        return session