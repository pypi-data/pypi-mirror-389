import pytest
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock, call
import os
from datetime import timedelta
from gcs_easy.auth import get_credentials
from gcs_easy.client import GCSClient, _load_config


class TestAuth:
    @patch('gcs_easy.auth.Path')
    def test_get_credentials_from_config_yml(self, mock_path_class):
        # Create a more realistic mock setup
        mock_config_path = MagicMock()
        mock_config_path.exists.return_value = True
        mock_config_path.parent = MagicMock()

        # Mock the chain: Path(__file__).parent.parent.parent / "config.yml"
        mock_path_class.return_value = mock_config_path

        # Mock yaml.safe_load
        with patch('gcs_easy.auth.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {'GOOGLE_APPLICATION_CREDENTIALS': 'credentials/test.json'}

            with patch('builtins.open', mock_open()):
                with patch('google.oauth2.service_account.Credentials.from_service_account_file') as mock_creds:
                    mock_creds.return_value = 'mock_credentials'
                    result = get_credentials()
                    # Just verify it was called with a string path and correct scopes
                    mock_creds.assert_called_once()
                    call_args = mock_creds.call_args
                    assert isinstance(call_args[0][0], str)  # First arg should be a string path
                    assert call_args[1]['scopes'] == ['https://www.googleapis.com/auth/devstorage.read_write']
                    assert result == 'mock_credentials'

    @patch('gcs_easy.auth.Path')
    def test_get_credentials_missing_config_yml(self, mock_path_class):
        # Mock config.yml not existing
        mock_path_instance = mock_path_class.return_value
        mock_path_instance.exists.return_value = False

        with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS not found in config.yml"):
            get_credentials()

    @patch('gcs_easy.auth.Path')
    def test_get_credentials_empty_config_yml(self, mock_path_class):
        # Mock config.yml existing but empty
        mock_path_instance = mock_path_class.return_value
        mock_path_instance.exists.return_value = True

        with patch('gcs_easy.auth.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {}

            with patch('builtins.open', mock_open()):
                with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS not found in config.yml"):
                    get_credentials()

    @patch('gcs_easy.auth.Path')
    def test_get_credentials_invalid_config_yml(self, mock_path_class):
        # Mock config.yml existing but with invalid content
        mock_path_instance = mock_path_class.return_value
        mock_path_instance.exists.return_value = True

        with patch('gcs_easy.auth.yaml.safe_load') as mock_yaml:
            mock_yaml.return_value = {'GOOGLE_APPLICATION_CREDENTIALS': ''}

            with patch('builtins.open', mock_open()):
                with pytest.raises(ValueError, match="GOOGLE_APPLICATION_CREDENTIALS not found in config.yml"):
                    get_credentials()


class TestGCSClient:
    @patch('gcs_easy.client._load_config')
    @patch('gcs_easy.client.get_credentials')
    @patch('google.cloud.storage.Client')
    def test_init_with_config_defaults(self, mock_storage_client, mock_get_creds, mock_load_config):
        # Mock config loading
        mock_load_config.return_value = {
            'default_bucket': 'test-bucket',
            'location': 'US',
            'uniform_access': False
        }
        mock_get_creds.return_value = 'mock_creds'
        mock_client_instance = MagicMock()
        mock_storage_client.return_value = mock_client_instance

        # Test with no parameters - should use config defaults
        client = GCSClient()

        mock_get_creds.assert_called_once()
        mock_storage_client.assert_called_once_with(project=None, credentials='mock_creds')
        assert client.bucket_name == 'test-bucket'
        assert client.default_prefix == ''
        # _ensure_bucket should not be called since create_bucket_if_missing=False
        mock_client_instance.get_bucket.assert_not_called()

    @patch('gcs_easy.client._load_config')
    @patch('gcs_easy.client.get_credentials')
    @patch('google.cloud.storage.Client')
    def test_init_with_explicit_params(self, mock_storage_client, mock_get_creds, mock_load_config):
        # Mock config loading
        mock_load_config.return_value = {
            'default_bucket': 'config-bucket',
            'location': 'EU',
            'uniform_access': True
        }
        mock_get_creds.return_value = 'mock_creds'
        mock_client_instance = MagicMock()
        mock_storage_client.return_value = mock_client_instance

        # Test with explicit parameters - should override config
        client = GCSClient(
            project='test-project',
            default_bucket='explicit-bucket',
            create_bucket_if_missing=True,
            location='ASIA',
            uniform_access=False
        )

        mock_get_creds.assert_called_once()
        mock_storage_client.assert_called_once_with(project='test-project', credentials='mock_creds')
        assert client.bucket_name == 'explicit-bucket'
        assert client.default_prefix == ''
        # _ensure_bucket should be called since create_bucket_if_missing=True
        mock_client_instance.get_bucket.assert_called_once_with('explicit-bucket')

    @patch('gcs_easy.client._load_config')
    @patch('gcs_easy.client.get_credentials')
    @patch('google.cloud.storage.Client')
    def test_init_with_bucket_path(self, mock_storage_client, mock_get_creds, mock_load_config):
        # Mock config loading with bucket path
        mock_load_config.return_value = {
            'default_bucket': 'test-bucket/folder/subfolder',
            'location': 'EU',
            'uniform_access': True
        }
        mock_get_creds.return_value = 'mock_creds'
        mock_client_instance = MagicMock()
        mock_storage_client.return_value = mock_client_instance

        # Test with bucket path - should parse bucket and prefix
        client = GCSClient()

        mock_get_creds.assert_called_once()
        mock_storage_client.assert_called_once_with(project=None, credentials='mock_creds')
        assert client.bucket_name == 'test-bucket'
        assert client.default_prefix == 'folder/subfolder/'
        # _ensure_bucket should not be called since create_bucket_if_missing=False
        mock_client_instance.get_bucket.assert_not_called()

    @patch('gcs_easy.client._load_config')
    @patch('gcs_easy.client.get_credentials')
    @patch('google.cloud.storage.Client')
    @patch('gcs_easy.client.Path')
    def test_upload_file(self, mock_path_class, mock_storage_client, mock_get_creds, mock_load_config):
        # Mock config
        mock_load_config.return_value = {
            'chunk_size': 1024,
            'cache_control': 'max-age=300'
        }

        # Mock credentials and storage client
        mock_get_creds.return_value = 'mock_creds'
        mock_client_instance = MagicMock()
        mock_storage_client.return_value = mock_client_instance

        # Mock bucket and blob
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob

        # Mock file path
        mock_file_path = MagicMock()
        mock_path_class.return_value = mock_file_path
        mock_file_path.stat.return_value = MagicMock(st_size=512)
        mock_file_path.open.return_value.__enter__.return_value = MagicMock()
        mock_file_path.name = 'test.txt'

        # Mock blob reload
        mock_blob.reload.return_value = None
        mock_blob.generation = '123'

        client = GCSClient(default_bucket='test-bucket')

        result = client.upload_file('test.txt', 'blob.txt')

        assert result.bucket == 'test-bucket'
        assert result.blob == 'blob.txt'
        assert result.size == 512
        assert result.generation == '123'

    @patch('gcs_easy.client._load_config')
    @patch('gcs_easy.client.get_credentials')
    @patch('google.cloud.storage.Client')
    def test_signed_url(self, mock_storage_client, mock_get_creds, mock_load_config):
        # Mock config
        mock_load_config.return_value = {
            'signed_url_expires_minutes': 30
        }

        # Mock credentials and storage client
        mock_get_creds.return_value = 'mock_creds'
        mock_client_instance = MagicMock()
        mock_storage_client.return_value = mock_client_instance

        # Mock bucket and blob
        mock_bucket = MagicMock()
        mock_blob = MagicMock()
        mock_client_instance.bucket.return_value = mock_bucket
        mock_bucket.blob.return_value = mock_blob
        mock_blob.generate_signed_url.return_value = 'https://signed-url.com'

        client = GCSClient(default_bucket='test-bucket')

        url = client.signed_url('test-blob.txt')

        mock_blob.generate_signed_url.assert_called_once()
        call_args = mock_blob.generate_signed_url.call_args
        assert call_args[1]['expiration'] == timedelta(minutes=30)
        assert url == 'https://signed-url.com'


class TestCLI:
    @patch('gcs_easy.cli.GCSClient')
    @patch('builtins.print')
    def test_upload_command(self, mock_print, mock_gcs_client):
        """Test the upload command."""
        mock_client_instance = MagicMock()
        mock_gcs_client.return_value = mock_client_instance

        with patch('sys.argv', ['gcs-easy', 'upload', '--bucket', 'test-bucket', '--src', 'local.txt', '--dst', 'remote.txt']):
            from gcs_easy.cli import main
            main()

        mock_gcs_client.assert_called_once_with(default_bucket='test-bucket')
        mock_client_instance.upload_file.assert_called_once_with('local.txt', 'remote.txt', make_public=False)
        mock_print.assert_called_once_with('OK')

    @patch('gcs_easy.cli.GCSClient')
    @patch('builtins.print')
    def test_upload_command_with_public_flag(self, mock_print, mock_gcs_client):
        """Test the upload command with public flag."""
        mock_client_instance = MagicMock()
        mock_gcs_client.return_value = mock_client_instance

        with patch('sys.argv', ['gcs-easy', 'upload', '--bucket', 'test-bucket', '--src', 'local.txt', '--dst', 'remote.txt', '--public']):
            from gcs_easy.cli import main
            main()

        mock_gcs_client.assert_called_once_with(default_bucket='test-bucket')
        mock_client_instance.upload_file.assert_called_once_with('local.txt', 'remote.txt', make_public=True)
        mock_print.assert_called_once_with('OK')

    @patch('gcs_easy.cli.GCSClient')
    @patch('builtins.print')
    def test_download_command(self, mock_print, mock_gcs_client):
        """Test the download command."""
        mock_client_instance = MagicMock()
        mock_gcs_client.return_value = mock_client_instance

        with patch('sys.argv', ['gcs-easy', 'download', '--bucket', 'test-bucket', '--src', 'remote.txt', '--dst', 'local.txt']):
            from gcs_easy.cli import main
            main()

        mock_gcs_client.assert_called_once_with(default_bucket='test-bucket')
        mock_client_instance.download_file.assert_called_once_with('remote.txt', 'local.txt')
        mock_print.assert_called_once_with('OK')

    @patch('gcs_easy.cli.GCSClient')
    @patch('builtins.print')
    def test_list_command(self, mock_print, mock_gcs_client):
        """Test the list command."""
        mock_client_instance = MagicMock()
        mock_gcs_client.return_value = mock_client_instance
        mock_client_instance.list.return_value = ['file1.txt', 'file2.txt']

        with patch('sys.argv', ['gcs-easy', 'list', '--bucket', 'test-bucket']):
            from gcs_easy.cli import main
            main()

        mock_gcs_client.assert_called_once_with(default_bucket='test-bucket')
        mock_client_instance.list.assert_called_once_with(prefix='')
        assert mock_print.call_count == 2
        mock_print.assert_has_calls([call('file1.txt'), call('file2.txt')])

    @patch('gcs_easy.cli.GCSClient')
    @patch('builtins.print')
    def test_list_command_with_prefix(self, mock_print, mock_gcs_client):
        """Test the list command with prefix."""
        mock_client_instance = MagicMock()
        mock_gcs_client.return_value = mock_client_instance
        mock_client_instance.list.return_value = ['folder/file1.txt']

        with patch('sys.argv', ['gcs-easy', 'list', '--bucket', 'test-bucket', '--prefix', 'folder/']):
            from gcs_easy.cli import main
            main()

        mock_gcs_client.assert_called_once_with(default_bucket='test-bucket')
        mock_client_instance.list.assert_called_once_with(prefix='folder/')
        mock_print.assert_called_once_with('folder/file1.txt')

    @patch('gcs_easy.cli.GCSClient')
    @patch('builtins.print')
    def test_sign_command(self, mock_print, mock_gcs_client):
        """Test the sign command."""
        mock_client_instance = MagicMock()
        mock_gcs_client.return_value = mock_client_instance
        mock_client_instance.signed_url.return_value = 'https://signed-url.com'

        with patch('sys.argv', ['gcs-easy', 'sign', '--bucket', 'test-bucket', '--path', 'file.txt', '--minutes', '30']):
            from gcs_easy.cli import main
            main()

        mock_gcs_client.assert_called_once_with(default_bucket='test-bucket')
        mock_client_instance.signed_url.assert_called_once_with('file.txt', expires=timedelta(minutes=30))
        mock_print.assert_called_once_with('https://signed-url.com')

    @patch('gcs_easy.cli.print_detailed_report')
    def test_permissions_command_default_bucket(self, mock_print_report):
        """Test the permissions command with default bucket."""
        with patch('sys.argv', ['gcs-easy', 'permissions']):
            from gcs_easy.cli import main
            main()

        mock_print_report.assert_called_once()

    @patch('gcs_easy.cli.print_detailed_report')
    def test_permissions_command_specific_bucket(self, mock_print_report):
        """Test the permissions command with specific bucket."""
        with patch('sys.argv', ['gcs-easy', 'permissions', '--bucket', 'specific-bucket']):
            from gcs_easy.cli import main
            main()

        mock_print_report.assert_called_once()

    def test_cli_has_permissions_command(self):
        """Test that the CLI has the permissions command available."""
        import subprocess
        import sys

        # Test that the CLI shows permissions in help
        result = subprocess.run([
            sys.executable, '-c',
            'from gcs_easy.cli import main; import sys; sys.argv = ["gcs-easy", "--help"]; main()'
        ], capture_output=True, text=True, cwd='src')

        # Should exit with error code 0 (successful help display)
        # and should contain 'permissions' in the output
        assert 'permissions' in result.stdout or 'permissions' in result.stderr

    def test_cli_requires_command(self):
        """Test that CLI requires a command."""
        with patch('sys.argv', ['gcs-easy']):
            from gcs_easy.cli import main
            with pytest.raises(SystemExit):  # argparse exits with error when required arg missing
                main()