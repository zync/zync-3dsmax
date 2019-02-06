import unittest

from arnold_model import ArnoldModel
from base_model import RendererType


class TestArnoldModel(unittest.TestCase):

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
    self.assertRaises(ValueError, ArnoldModel, None, None)

  def test_should_return_correct_job_type_when_non_standalone(self):
    # given
    model = ArnoldModel('1.2.3', None)

    # then
    self.assertEqual('3dsmax', model.job_type)

  def test_should_return_correct_job_type_when_standalone(self):
    # given
    model = ArnoldModel('1.2.3', None)

    # when
    model.use_standalone = True

    # then
    self.assertEqual('3dsmax_arnold', model.job_type)

  def test_should_return_pretty_renderer_name(self):
    # given
    model = ArnoldModel('1.2.3', None)

    # then
    self.assertEqual('Arnold', model.pretty_renderer_name)

  def test_should_return_correct_renderer_type(self):
    # given
    model = ArnoldModel('1.2.3', None)

    # then
    self.assertEqual(RendererType.ARNOLD, model.renderer_type)

  def test_should_correctly_augment_scene_info(self):
    # given
    model = ArnoldModel('1.2.3', None)
    model.assets = []
    model.extra_assets = []
    model.project_path = 'project_path'
    model.xrefs = []

    # when
    scene_info = model._get_scene_info()

    # then
    self.assertEqual('1.2.3', scene_info['maxtoa_version'])

  def test_should_correctly_update_scene_files_when_non_standalone(self):
    # given
    model = ArnoldModel('1.2.3', lambda name: name.replace('.', '_generated.'))
    model.original_scene_file = 'scene_file.max'

    # when
    model.update_scene_file_path()

    # then
    self.assertEqual('scene_file.max', model.scene_file)

  def test_should_correctly_update_scene_files_when_standalone(self):
    # given
    model = ArnoldModel('1.2.3', lambda name: name + '_generated')
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
