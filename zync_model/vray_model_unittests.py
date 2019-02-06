import unittest

from base_model import RendererType
from base_model_unittests import create_test_model
from vray_model import VrayModel
from vray_model import VrayRtEngineType


def generate_scene_path(path):
  return path + '_generated'


def create_standalone_vray_model(version='3.60.04', rt_engine_type=None):

  class VrayStandalone(VrayModel):

    def __init__(self):
      super(VrayStandalone, self).__init__(version, rt_engine_type,
                                           generate_scene_path)

    @property
    def use_standalone(self):
      return True

    @use_standalone.setter
    def use_standalone(self, _):
      pass

  return create_test_model(VrayStandalone)


def create_non_standalone_vray_model(version='3.60.04', rt_engine_type=None):

  class VrayNonStandalone(VrayModel):

    def __init__(self):
      super(VrayNonStandalone, self).__init__(version, rt_engine_type,
                                              generate_scene_path)

    @property
    def use_standalone(self):
      return False

    @use_standalone.setter
    def use_standalone(self, _):
      pass

  return create_test_model(VrayNonStandalone)


class TestVrayModel(unittest.TestCase):

  def test_should_be_compatible_with_vray_renderer(self):
    # given
    renderer_name = 'V-Ray Adv 3.60.04'

    # then
    self.assertTrue(VrayModel.is_compatible_with_renderer(renderer_name))

  def test_should_be_incompatible_with_non_vray_renderer(self):
    # given
    arnold_renderer = 'Arnold 3.1.0'
    other_renderer = 'Some Other Renderer'
    scanline_renderer = 'Scanline Renderer'

    # then
    self.assertFalse(VrayModel.is_compatible_with_renderer(arnold_renderer))
    self.assertFalse(VrayModel.is_compatible_with_renderer(other_renderer))
    self.assertFalse(VrayModel.is_compatible_with_renderer(scanline_renderer))

  def test_should_raise_value_error_when_no_version_specified(self):
    self.assertRaises(ValueError, VrayModel, None, None, None)

  def test_should_raise_value_error_when_rt_engine_is_opencl(self):
    self.assertRaises(ValueError, VrayModel, '3.60.04', VrayRtEngineType.OPENCL,
                      None)

  def test_should_return_correct_job_type_for_standalone(self):
    # given
    model = create_standalone_vray_model()

    # when
    job_type = model.job_type

    # then
    self.assertEqual('3dsmax_vray', job_type)

  def test_should_return_correct_job_type_for_non_standalone(self):
    # given
    model = create_non_standalone_vray_model()

    # when
    job_type = model.job_type

    # then
    self.assertEqual('3dsmax', job_type)

  def test_should_return_pretty_renderer_name_for_all_engines(self):
    # given
    models = [
        create_standalone_vray_model(),
        create_standalone_vray_model(rt_engine_type=VrayRtEngineType.CPU),
        create_standalone_vray_model(rt_engine_type=VrayRtEngineType.CUDA),
    ]

    # when
    pretty_renderer_names = [model.pretty_renderer_name for model in models]

    # then
    self.assertEqual(['V-Ray', 'V-Ray RT (CPU)', 'V-Ray RT (CUDA)'],
                     pretty_renderer_names)

  def test_should_return_production_engine_name_for_all_engines(self):
    # given
    models = [
        create_standalone_vray_model(),
        create_standalone_vray_model(rt_engine_type=VrayRtEngineType.CPU),
        create_standalone_vray_model(rt_engine_type=VrayRtEngineType.CUDA),
    ]

    # when
    production_engine_names = [
        model._production_engine_name for model in models
    ]

    # then
    self.assertEqual(['unknown', 'cpu', 'cuda'], production_engine_names)

  def test_should_return_correct_renderer_type(self):
    # given
    model = create_standalone_vray_model()

    # then
    self.assertEqual(RendererType.VRAY, model.renderer_type)

  def test_should_return_correct_usage_tags_for_all_rt_engines(self):
    # given
    cuda_model = create_standalone_vray_model(
        rt_engine_type=VrayRtEngineType.CUDA)
    no_rt_model = create_standalone_vray_model()
    cpu_model = create_standalone_vray_model(
        rt_engine_type=VrayRtEngineType.CPU)

    # then
    self.assertEqual('3dsmax_vray_rt_gpu', cuda_model.usage_tag)
    self.assertEqual('3dsmax', no_rt_model.usage_tag)
    self.assertEqual('3dsmax', cpu_model.usage_tag)

  def test_should_return_correct_scene_info_for_non_rt_engine(self):
    # given
    model = create_standalone_vray_model()
    model.update_scene_file_path()

    # when
    scene_info = model._get_scene_info()

    # then
    self.assertEqual('3.60.04', scene_info['vray_version'])
    self.assertEqual('unknown', scene_info['vray_production_engine_name'])

  def test_should_return_correct_scene_file_when_non_standalone(self):
    # given
    model = create_non_standalone_vray_model()
    model.original_scene_file = 'scene_file.max'
    model.update_scene_file_path()

    # then
    self.assertEqual('scene_file.max', model.scene_file)

  def test_should_return_corrent_scene_files_when_standalone(self):
    # given
    model = create_standalone_vray_model()
    model.camera_name = 'camera'
    model.frame_range = '1-10'
    model.frame_step = '3'
    model.original_scene_file = 'scene_file.max'
    model.update_scene_file_path()

    # then
    self.assertEqual('scene_file_1-10x3_camera_generated.vrscene',
                     model.scene_file)
    self.assertEqual('scene_file_1-10x3_camera_generated.vrscene',
                     model.standalone_scene_file)


def main():
  unittest.main()


if __name__ == '__main__':
  main()
