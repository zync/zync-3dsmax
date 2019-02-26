"""Contains the data model for 3ds Max Zync plugin."""

import os.path
import re


class RendererType(object):
  """Enumeration of all possible renderers for 3ds Max Zync plugin."""
  ARNOLD = 'arnold'
  SCANLINE = 'scanline'
  VRAY = 'vray'


class FrameRange(object):
  """Frame range with step."""

  extract_regex = re.compile(r'^(?P<start>\d+)(-(?P<end>\d+))?$')

  @staticmethod
  def from_string_and_step(frame_range_no_step, step):
    """Creates frame range from string and step.

    Input string must be of form SF-EF or SF, where SF and EF are numbers
    and are interpreted as start and end frame.
    """
    match = FrameRange.extract_regex.match(frame_range_no_step)
    if match:
      start = int(match.group('start'))
      if match.group('end'):
        end = int(match.group('end'))
      else:
        end = start
    else:
      raise ValueError('Invalid frame range')
    return FrameRange(start, end, step)

  def __init__(self, start, end, step):
    """Class constructor."""
    self.start = start
    self.end = end
    self.step = step

  def to_string_without_step(self):
    """Returns a string representation without the step."""
    return '%s-%s' % (self.start, self.end)

  def __str__(self):
    """Returns a string representation.

    String representation of FrameRange is in form SF-EFxST or SF-SFxST
    if start and end frame are the equal. Examples: 1-10x2, 3-3x1.
    """
    return '%sx%s' % (self.to_string_without_step(), self.step)


class BaseModel(object):
  """3ds Max-specific data model."""

  def __init__(self, standalone):
    """Class constructor."""
    self._is_standalone = standalone
    self._assets = None
    self.camera_name = None
    self.chunk_size = None
    self._extra_assets = None
    self.frame_range = None
    self.frame_step = None
    self.instance_count = None
    self.instance_type = None
    self.instance_type_label = None
    self.max_version = None
    self.notify_complete = None
    self._original_scene_file = None
    self.output_name = None
    self.plugin_version = None
    self.priority = None
    self.project = None
    self.project_path = None
    self.sync_extra_assets = None
    self.upload_only = None
    self._xrefs = None
    self.x_resolution = None
    self.y_resolution = None

  @property
  def assets(self):
    """Gets or sets the list of asset file paths.

    When set, the input list is duplicated.
    """
    return self._assets

  @assets.setter
  def assets(self, assets):
    self._assets = list(assets)

  @property
  def extra_assets(self):
    """Gets or sets the list of extra files selected by user.

    When set, the input list is duplicated.
    """
    return self._extra_assets

  @extra_assets.setter
  def extra_assets(self, extra_assets):
    self._extra_assets = list(extra_assets)

  @property
  def full_frame_range(self):
    """Gets the frame range as FrameRange object."""
    return FrameRange.from_string_and_step(self.frame_range, self.frame_step)

  @property
  def is_instance_type_preemptible(self):
    """Checks if the instance type is preemptible."""
    return 'PREEMPTIBLE' in self.instance_type

  @property
  def is_standalone(self):
    return self._is_standalone

  @property
  def job_type(self):
    """Gets the job type.

    Used for submission to Zync API.
    """
    return '3dsmax'

  @property
  def original_scene_file(self):
    """Gets and sets the original scene file path."""
    return self._original_scene_file

  @original_scene_file.setter
  def original_scene_file(self, original_scene_file):
    self._original_scene_file = original_scene_file

  @property
  def renderer_type(self):
    """Gets the renderer type."""
    raise AttributeError('Unknown renderer type')

  @property
  def resolution(self):
    """Gets or sets the resolution."""
    return self.x_resolution, self.y_resolution

  @resolution.setter
  def resolution(self, resolution):
    x, y = resolution
    self.x_resolution = x
    self.y_resolution = y

  @property
  def scene_file(self):
    """Gets the scene file.

    This path is meant to be used for submission to Zync API.
    """
    return self.original_scene_file

  @property
  def usage_tag(self):
    """Gets the usage tag."""
    return '3dsmax'

  @property
  def xrefs(self):
    """Gets or sets the list of xrefs."""
    return self._xrefs

  @xrefs.setter
  def xrefs(self, xrefs):
    self._xrefs = list(xrefs)

  @property
  def instance_renderer_type(self):
    """Gets the renderer type used by Zync API to retrieve instance types."""
    raise AttributeError('Unknown renderer type')

  def get_submission_params(self):
    """Gets a dictionary of params for submission to Zync API."""
    self._validate_data()
    params = {
        'camera': self.camera_name,
        'chunk_size': self.chunk_size,
        'distributed': 0,
        'frange': self.frame_range,
        'instance_type': self.instance_type,
        'notify_complete': int(self.notify_complete),
        'num_instances': self.instance_count,
        'output_name': BaseModel._sanitize_path(self.output_name),
        'plugin_version': self.plugin_version,
        'priority': self.priority,
        'proj_name': self.project,
        'renderer': self.renderer_type,
        'scene_info': self._get_scene_info(),
        'step': self.frame_step,
        'sync_extra_assets': self.sync_extra_assets,
        'upload_only': int(self.upload_only),
        'xres': self.x_resolution,
        'yres': self.y_resolution,
    }
    return BaseModel._sanitize_path(self.scene_file), params

  def _validate_data(self):
    self._validate_output_name()
    if not self.scene_file:
      raise ValueError('Scene file name unknown')
    if not self.instance_type:
      raise ValueError('Please select machine type')
    if not self.project:
      raise ValueError('Please specify project name')
    if self.sync_extra_assets and not self.extra_assets:
      raise ValueError('No extra assets selected')

  def _validate_output_name(self):
    if not self.output_name:
      raise ValueError('Please specify output file name')
    if not BaseModel._has_file_extension(self.output_name):
      raise ValueError('Please specify output file name with extension')

  @staticmethod
  def _has_file_extension(filename):
    name, extension = os.path.splitext(filename)
    return len(extension) > 1

  def _get_scene_info(self):
    references = self.assets + self.extra_assets
    scene_info = {
        'max_version': self.max_version,
        'project_path': BaseModel._sanitize_path(self.project_path),
        'references': BaseModel._sanitize_paths(references),
        'xrefs': BaseModel._sanitize_paths(self.xrefs),
    }
    return scene_info

  @staticmethod
  def _sanitize_path(path):
    return path.replace('\\', '/')

  @staticmethod
  def _sanitize_paths(paths):
    return [BaseModel._sanitize_path(path) for path in paths]

  def update_scene_file_path(self):
    """Updates the scene and stand-alone scene file paths.

    The update is necessary to refresh scene file names, because they may depend
    on other fields of the model.
    """
    pass
