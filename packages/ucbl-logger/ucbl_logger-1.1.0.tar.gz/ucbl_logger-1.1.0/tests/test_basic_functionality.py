import unittest
import os
from unittest.mock import patch

class TestBasicFunctionality(unittest.TestCase):
    """Basic functionality tests that work without complex logger setup"""

    def test_import_ucbl_logger(self):
        """Test that UCBLLogger can be imported"""
        from ucbl_logger.logger import UCBLLogger
        self.assertTrue(UCBLLogger)

    def test_create_logger_instance(self):
        """Test that UCBLLogger can be instantiated"""
        # Disable enhanced features to avoid initialization issues
        with patch.dict(os.environ, {'UCBL_DISABLE_EKS_FEATURES': 'true'}):
            from ucbl_logger.logger import UCBLLogger
            logger = UCBLLogger(enable_eks_features=False)
            self.assertIsNotNone(logger)

    def test_logger_info_method(self):
        """Test that info method exists and can be called"""
        with patch.dict(os.environ, {'UCBL_DISABLE_EKS_FEATURES': 'true'}):
            from ucbl_logger.logger import UCBLLogger
            logger = UCBLLogger(enable_eks_features=False)
            # Just test that the method exists and doesn't crash
            try:
                logger.info("Test message")
                success = True
            except Exception:
                success = False
            self.assertTrue(success)

    def test_logger_methods_exist(self):
        """Test that required methods exist on the logger"""
        with patch.dict(os.environ, {'UCBL_DISABLE_EKS_FEATURES': 'true'}):
            from ucbl_logger.logger import UCBLLogger
            logger = UCBLLogger(enable_eks_features=False)
            
            # Check that methods exist
            self.assertTrue(hasattr(logger, 'info'))
            self.assertTrue(hasattr(logger, 'debug'))
            self.assertTrue(hasattr(logger, 'warning'))
            self.assertTrue(hasattr(logger, 'error'))
            self.assertTrue(hasattr(logger, 'log_risk'))
            self.assertTrue(hasattr(logger, 'log_anomaly'))

if __name__ == '__main__':
    unittest.main()