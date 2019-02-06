import unittest

from base_model import RendererType
from scanline_model import ScanlineModel


class TestScanlineModel(unittest.TestCase):

  def test_should_be_compatible_with_scanline_renderer(self):
    # given
    renderer_name = 'Scanline Renderer'

    # then
    self.assertTrue(ScanlineModel.is_compatible_with_renderer(renderer_name))

  def test_should_be_incompatible_with_non_vray_renderer(self):
    # given
    arnold_renderer = 'Arnold 3.1.0'
    other_renderer = 'Some Other Renderer'
    vray_renderer = 'V-Ray Adv 3.60.04'

    # then
    self.assertFalse(ScanlineModel.is_compatible_with_renderer(arnold_renderer))
    self.assertFalse(ScanlineModel.is_compatible_with_renderer(other_renderer))
    self.assertFalse(ScanlineModel.is_compatible_with_renderer(vray_renderer))

  def test_should_return_pretty_renderer_name(self):
    # given
    model = ScanlineModel()

    # then
    self.assertEqual('Scanline Renderer', model.pretty_renderer_name)

  def test_should_return_correct_renderer_type(self):
    # given
    model = ScanlineModel()

    # then
    self.assertEqual(RendererType.SCANLINE, model.renderer_type)


def main():
  unittest.main()


if __name__ == '__main__':
  main()
