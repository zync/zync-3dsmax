"""Contains V-Ray-specific data model for 3ds Max Zync plugin."""

import os

from base_model import BaseModel
from base_model import RendererType


class VrayRtEngineType(object):
  """Enumeration of all possible V-Ray RT engines for 3ds Max Zync plugin."""
  CPU, OPENCL, CUDA = range(0, 3)

  _NAMES = {
      CPU: 'cpu',
      OPENCL: 'opencl',
      CUDA: 'cuda',
  }

  _PRETTY_NAMES = {
      CPU: 'CPU',
      OPENCL: 'OpenCL',
      CUDA: 'CUDA',
  }

  @staticmethod
  def get_name(type):
    """Gets the Zync-compatible name of RT engine."""
    if type in VrayRtEngineType._NAMES:
      return VrayRtEngineType._NAMES[type]
    return 'unknown'

  @staticmethod
  def get_pretty_name(type):
    """Gets the pretty name of RT engine."""
    if type in VrayRtEngineType._PRETTY_NAMES:
      return VrayRtEngineType._PRETTY_NAMES[type]
    raise ValueError('Unknown V-Ray RT Engine Type')


class VrayModel(BaseModel):
  """V-Ray-specific data model for 3ds Max Zync plugin."""

  @staticmethod
  def is_compatible_with_renderer(actual_renderer_name):
    """Checks if VrayModel can be used for a given renderer."""
    return 'v-ray' in actual_renderer_name.lower()

  def __init__(self, version, rt_engine_type, scene_path_generator, standalone):
    """Class constructor.

    Args:
      version: V-Ray version.
      rt_engine_type: rt engine type from VrayRtEngineType enumeration or None.
      scene_path_generator: function producing actual path were exported scene
        files are saved.
    """
    super(VrayModel, self).__init__(standalone)
    if version is None:
      raise ValueError('Undefined V-Ray version')
    if rt_engine_type == VrayRtEngineType.OPENCL:
      raise ValueError('Only CUDA GPU rendering engine is supported')
    self._rt_engine_type = rt_engine_type
    self.renderer_version = version
    self._scene_path_generator = scene_path_generator
    self._original_scene_file = None
    self._standalone_scene_file = None

  @property
  def job_type(self):
    """Gets the job type."""
    if self.is_standalone:
      return '3dsmax_vray'
    return super(VrayModel, self).job_type

  @property
  def original_scene_file(self):
    """Gets and sets the original scene file path."""
    return self._original_scene_file

  @original_scene_file.setter
  def original_scene_file(self, original_scene_file):
    self._original_scene_file = original_scene_file

  @property
  def pretty_renderer_name(self):
    """Gets the pretty renderer name."""
    renderer_name = 'V-Ray'
    if self._rt_engine_type is not None:
      renderer_name += ' RT (%s)' % VrayRtEngineType.get_pretty_name(
          self._rt_engine_type)
    return renderer_name

  @property
  def renderer_type(self):
    """Gets the renderer type."""
    return RendererType.VRAY

  @property
  def usage_tag(self):
    """Gets the usage tag."""
    if self._rt_engine_type == VrayRtEngineType.CUDA:
      return '3dsmax_vray_rt_gpu'
    return super(VrayModel, self).usage_tag

  @property
  def _production_engine_name(self):
    return VrayRtEngineType.get_name(self._rt_engine_type)

  def _get_scene_info(self):
    scene_info = super(VrayModel, self)._get_scene_info()
    scene_info['vray_version'] = self.renderer_version
    scene_info['vray_production_engine_name'] = self._production_engine_name
    return scene_info

  @property
  def scene_file(self):
    """Gets the standalone scene file path.

    This path is meant to be used for submission to Zync.
    Should be used after call to update_scene_file_path.
    """
    if self.is_standalone and not self.upload_only:
      return self._standalone_scene_file
    return self.original_scene_file

  @property
  def standalone_scene_file(self):
    """Gets the standalone scene file path.

    This path is meant to be used by V-Ray exporter.
    Should be used after call to update_scene_file_path.
    """
    return self._standalone_scene_file

  @property
  def instance_renderer_type(self):
    """Gets the renderer type used by Zync API to retrieve instance types."""
    if self.is_standalone:
      return 'standalone-vray'
    return 'vray'

  def update_scene_file_path(self):
    """Updates the scene and stand-alone scene file paths.

    The update is necessary to refresh scene file names, because they depend
    on other fields of the model.
    """
    filename, _ = os.path.splitext(self._original_scene_file)
    filename += '_' + str(self.full_frame_range)
    filename += '_' + str(self.camera_name)
    filename = self._scene_path_generator(filename) + '.vrscene'
    self._standalone_scene_file = filename
