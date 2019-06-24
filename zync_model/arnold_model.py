"""Contains Arnold-specific data model for 3ds Max Zync plugin."""

from functools import total_ordering
import os
from base_model import BaseModel
from base_model import RendererType


@total_ordering
class MaxtoaVersion(object):

  @staticmethod
  def from_string(version):
    try:
      components = [int(component) for component in version.split('.')]
      assert len(components) == 3
    except (ValueError, AssertionError, AttributeError):
      raise ValueError('Invalid MaxToA version %s' % version)
    return MaxtoaVersion(components[0], components[1], components[2])

  def __init__(self, major, minor, patch):
    self.major = major
    self.minor = minor
    self.patch = patch

  def __eq__(self, other):
    return self.major == other.major and self.minor == other.minor and self.patch == other.patch

  def __lt__(self, other):
    if self.major != other.major:
      return self.major < other.major
    if self.minor != other.minor:
      return self.minor < other.minor
    if self.patch != other.patch:
      return self.patch < other.patch
    return False

  def __unicode__(self):
    return "%d.%d.%d" % (self.major, self.minor, self.patch)

  def __str__(self):
    return unicode(self).encode('utf-8')


class ArnoldModel(BaseModel):
  """Arnold-specific data model for 3ds Max Zync plugin."""

  STANDALONE_MINIMUM_SUPPORTED_MAXTOA_VERSION = MaxtoaVersion(3, 0, 32)

  @staticmethod
  def is_compatible_with_renderer(actual_renderer_name):
    """Checks if ArnoldModel can be used for a given renderer."""
    return 'arnold' in actual_renderer_name.lower()

  def __init__(self, version_string, scene_path_generator, standalone):
    """Class constructor.

    Args:
      version_string: MAXtoA version.
      scene_path_generator: function producing actual path were exported scene
        files are saved.
      standalone: indicates if the stand-alone scene will be used.
    """
    super(ArnoldModel, self).__init__(standalone)
    version = MaxtoaVersion.from_string(version_string)
    if standalone and version < ArnoldModel.STANDALONE_MINIMUM_SUPPORTED_MAXTOA_VERSION:
      raise ValueError('Unsupported MaxToA version: %s. Minimum version is: %s' % (version_string, ArnoldModel.STANDALONE_MINIMUM_SUPPORTED_MAXTOA_VERSION))
    self.renderer_version = version_string
    self._scene_path_generator = scene_path_generator
    self._original_scene_file = None
    self._standalone_scene_file_prefix = None
    self._aovs = []

  @property
  def job_type(self):
    """Gets the job type."""
    if self.is_standalone:
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

  @property
  def aovs(self):
    """Gets or sets the list of aovs."""
    return self._aovs

  @aovs.setter
  def aovs(self, aovs):
    self._aovs = aovs

  def _get_scene_info(self):
    scene_info = super(ArnoldModel, self)._get_scene_info()
    scene_info['maxtoa_version'] = self.renderer_version
    scene_info['aovs'] = self.aovs
    return scene_info

  @property
  def scene_file(self):
    """Gets the scene file path.

    This path is meant to be used for submission to Zync and can contain
    wildcards (e.g. for stand-alone export, there are multiple scene files,
    one for each exported frame.

    Should be used after call to update_scene_file_path.
    """
    if self.is_standalone and not self.upload_only:
      return self._standalone_scene_file_prefix + '*.ass'
    return self.original_scene_file

  @property
  def instance_renderer_type(self):
    """Gets the renderer type used by Zync API to retrieve instance types."""
    if self.is_standalone:
      return 'standalone-arnold'
    return 'arnold'

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
