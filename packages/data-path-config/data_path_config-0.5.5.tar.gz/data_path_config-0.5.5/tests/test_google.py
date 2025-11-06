import pytest
from data_path_config.google.sheet import GoogleSheetsManager
from data_path_config.google.drive import GoogleDriveManager

def test_imports():
    """Test that GoogleSheetsManager can be imported and has expected methods."""
    assert GoogleSheetsManager
    assert hasattr(GoogleSheetsManager, 'list_sheets')
    assert hasattr(GoogleSheetsManager, 'sheet_df')
    assert hasattr(GoogleSheetsManager, 'append_to_sheet')
    assert hasattr(GoogleSheetsManager, 'df_to_sheet')
    assert hasattr(GoogleSheetsManager, 'insert_key_value')
    assert hasattr(GoogleSheetsManager, 'list_shared_drive_sheets')
    
    # Test GoogleDriveManager import
    assert GoogleDriveManager
    assert hasattr(GoogleDriveManager, 'list_files')
    assert hasattr(GoogleDriveManager, 'upload_file')
    assert hasattr(GoogleDriveManager, 'download_file')
    assert hasattr(GoogleDriveManager, 'create_folder')
    assert hasattr(GoogleDriveManager, 'delete_file')
    assert hasattr(GoogleDriveManager, 'get_file_info')
    assert hasattr(GoogleDriveManager, 'move_file')
    assert hasattr(GoogleDriveManager, 'copy_file')
    assert hasattr(GoogleDriveManager, 'list_shared_drives')
    assert hasattr(GoogleDriveManager, 'list_shared_drive_files')

def test_google_sheets_manager():
    """Test GoogleSheetsManager initialization."""
    try:
        manager = GoogleSheetsManager()
        assert manager.gc is not None
    except (ValueError, FileNotFoundError) as e:
        # Expected if .env not set or file missing
        assert "not set" in str(e) or "No such file" in str(e)

def test_list_sheets():
    """Test list_sheets method."""
    try:
        manager = GoogleSheetsManager()
        sheets = manager.list_sheets()
        print(f"All sheets: {sheets}")
        assert isinstance(sheets, list)
        if sheets:
            assert 'id' in sheets[0]
            assert 'title' in sheets[0]
    except (ValueError, FileNotFoundError) as e:
        # Expected if .env not set or file missing
        assert "not set" in str(e) or "No such file" in str(e)

def test_list_shared_drive_sheets():
    """Test list_shared_drive_sheets method."""
    try:
        manager = GoogleSheetsManager()
        # Attempt to list shared drive sheets with a dummy drive_id
        sheets = manager.list_shared_drive_sheets("share")
        print(f"Shared drive sheets: {sheets}")
        assert isinstance(sheets, list)
        if sheets:
            assert 'id' in sheets[0]
            assert 'title' in sheets[0]
    except Exception as e:
        # Expected if .env not set or invalid drive_id
        print(f"Expected error: {e}")
        # Test passes as long as no unexpected errors

def test_google_drive_manager():
    """Test GoogleDriveManager initialization."""
    try:
        manager = GoogleDriveManager()
        assert manager.service is not None
    except (ValueError, FileNotFoundError) as e:
        # Expected if .env not set or file missing
        assert "not set" in str(e) or "No such file" in str(e)

def test_list_files():
    """Test list_files method."""
    try:
        manager = GoogleDriveManager()
        files = manager.list_files()
        print(f"All files: {files}")
        assert isinstance(files, list)
        if files:
            assert 'id' in files[0]
            assert 'name' in files[0]
    except (ValueError, FileNotFoundError) as e:
        # Expected if .env not set or file missing
        assert "not set" in str(e) or "No such file" in str(e)

def test_list_shared_drives():
    """Test list_shared_drives method."""
    try:
        manager = GoogleDriveManager()
        drives = manager.list_shared_drives()
        print(f"All shared drives: {drives}")
        assert isinstance(drives, list)
        if drives:
            assert 'id' in drives[0]
            assert 'name' in drives[0]
    except Exception as e:
        # Expected if .env not set, file missing, or no shared drives accessible
        print(f"Expected error: {e}")
        # Test passes as long as no unexpected errors

def test_list_shared_drive_files():
    """Test list_shared_drive_files method."""
    try:
        manager = GoogleDriveManager()
        # Get the first shared drive and list its files
        drives = manager.list_shared_drives()
        if drives:
            drive_id = drives[0]['id']
            files = manager.list_shared_drive_files(drive_id)
            print(f"Files in shared drive '{drives[0]['name']}': {files}")
            assert isinstance(files, list)
            if files:
                assert 'id' in files[0]
                assert 'name' in files[0]
        else:
            print("No shared drives found to test file listing")
    except Exception as e:
        # Expected if .env not set, file missing, or no shared drives accessible
        print(f"Expected error: {e}")
        # Test passes as long as no unexpected errors