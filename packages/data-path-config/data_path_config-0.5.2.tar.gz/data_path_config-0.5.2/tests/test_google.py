import pytest
from data_path_config.google.sheet import GoogleSheetsManager

def test_imports():
    """Test that GoogleSheetsManager can be imported and has expected methods."""
    assert GoogleSheetsManager
    assert hasattr(GoogleSheetsManager, 'list_sheets')
    assert hasattr(GoogleSheetsManager, 'sheet_df')
    assert hasattr(GoogleSheetsManager, 'append_to_sheet')
    assert hasattr(GoogleSheetsManager, 'df_to_sheet')
    assert hasattr(GoogleSheetsManager, 'insert_key_value')

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

# Note: Actual API tests require valid Google Sheets credentials and sheet IDs
# To run full tests, set up a test sheet and credentials in .env