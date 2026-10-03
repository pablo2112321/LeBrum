from io import BytesIO
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from .validators import scan_uploaded_file


class AntivirusValidationTests(SimpleTestCase):
    @patch('LeBrum.validators.shutil.which', return_value='clamscan')
    @patch('LeBrum.validators.subprocess.run')
    def test_clean_file_is_accepted(self, run, _which):
        run.return_value.returncode = 0
        scan_uploaded_file(BytesIO(b'clean content'), 'clamscan')
        run.assert_called_once()

    @patch('LeBrum.validators.shutil.which', return_value='clamscan')
    @patch('LeBrum.validators.subprocess.run')
    def test_infected_file_is_rejected(self, run, _which):
        run.return_value.returncode = 1
        with self.assertRaises(ValidationError):
            scan_uploaded_file(BytesIO(b'infected content'), 'clamscan')
