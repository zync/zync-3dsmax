import unittest

from arnold_model import ArnoldModel
from base_model import RendererType


class TestArnoldModel(unittest.TestCase):

  def setUp(self):
    self.minimum_version = unicode(ArnoldModel.STANDALONE_MINIMUM_SUPPORTED_MAXTOA_VERSION)

  def test_should_be_compatible_with_arnold_renderer(self):
    # given
    renderer_name = 'Arnold 5'

    # then
    self.assertTrue(ArnoldModel.is_compatible_with_renderer(renderer_name))

  def test_should_be_incompatible_with_other_renderers(self):
    # given
    other_renderer = 'Some Other Renderer'
    scanline_renderer = 'Scanline Renderer'
    vray_renderer = 'V-Ray Adv 3.60.04'

    # then
    self.assertFalse(ArnoldModel.is_compatible_with_renderer(other_renderer))
    self.assertFalse(ArnoldModel.is_compatible_with_renderer(scanline_renderer))
    self.assertFalse(ArnoldModel.is_compatible_with_renderer(vray_renderer))

  def test_should_raise_value_error_when_no_version_specified(self):
    self.assertRaises(ValueError, ArnoldModel, None, None, False)

  def test_should_raise_value_error_when_incorrect_version(self):
    self.assertRaises(ValueError, ArnoldModel, 'x.1.2', None, False)

  def test_should_raise_value_error_when_version_below_minimum(self):
    self.assertRaises(ValueError, ArnoldModel, '2.3.30', None, True)

  def test_should_return_correct_job_type_when_v1(self):
    # given
    model = ArnoldModel('1.2.3', None, False)

    # then
    self.assertEqual('3dsmax', model.job_type)

  def test_should_return_correct_job_type_when_v2(self):
    # given
    model = ArnoldModel(self.minimum_version, None, True)

    # when
    model.use_standalone = True

    # then
    self.assertEqual('3dsmax_arnold', model.job_type)

  def test_should_return_pretty_renderer_name(self):
    # given
    model = ArnoldModel('1.2.3', None, False)

    # then
    self.assertEqual('Arnold', model.pretty_renderer_name)

  def test_should_return_correct_renderer_type(self):
    # given
    model = ArnoldModel(self.minimum_version, None, True)

    # then
    self.assertEqual(RendererType.ARNOLD, model.renderer_type)

  def test_should_correctly_augment_scene_info(self):
    # given
    model = ArnoldModel(self.minimum_version, None, True)
    model.assets = []
    model.extra_assets = []
    model.project_path = 'project_path'
    model.xrefs = []
    model.aovs = ['albedo', 'opacity']

    # when
    scene_info = model._get_scene_info()

    # then
    self.assertEqual(self.minimum_version, scene_info['maxtoa_version'])
    self.assertEqual(['albedo', 'opacity'], scene_info['aovs'])

  def test_should_correctly_update_scene_files_when_v1(self):
    # given
    model = ArnoldModel('1.2.3', lambda name: name.replace('.', '_generated.'),
                        False)
    model.original_scene_file = 'scene_file.max'

    # when
    model.update_scene_file_path()

    # then
    self.assertEqual('scene_file.max', model.scene_file)

  def test_should_correctly_update_scene_files_when_v2(self):
    # given
    model = ArnoldModel(self.minimum_version, lambda name: name + '_generated', True)
    model.original_scene_file = 'scene_file.max'

    # when
    model.use_standalone = True
    model.camera_name = 'camera'
    model.update_scene_file_path()

    # then
    self.assertEqual('scene_file_camera_generated.*.ass', model.scene_file)
    self.assertEqual('scene_file_camera_generated..ass',
                     model.standalone_scene_file)


def main():
  unittest.main()


if __name__ == '__main__':
  main()
