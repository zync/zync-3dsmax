"""Contains the adapter to 3ds Max API."""

import re

import MaxPlus


class MaxApiFacade(object):
  """Adapter to 3ds Max API."""

  @property
  def assets(self):
    """Gets the assets used in the current scene."""
    assets = []
    for asset in list(MaxPlus.AssetManager.GetAssets()):
      file_name = asset.GetResolvedFileName().replace('\\', '/')
      assets.append(file_name)
    return assets

  def attach_qt_widget_to_max(self, widget):
    """Attaches Qt widget to Max GUI."""
    MaxPlus.AttachQWidgetToMax(widget, False)

  @property
  def camera_names(self):
    """Gets the cameras used in the current scene."""
    camera_names = []
    MaxApiFacade._collect_camera_names_recursively(MaxPlus.Core.GetRootNode(),
                                                   camera_names)
    return camera_names

  @staticmethod
  def _collect_camera_names_recursively(node, camera_names):
    if MaxApiFacade._is_camera_node(node):
      camera_names.append(node.Name)
    for child_node in node.Children:
      MaxApiFacade._collect_camera_names_recursively(child_node, camera_names)

  @staticmethod
  def _is_camera_node(node):
    node_object = node.Object
    if node_object:
      return node_object.GetSuperClassID() == MaxPlus.SuperClassIds.Camera
    return False

  def export_ass(self, file_name, start_frame, end_frame):
    """Exports the frames to Arnold scene file using given file name."""
    export_commands = [
        # Render Setup window must be closed, otherwise setting rendTimeType and
        # rendPickupFrames might not stick, according to Autodesk
        # https://help.autodesk.com/view/3DSMAX/2017/ENU/?guid=__files_GUID_30AF1E53_5A69_402D_84D6_4D6ECCDD6D20_htm
        'renderSceneDialog.close()',
        # rendTimeType 4 is equivalent to "Frames" in
        # "Render Setup -> Common -> TimeOutput" and it expects the frame range
        # to be specified via rendPickupFrames
        'rendTimeType=4',
        'rendPickupFrames="%s-%s"' % (start_frame, end_frame),
        'rendNThFrame=1',
        'renderers.current.export_to_ass = true',
        'renderers.current.ass_file_path = "%s"' % file_name,
        'render fromFrame:%s toFrame:%s vfb:false' % (start_frame, end_frame)
    ]
    MaxApiFacade._run_commands_raise_errors(export_commands)

  def export_vrscene(self, file_name, start_frame, end_frame):
    """Exports the frames to V-Ray scene file using given file name."""
    export_commands = [
        'oldSaveRequired = getSaveRequired()',
        'renderers.activeShade = VRayRT()',
        MaxApiFacade._vray_export_command(file_name, start_frame, end_frame),
        'setSaveRequired oldSaveRequired'
    ]
    MaxApiFacade._run_commands_raise_errors(export_commands)

  @staticmethod
  def _run_commands_raise_errors(commands):
    command = ';'.join(commands)
    maybe_error = MaxPlus.FPValue()
    if not MaxPlus.Core.EvalMAXScript(command, maybe_error):
      raise RuntimeError(str(maybe_error))

  @staticmethod
  def _vray_export_command(file_name, start_frame, end_frame):
    # According to Chaos Group, endFrame parameter of vrayExportRTScene
    # is non-inclusive
    return 'vrayExportRTScene "%s" startFrame:%s endFrame:%s' % (
        file_name, start_frame, end_frame + 1)

  @property
  def frame_range(self):
    """Gets the frame range of the current scene."""
    ticks_per_frame = MaxPlus.Animation.GetTicksPerFrame()
    interval = MaxPlus.Animation.GetAnimRange()
    first_frame = int(interval.Start() / ticks_per_frame)
    last_frame = int(interval.End() / ticks_per_frame)
    if first_frame == last_frame:
      frame_range = str(first_frame)
    else:
      frame_range = '%s-%s' % (first_frame, last_frame)
    return frame_range

  @property
  def is_renderer_vray_rt_engine(self):
    """Checks if renderer is V-Ray and uses RT engine."""
    renderer_name = self.renderer_name.lower()
    return 'v-ray' in renderer_name and 'rt' in renderer_name

  @property
  def is_save_pending(self):
    """Checks if the current scene has unsaved changes.

    Prompts the user to save the scene if there are unsaved changes.
    """
    MaxPlus.FileManager.CheckForSave()
    return MaxPlus.Core.EvalMAXScript('getSaveRequired()').Get()

  def load_ui_type(self, ui_file_name):
    """Returns Qt base classes used for plugin GUI construction."""
    return MaxPlus.LoadUiType(ui_file_name)

  _max_version_regex = re.compile(r'(?P<major>\d+),(?P<minor>\d+),.*')

  _max_file_version_to_user_version = {'19': '2017', '20': '2018', '21': '2019'}

  @property
  def max_version(self):
    """Returns the version of 3ds Max."""
    return MaxPlus.Core.EvalMAXScript(
        'getFileVersion("$max/3dsmax.exe")').Get().split()[0]

  @property
  def pretty_max_version(self):
    """Returns the user-friendly version of 3ds Max."""
    max_version = self.max_version
    match = MaxApiFacade._max_version_regex.match(max_version)
    if match is not None and match.group('major') is not None and match.group(
        'minor') is not None:
      major = match.group('major')
      if major in MaxApiFacade._max_file_version_to_user_version:
        major = MaxApiFacade._max_file_version_to_user_version[major]
      else:
        raise AttributeError('Unsupported Max version')
      minor = match.group('minor')
      return '%s.%s' % (major, minor)
    raise AttributeError('Unable to retrieve Max version')

  @property
  def maxtoa_version(self):
    plugins_dlls = MaxApiFacade._get_plugin_dlls()
    for plugin_dll in plugins_dlls:
      if plugin_dll.GetDescription() == 'Arnold':
        version = MaxPlus.Core.EvalMAXScript(
            'getFileVersion "%s"' % plugin_dll.GetFilePath()).Get()
        return MaxApiFacade._parse_maxtoa_version(version)
    raise AttributeError('Unknown Arnold version')

  @staticmethod
  def _get_plugin_dlls():
    return [
        MaxPlus.PluginManager.GetPluginDll(plugin_id)
        for plugin_id in range(0, MaxPlus.PluginManager.GetNumPluginDlls())
    ]

  _maxtoa_version_regex = re.compile(r'(?P<version>\d+,\d+,\d+),.*')

  @staticmethod
  def _parse_maxtoa_version(version):
    match = MaxApiFacade._maxtoa_version_regex.match(version)
    if match is not None and match.group('version') is not None:
      version = match.group('version')
      return version.replace(',', '.')
    raise AttributeError("Can't parse Arnold version string %s" % version)

  @property
  def output_dir_name(self):
    """Returns the current render output dir."""
    return MaxPlus.PathManager.GetRenderOutputDir()

  @property
  def output_file_name(self):
    """Returns the current render output file name."""
    return MaxPlus.RenderSettings.GetOutputFile()

  @property
  def project_path(self):
    """Returns the current project path."""
    return MaxPlus.Core.EvalMAXScript(
        'pathConfig.getCurrentProjectFolder()').Get()

  @property
  def renderer_name(self):
    """Returns the name of the current renderer."""
    return MaxPlus.RenderSettings.GetProduction().GetClassName()

  @property
  def resolution(self):
    """Gets or sets the current render output resolution."""
    return MaxPlus.RenderSettings.GetWidth(), MaxPlus.RenderSettings.GetHeight()

  @resolution.setter
  def resolution(self, resolution):
    width, height = resolution
    MaxPlus.RenderSettings.SetWidth(width)
    MaxPlus.RenderSettings.SetHeight(height)

  @property
  def scene_file_name(self):
    """Returns the name of the current scene file."""
    return MaxPlus.FileManager.GetFileName()

  @property
  def scene_file_path(self):
    """Returns the path to the current scene file."""
    return MaxPlus.FileManager.GetFileNameAndPath().replace('\\', '/')

  def set_camera_in_active_viewport(self, camera_name):
    """Attaches the camera with a given name to the active viewport."""
    current_viewport = MaxPlus.ViewportManager.GetActiveViewport()
    export_camera = MaxApiFacade._find_camera_by_name(camera_name)
    current_viewport.SetViewCamera(export_camera)

  @staticmethod
  def _find_camera_by_name(name):

    def find(node):
      if MaxApiFacade._is_camera_node(node) and node.Name == name:
        return node
      for child_node in node.Children:
        maybe_camera = find(child_node)
        if maybe_camera is not None:
          return maybe_camera
      return None

    return find(MaxPlus.Core.GetRootNode())

  def undo(self):
    """Creates a context manager which undoes any changes to the scene."""

    class UndoContextManager(object):

      def __enter__(self):
        MaxPlus.Core.EvalMAXScript('theHold.Begin()')

      def __exit__(self, _exc1, _exc2, _exc3):
        MaxPlus.Core.EvalMAXScript('theHold.Cancel()')

    return UndoContextManager()

  @property
  def vray_rt_engine(self):
    """Returns the type of renderer engine."""
    return MaxPlus.Core.EvalMAXScript('renderers.current.engine_type').Get()

  @property
  def vray_version(self):
    """Returns the version of V-Ray renderer."""
    version = MaxPlus.Core.EvalMAXScript('vrayVersion()').Get()
    version = version[0].split('.')
    return '.'.join(version[0:3])

  @property
  def xrefs(self):
    """Returns the list of references."""
    count = MaxPlus.Core.EvalMAXScript('pathConfig.xrefPaths.count()').Get()
    xrefs = []
    for i in range(count):
      xrefs.append(
          MaxPlus.Core.EvalMAXScript(
              'pathConfig.xrefPaths.get %d' % (i + 1)).Get())
    return xrefs
