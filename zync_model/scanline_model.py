"""Contains Scanline-specific data model for 3ds Max Zync plugin."""

from base_model import BaseModel
from base_model import RendererType


class ScanlineModel(BaseModel):
  """Scanline-specific data model for 3ds Max Zync plugin."""

  def __init__(self):
    super(ScanlineModel, self).__init__(standalone=False)

  @staticmethod
  def is_compatible_with_renderer(actual_renderer_name):
    """Checks if ScanlineModel can be used for a given renderer."""
    return 'scanline renderer' == actual_renderer_name.lower()

  @property
  def pretty_renderer_name(self):
    """Gets the pretty renderer name."""
    return 'Scanline Renderer'

  @property
  def renderer_type(self):
    """Gets the renderer type."""
    return RendererType.SCANLINE

  @property
  def instance_renderer_type(self):
    """Gets the renderer type used by Zync API to retrieve instance types."""
    return 'scanline'
