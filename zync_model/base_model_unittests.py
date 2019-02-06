import unittest

from base_model import BaseModel


def create_test_model_with_dummy_renderer():

  class BaseModelWithDummyRenderer(BaseModel):

    @property
    def renderer_type(self):
      return 'test_renderer'

  return create_test_model(BaseModelWithDummyRenderer)


def create_test_model(ModelClass):
  model = ModelClass()
  model.assets = ['C:\\asset1', 'C:\\asset2']
  model.camera_name = 'CameraName'
  model.chunk_size = 10
  model.extra_assets = ['C:\\extra_asset1', 'C:\\extra_asset2']
  model.frame_range = '1-10'
  model.frame_step = '1'
  model.instance_count = 10
  model.instance_type = 'zync-instance'
  model.max_version = '(20,1,2,3)'
  model.notify_complete = True
  model.output_name = 'C:\\output.png'
  model.plugin_version = '1.2.3'
  model.priority = 50
  model.project = 'test-project'
  model.project_path = 'C:\\Path\\To\\Project'
  model.resolution = (640, 480)
  model.original_scene_file = 'C:\\scene.max'
  model.sync_extra_assets = True
  model.upload_only = False
  model.xrefs = ['C:\\xref1', 'C:\\xref2']
  return model


class TestBaseModel(unittest.TestCase):

  def test_should_duplicate_assets(self):
    # given
    assets = ['x']
    model = BaseModel()

    # when
    model.assets = assets

    # then
    self.assertEqual(assets, model.assets)
    self.assertIsNot(assets, model.assets)

  def test_should_duplicate_extra_assets(self):
    # given
    extra_assets = ['x']
    model = BaseModel()

    # when
    model.extra_assets = extra_assets

    # then
    self.assertEqual(extra_assets, model.extra_assets)
    self.assertIsNot(extra_assets, model.extra_assets)

  def test_should_return_correct_full_frame_range(self):
    # given
    model = BaseModel()
    model.frame_range = '1-10'
    model.frame_step = 3

    # when
    full_frame_range = model.full_frame_range

    # then
    self.assertEqual('1-10x3', str(full_frame_range))

  def test_should_return_false_if_instance_not_preemptible(self):
    # given
    model = BaseModel()
    model.instance_type = 'zync-instance'

    # then
    self.assertFalse(model.is_instance_type_preemptible)

  def test_should_return_true_if_instance_is_preemptible(self):
    # given
    model = BaseModel()
    model.instance_type = 'zync-instance-PREEMPTIBLE'

    # then
    self.assertTrue(model.is_instance_type_preemptible)

  def test_should_return_correct_job_type(self):
    # given
    model = BaseModel()

    # then
    self.assertEqual('3dsmax', model.job_type)

  def test_should_raise_exception_on_renderer_type(self):
    # given
    model = BaseModel()

    # then
    self.assertRaises(AttributeError, lambda: model.renderer_type)

  def test_should_return_resolution_as_tuple(self):
    # given
    model = BaseModel()
    model.x_resolution = 640
    model.y_resolution = 480

    # when
    resolution = model.resolution

    # then
    self.assertEqual((640, 480), resolution)

  def test_should_return_correct_usage_tag(self):
    # given
    model = BaseModel()

    # then
    self.assertEqual('3dsmax', model.usage_tag)

  def test_should_duplicate_xrefs(self):
    # given
    xrefs = ['x']
    model = BaseModel()

    # when
    model.xrefs = xrefs

    # then
    self.assertEqual(xrefs, model.xrefs)
    self.assertIsNot(xrefs, model.xrefs)

  def test_should_validate_correct_attributes(self):
    # given
    model = create_test_model_with_dummy_renderer()

    # then
    try:
      model._validate_data()
    except Exception:
      self.fail('Should not throw exception')

  def test_should_raise_value_error_when_no_output_name(self):
    # given
    model = create_test_model_with_dummy_renderer()
    model.output_name = ''

    # then
    self.assertRaises(ValueError, model._validate_data)

  def test_should_raise_value_error_when_output_name_has_no_extension(self):
    # given
    model = create_test_model_with_dummy_renderer()
    model.output_name = 'C:\\output'

    # then
    self.assertRaises(ValueError, model._validate_data)

  def test_should_raise_value_error_when_no_instance_type(self):
    # given
    model = create_test_model_with_dummy_renderer()
    model.instance_type = ''

    # then
    self.assertRaises(ValueError, model._validate_data)

  def test_should_raise_value_error_when_no_project(self):
    # given
    model = create_test_model_with_dummy_renderer()
    model.project = ''

    # then
    self.assertRaises(ValueError, model._validate_data)

  def test_should_raise_value_error_when_sync_extra_assets_and_no_assets(self):
    # given
    model = create_test_model_with_dummy_renderer()
    model.sync_extra_assets = True
    model.extra_assets = []

    # then
    self.assertRaises(ValueError, model._validate_data)

  def test_should_return_true_if_filename_has_extension(self):
    # given
    filename = 'output.png'

    # then
    self.assertTrue(BaseModel._has_file_extension(filename))

  def test_should_return_true_if_filename_has_no_extension(self):
    # given
    filename = 'output.'

    # then
    self.assertFalse(BaseModel._has_file_extension(filename))

  def test_should_return_correct_submission_params(self):
    # given
    model = create_test_model_with_dummy_renderer()
    expected_params = {
        'camera': 'CameraName',
        'chunk_size': 10,
        'distributed': 0,
        'frange': '1-10',
        'instance_type': 'zync-instance',
        'notify_complete': 1,
        'num_instances': 10,
        'output_name': 'C:/output.png',
        'plugin_version': '1.2.3',
        'priority': 50,
        'proj_name': 'test-project',
        'renderer': 'test_renderer',
        'step': '1',
        'sync_extra_assets': True,
        'upload_only': 0,
        'xres': 640,
        'yres': 480,
        'scene_info': {
            'max_version': '(20,1,2,3)',
            'project_path': 'C:/Path/To/Project',
            'references': [
                'C:/asset1', 'C:/asset2', 'C:/extra_asset1', 'C:/extra_asset2'
            ],
            'xrefs': ['C:/xref1', 'C:/xref2'],
        }
    }
    expected_scene = 'C:/scene.max'

    # when
    scene, params = model.get_submission_params()

    # then
    self.assertEqual(expected_params, params)
    self.assertEqual(expected_scene, scene)

  def test_should_sanitize_path(self):
    # given
    path = 'C:\\Windows\\Path'

    # when
    sanitized_path = BaseModel._sanitize_path(path)

    # then
    self.assertEquals('C:/Windows/Path', sanitized_path)

  def test_should_sanitize_paths(self):
    # given
    paths = ['C:\\Windows\\Path1', 'D:\\Windows\\Path2', '/Non/Windows/Path']

    # when
    sanitized_paths = BaseModel._sanitize_paths(paths)

    # then
    self.assertEquals(
        ['C:/Windows/Path1', 'D:/Windows/Path2', '/Non/Windows/Path'],
        sanitized_paths)


def main():
  unittest.main()


if __name__ == '__main__':
  main()
