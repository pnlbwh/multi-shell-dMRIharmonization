import unittest
import tempfile
import os
from unittest.mock import patch, Mock
from ..automate_harmonization_pipeline import run_bash_script, setup_logging, main


class TestPipeline(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_setup_logging(self):
        logfile = os.path.join(self.temp_dir.name, "test.log")
        setup_logging(logfile, False)
        self.assertTrue(os.path.exists(logfile))

    @patch("subprocess.Popen")
    def test_run_bash_script(self, mock_popen):
        mock_config = {
            "ref_list": "ref_list",
            "tar_list": "tar_list",
            "ref_name": "ref_name",
            "tar_name": "tar_name",
            "template": "template",
            "nproc": "nproc",
        }
        process_mock = Mock()
        attrs = {"poll.return_value": None}
        process_mock.configure_mock(**attrs)
        mock_popen.return_value = process_mock
        run_bash_script(mock_config, False, False, False, False)
        mock_popen.assert_called_once()

    # For main function, please mock necessary dependencies such as 'argparse.ArgumentParser.parse_args'
    # and add tests to ensure the function calls its dependencies as expected


if __name__ == "__main__":
    unittest.main()
