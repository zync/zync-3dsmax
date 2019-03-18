import unittest

from arnold_model import MaxtoaVersion


class TestMaxtoaVersion(unittest.TestCase):

  def test_should_raise_value_error_when_invalid_version(self):
    self.assertRaises(ValueError, MaxtoaVersion.from_string, 'x.1.2')

  def test_should_raise_value_error_when_missing_components(self):
    self.assertRaises(ValueError, MaxtoaVersion.from_string, '2.3')

  def test_should_raise_value_error_when_too_many_components(self):
    self.assertRaises(ValueError, MaxtoaVersion.from_string, '2.3.4.5')

  def test_should_correctly_parse_version(self):
    # given
    version_string = '2.3.456'

    # when
    version = MaxtoaVersion.from_string(version_string)

    # then
    self.assertEqual(MaxtoaVersion(2, 3, 456), version)

  def test_should_correctly_compare_versions(self):
    # given
    version_1_2_3 = MaxtoaVersion(1, 2, 3)
    version_2_0_0 = MaxtoaVersion(2, 0, 0)
    version_2_1_0 = MaxtoaVersion(2, 1, 0)
    version_2_1_1 = MaxtoaVersion(2, 1, 1)

    # then
    self.assertGreater(version_2_1_1, version_2_1_0)
    self.assertGreater(version_2_1_0, version_2_0_0)
    self.assertGreater(version_2_0_0, version_1_2_3)
    self.assertFalse(version_2_0_0 < version_2_0_0)


def main():
  unittest.main()


if __name__ == '__main__':
  main()