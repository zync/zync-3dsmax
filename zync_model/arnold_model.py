"""Contains Arnold-specific data model for 3ds Max Zync plugin."""

import os
from base_model import BaseModel
from base_model import RendererType


class ArnoldModel(BaseModel):
  """Arnold-specific data model for 3ds Max Zync plugin."""

  @staticmethod
  def is_compatible_with_renderer(actual_renderer_name):
    """Checks if ArnoldModel can be used for a given renderer."""
    return 'arnold' in actual_renderer_name.lower()

  def __init__(self, version, scene_path_generator):
    """Class constructor.

    Args:
      version: MAXtoA version.
      scene_path_generator: function producing actual path were exported scene
        files are saved.
    """
    super(ArnoldModel, self).__init__()
    if version is None:
      raise ValueError('Undefined Arnold version')
    self.renderer_version = version
    self._scene_path_generator = scene_path_generator
    self._original_scene_file = None
    self._standalone_scene_file_prefix = None

  @property
  def job_type(self):
    """Gets the job type."""
    if self.use_standalone:
      return '3dsmax_arnold'
    return super(ArnoldModel, self).job_type

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
    return 'Arnold'

  @property
  def renderer_type(self):
    """Gets the renderer type."""
    return RendererType.ARNOLD

  def _get_scene_info(self):
    scene_info = super(ArnoldModel, self)._get_scene_info()
    scene_info['maxtoa_version'] = self.renderer_version
    return scene_info

  @property
  def scene_file(self):
    """Gets the scene file path.

    This path is meant to be used for submission to Zync and can contain
    wildcards (e.g. for stand-alone export, there are multiple scene files,
    one for each exported frame.

    Should be used after call to update_scene_file_path.
    """
    if self.use_standalone and not self.upload_only:
      return self._standalone_scene_file_prefix + '*.ass'
    return self.original_scene_file

  @property
  def standalone_scene_file(self):
    """Gets the standalone scene file path.

    This path is meant to be used by Arnold exporter. It differs from scene_file
    as it doesn't have wildcards - exporter automatically appends the frame
    number to the scene name, just before the extension.

    Should be used after call to update_scene_file_path.
    """
    return self._standalone_scene_file_prefix + '.ass'

  def update_scene_file_path(self):
    """Updates the scene and stand-alone scene file paths.

    The update is necessary to refresh scene file names, because they depend
    on other fields of the model.
    """
    filename, _ = os.path.splitext(self.original_scene_file)
    filename += '_' + str(self.camera_name)
    filename = self._scene_path_generator(filename) + '.'
    self._standalone_scene_file_prefix = filename
