from datetime import datetime
# from .SharePointAPI import SharePointAPI as SP

class SharePointListItem:
    """
    Represents a generic item in a SharePoint list.

    Provides access to common fields such as ``Id``, ``Title``, ``Created`` and
    ``Modified`` and handles lazy loading of related list data and version
    history. Sub‑classes (e.g. :class:`SharepointSiteCase` or
    :class:`TimeRegistration`) extend this base with domain‑specific properties.
    """
    ''' 
    '''
    settings = {}

    def __init__(self, sp, sharepoint_site, list_guid, settings: dict = None, versions: list = None):
        self.sp = sp
        self.sharepoint_site = sharepoint_site
        self.list_guid = list_guid
        self._list = None
        self._versions = versions
        self.settings = settings

    def __str__(self):
        return self.Title

    @property
    def list(self):
        if not self._list:
            self._list = self.sp.get_list(self.sharepoint_site, self.list_guid)
        return self._list

    @property
    def versions(self) -> list:
        if not self._versions:
            self._versions = self.sp.get_item_versions(self.sharepoint_site, self.list_guid, self.Id) 
            if self._list is not None:
                self._list.CHANGE_DETECTED = True
        return self._versions    
    
    
    @property
    def Id(self) -> str:
        """Unique identifier of the list item."""
        return self.settings['Id']

    @property
    def Title(self) -> str:
        """Title of the list item."""
        return self.settings['Title']

    @property
    def Created(self) -> datetime:
        """
        Timestamp of when the item was created.

        Returns ``None`` if the ``Created`` field is missing or null.
        """
        if 'Created' not in self.settings:
            return None
        elif self.settings['Created'] is None:
            return None
        else:
            return datetime.strptime(self.settings['Created'], '%Y-%m-%dT%H:%M:%SZ')

    @property
    def Modified(self) -> datetime:
        """
        Timestamp of when the item was modified.

        Returns ``None`` if the ``Modified`` field is missing or null.
        """
        if 'Modified' not in self.settings:
            return None
        elif self.settings['Modified'] is None:
            return None
        else:
            return datetime.strptime(self.settings['Modified'], '%Y-%m-%dT%H:%M:%SZ')

    def attach_item(self, file_name, file_path):
        """
        Attach a file to this list item.
    
        Parameters
        ----------
        file_name : str
            The name of the file as it should appear in SharePoint.
        file_path : str
            Local path to the file to be uploaded.
    
        The method reads the file content and uses :meth:`SharePointAPI.attach_file`
        to upload it to the corresponding SharePoint list item.
        """
        with open(file_path, 'r') as f:
            file_content = f.read()

    
        self.sp.attach_file(self.sharepoint_site, self.list, self, file_name, file_content)

    def versions_select_fields(self, select_fields=[]) -> list:
        if not self._versions:
            self._versions = self.sp.get_item_versions(self.sharepoint_site, self.list_guid, self.Id, select_fields) 
        return self._versions

    def update_fields(self, data):
        self.sp.update_item(self.sharepoint_site,
                            self.list_guid, self.Id, data)

class SharepointSiteCase(SharePointListItem):
    
    @property
    def AssignmentType(self) -> str:
        return self.settings['AssignmentType']

    @property
    def CaseClosedTimestamp(self) -> datetime:
        'Timestamp of when the case was closed'
        if 'CaseClosed' not in self.settings:
            return None
        elif self.settings['CaseClosed'] is None:
            return None
        else:
            return datetime.strptime(self.settings['CaseClosed'], '%Y-%m-%dT%H:%M:%SZ')

    @property
    def Due(self) -> datetime:
        'Timestamp of when the case is due'
        if 'DueDate' not in self.settings:
            return None
        elif self.settings['DueDate'] is None:
            return None
        else:
            return datetime.strptime(self.settings['DueDate'], '%Y-%m-%dT%H:%M:%SZ')

    @property
    def Priority(self) -> str:
        return self.settings['Priority']

    @property
    def ResponsibleId(self) -> str:
        return self.settings['AssignedToId']

    @property
    def Status(self) -> str:
        return self.settings['Status']

    @property
    def SolvedInTime(self) -> bool:
        'Bool indicating whether work was solved in time'
        solved_in_time = False
        if self.Due:
            if not self.CaseClosedTimestamp:
                solved_in_time = True
            elif self.CaseClosedTimestamp <= self.Due:
                solved_in_time = True
        else:
            solved_in_time = True
        
        return solved_in_time

    @property
    def WorkBegunTimestamp(self) -> datetime:
        'Timestamp of when work was started on the case'
        if 'WorkBegun' not in self.settings:
            return None
        elif self.settings['WorkBegun'] is None:
            return None
        else:
            return datetime.strptime(self.settings['WorkBegun'], '%Y-%m-%dT%H:%M:%SZ')

    @property
    def DeadlineWorkTimestamp(self) -> datetime:
        'Timestamp of when work should start on the case'
        if 'DeadlineWork' not in self.settings:
            return None
        elif self.settings['DeadlineWork'] is None:
            return None
        else:
            return datetime.strptime(self.settings['DeadlineWork'], '%Y-%m-%dT%H:%M:%SZ')

    @property
    def ReactedInTime(self) -> bool:
        'Bool indicating whether work was started in time'
        reacted_in_time = False
        if self.DeadlineWorkTimestamp:
            if not self.WorkBegunTimestamp:
                reacted_in_time = True
            elif self.WorkBegunTimestamp <= self.DeadlineWorkTimestamp:
                reacted_in_time = True
        else:
            reacted_in_time = True
        return reacted_in_time

    
        
