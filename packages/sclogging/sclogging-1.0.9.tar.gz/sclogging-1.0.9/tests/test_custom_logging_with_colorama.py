import unittest
from unittest.mock import MagicMock, patch

from sclogging.custom_logging_with_colorama import (
    Timer,
    clear_logs,
    get_logger,
    set_config,
)

# Centralize patch target to avoid repetition and typos
MODULE = "sclogging.custom_logging_with_colorama"


class TestClearLogs(unittest.TestCase):
    pass


class TestGetLogger(unittest.TestCase):
    @patch(f"{MODULE}.logging.getLogger")
    @patch(f"{MODULE}.verify_level")
    @patch(f"{MODULE}.fix_mod_path", return_value="test_module")
    def test_get_logger_default_values(
        self, mock_fix_mod_path, mock_verify_level, mock_get_logger
    ):
        mock_verify_level.return_value = True
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        logger = get_logger()
        self.assertEqual(logger, mock_logger)
        mock_fix_mod_path.assert_called_once()
        mock_get_logger.assert_called_with("test_module")


class TestTimer(unittest.TestCase):
    @patch(f"{MODULE}.verify_level", return_value=True)
    @patch(f"{MODULE}.logging.getLogger")
    @patch(f"{MODULE}.fix_mod_path", return_value="test_module")
    def test_timer_initialization(
        self, mock_fix_mod_path, mock_get_logger, mock_verify_level
    ):
        timer = Timer(level="DEBUG")
        self.assertEqual(timer.level, "DEBUG")
        self.assertEqual(timer.count, Timer._counter)
        mock_fix_mod_path.assert_called_once()
        mock_verify_level.assert_called_once_with("DEBUG")

    @patch(f"{MODULE}.time.perf_counter", side_effect=[0.0, 2.5])
    @patch(f"{MODULE}.logging.getLogger")
    def test_timer_start_and_stop(self, mock_get_logger, mock_perf_counter):
        timer = Timer(level="INFO")
        timer.start_timer(note="Starting timer")
        elapsed_time = timer.stop_timer(note="Elapsed: %t% seconds")
        self.assertEqual(elapsed_time, 2.5)
        self.assertEqual(timer.start_time, 0)  # Reset after stopping
        mock_perf_counter.assert_called()

    @patch(f"{MODULE}.logging.getLogger")
    @patch(f"{MODULE}.verify_level")
    @patch(f"{MODULE}.fix_mod_path", return_value="custom_name")
    def test_get_logger_with_custom_name_and_level(
        self, mock_fix_mod_path, mock_verify_level, mock_get_logger
    ):
        mock_verify_level.return_value = True
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        logger = get_logger(caller_name="custom", level="DEBUG")
        self.assertEqual(logger, mock_logger)
        mock_fix_mod_path.assert_called_once_with("custom")
        mock_get_logger.assert_called_with("custom_name")

    @patch(f"{MODULE}.logging.getLogger")
    @patch(f"{MODULE}.verify_level")
    @patch(f"{MODULE}.fix_mod_path", return_value="test_module")
    @patch(f"{MODULE}.logging.FileHandler")
    def test_get_logger_logs_to_file(
        self, mock_file_handler, mock_fix_mod_path, mock_verify_level, mock_get_logger
    ):
        mock_verify_level.return_value = True
        mock_logger = MagicMock()
        mock_get_logger.return_value = mock_logger
        mock_file_handler_instance = MagicMock()
        mock_file_handler.return_value = mock_file_handler_instance
        logger = get_logger(log_to_file=True)
        self.assertEqual(logger, mock_logger)
        mock_file_handler.assert_called_once()
        mock_logger.addHandler.assert_called_once_with(mock_file_handler_instance)

    @patch(f"{MODULE}.os.listdir")
    @patch(f"{MODULE}.base_logger")
    def test_clear_logs_no_files(self, mock_logger, mock_listdir):
        mock_listdir.return_value = []
        clear_logs(force=True)
        mock_logger.warning.assert_called_once_with("No files to delete")

    @patch(f"{MODULE}.shutil.rmtree")
    @patch(f"{MODULE}.os.listdir")
    @patch(f"{MODULE}.set_log_path")
    @patch(f"{MODULE}.base_logger")
    def test_clear_logs_force_delete(
        self, mock_logger, mock_set_log_path, mock_listdir, mock_rmtree
    ):
        mock_listdir.return_value = ["log1.txt", "log2.txt"]
        clear_logs(force=True)
        mock_rmtree.assert_called_once()
        mock_set_log_path.assert_called_once_with(auto_create=True)
        mock_logger.info.assert_called_once_with("Log directory cleared")
        mock_logger.warning.assert_not_called()

    @patch(f"{MODULE}.py_option.inputYesNo")
    @patch(f"{MODULE}.shutil.rmtree")
    @patch(f"{MODULE}.os.listdir")
    @patch(f"{MODULE}.set_log_path")
    @patch(f"{MODULE}.base_logger")
    def test_clear_logs_prompt_confirm_delete(
        self, mock_logger, mock_set_log_path, mock_listdir, mock_rmtree, mock_inputYesNo
    ):
        mock_listdir.return_value = ["log1.txt", "log2.txt"]
        mock_inputYesNo.return_value = "yes"
        clear_logs(force=False)
        mock_rmtree.assert_called_once()
        mock_set_log_path.assert_called_once_with(auto_create=True)
        mock_logger.info.assert_called_once_with("Log directory cleared")
        mock_logger.warning.assert_not_called()

    @patch(f"{MODULE}.write_config")
    @patch(f"{MODULE}.verify_level", return_value=True)
    def test_set_config_valid_values(self, mock_verify_level, mock_write_config):
        specific_loggers = {"module_name": "INFO"}
        set_config(
            default_log_level="DEBUG",
            log_file_path="./custom_logs",
            log_extension=".txt",
            log_to_file=True,
            specific_logger_levels=specific_loggers,
        )
        mock_write_config.assert_called_once_with(
            {
                "logging_log_to_file": True,
                "logging_path": "./custom_logs",
                "logging_level": "DEBUG",
                "logging_file_level": "DEBUG",
                "logging_ext": "txt",
                "logging_auto_create_dir": True,
                "spacer": " ",
                "spacer_color": "WHITE",
                "specific_loggers": specific_loggers,
            }
        )

    @patch(f"{MODULE}.write_config")
    @patch(f"{MODULE}.verify_level", side_effect=[False, True])
    def test_set_config_invalid_log_level_defaults(
        self, mock_verify_level, mock_write_config
    ):
        set_config(default_log_level="INVALID", log_file_path="./logs")
        mock_write_config.assert_called_once()

    @patch(f"{MODULE}.shutil.rmtree")
    @patch(f"{MODULE}.os.listdir")
    @patch(f"{MODULE}.set_log_path")
    @patch(f"{MODULE}.base_logger")
    def test_clear_logs_error_handler(
        self, mock_logger, mock_set_log_path, mock_listdir, mock_rmtree
    ):
        mock_listdir.return_value = ["log1.txt", "log2.txt"]
        mock_rmtree.side_effect = OSError("Mock rmtree error")
        with self.assertRaises(OSError):
            clear_logs(force=True)
        mock_logger.error.assert_called()


if __name__ == "__main__":
    unittest.main()
