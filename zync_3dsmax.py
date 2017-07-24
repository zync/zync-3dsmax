import functools
import getpass
import inspect
import os
import sys
import traceback

import MaxPlus

try:
  import pysideuic

  from PySide.QtCore import QThread
  from PySide.QtCore import Qt
  from PySide.QtCore import Signal
  from PySide.QtCore import QSize
  from PySide.QtGui import QDialog
  from PySide.QtGui import QIntValidator
  from PySide.QtGui import QMessageBox
  from PySide.QtGui import QMovie
  from PySide.QtGui import QWidget
except:
  import pyside2uic as pysideuic

  from PySide2.QtCore import QThread
  from PySide2.QtCore import Qt
  from PySide2.QtCore import Signal
  from PySide2.QtCore import QSize
  from PySide2.QtGui import QIntValidator
  from PySide2.QtGui import QMovie
  from PySide2.QtWidgets import QDialog
  from PySide2.QtWidgets import QMessageBox
  from PySide2.QtWidgets import QWidget

__version__ = '0.1.11'
SUBMIT_DIALOG_FILE_NAME = 'submit_dialog.ui'
SPINNER_DIALOG_FILE_NAME = 'spinner_dialog.ui'
SPINNER_GIF_FILE_NAME = 'spinner.gif'

zync = None


class BadParamException(Exception):
  pass


class AsyncThread(QThread):
  signal_succeeded = Signal()
  signal_failed = Signal(Exception)

  def __init__(self, func_init):
    super(AsyncThread, self).__init__()
    self._func_init = func_init

  def run(self):
    try:
      self._func_init()
    except Exception as e:
      self.signal_failed.emit(e)
    else:
      self.signal_succeeded.emit()


def show_exceptions(func):
  """Error-showing decorator for all entry points

  Catches all exceptions and shows dialog box with the message.
  """
  @functools.wraps(func)
  def wrapped(*args, **kwargs):
    try:
      return func(*args, **kwargs)
    except Exception as e:
      traceback.print_exc()
      show_error(e.message)

  return wrapped


# Importing zync-python is deferred until user's action (i.e. attempt
# to open plugin window), because we are not able to reliably show message
# windows any time earlier. Zync-python is not needed for plugin to load.
@show_exceptions
def import_zync_python():
  """Imports zync-python"""
  global zync
  if zync:
    return

  if os.environ.get('ZYNC_API_DIR'):
    API_DIR = os.environ.get('ZYNC_API_DIR')
  else:
    config_path = os.path.join(os.path.dirname(__file__), 'config_3dsmax.py')
    if not os.path.exists(config_path):
      raise Exception(
        "Plugin configuration incomplete: zync-python path not provided.\n\n"
        "Re-installing the plugin may solve the problem.")
    import imp
    config_3dsmax = imp.load_source('config_3dsmax', config_path)
    API_DIR = config_3dsmax.API_DIR
    if not isinstance(API_DIR, basestring):
      raise Exception("API_DIR defined in config_3dsmax.py is not a string")

  sys.path.append(API_DIR)
  import zync
  import file_select_dialog


def show_info(message):
  QMessageBox.information(None, "", message)


def show_error(message):
  QMessageBox.critical(None, "Error", message)


# TODO(maciek): add tooltips (b/38194603)
class SubmitWindowController(object):
  spinner_dialog = None
  submit_dialog = None

  def __init__(self):
    import_zync_python()

    renderer_name = MaxPlus.RenderSettings.GetProduction().GetClassName()
    if 'arnold' in renderer_name.lower():
      self._renderer = 'arnold'
    elif 'v-ray' in renderer_name.lower():
      self._renderer = 'vray'
    elif renderer_name.lower() == 'scanline renderer':
      self._renderer = 'scanline'
    else:
      raise Exception('Unknown renderer: %s' % renderer_name)
    num_xrefs = MaxPlus.Core.EvalMAXScript('pathConfig.xrefPaths.count()').Get()
    self._xrefs = []
    for i in range(num_xrefs):
      xref = MaxPlus.Core.EvalMAXScript('pathConfig.xrefPaths.get %d' % (i + 1)).Get()
      self._xrefs.append(xref.replace('\\', '/'))
    self._num_instances = 1
    self._instance_type_label = ""
    self._priority = 50
    self._project = getpass.getuser()
    self._frange = '1'
    self._frame_step = 1
    self._chunk_size = 10
    self._upload_only = 0
    self._notify_complete = 0
    self._sync_extra_assets = False
    self._extra_assets = []
    self._x_res = 1920
    self._y_res = 1080
    self._output_name = MaxPlus.RenderSettings.GetOutputFile()
    if not self._output_name:
      output_dir = MaxPlus.PathManager.GetRenderOutputDir()
      if output_dir:
        output_file = MaxPlus.FileManager.GetFileName().rstrip('.max') or "unknown"
        output_file += '.exr'
        self._output_name = os.path.join(output_dir, output_file)


    self._loadSpinnerDialog()
    self._loadSubmitDialog()

  def login(self):
    """Connects to Zync service and upon successful connection pops up the dialog.
    """
    SubmitWindowController.spinner_dialog.setWindowTitle("Logging into Zync...")
    SubmitWindowController.spinner_dialog.show()

    def func_init():
      self._zync_conn = zync.Zync(application='3dsmax')

    self._init_thread = AsyncThread(lambda: func_init())
    self._init_thread.signal_succeeded.connect(lambda: self._on_init_done(None))
    self._init_thread.signal_failed.connect(lambda e: self._on_init_done(e))
    self._init_thread.start()

  def _loadSpinnerDialog(self):
    ui_file_name = os.path.join(SubmitWindowController._get_self_dir(), SPINNER_DIALOG_FILE_NAME)
    SpinnerDialogType, BaseType = MaxPlus.LoadUiType(ui_file_name)

    class SpinnerDialog(SpinnerDialogType, BaseType):
      def __init__(self, parent=None):
        SpinnerDialogType.__init__(self, parent)
        BaseType.__init__(self, parent)
        self.setupUi(self)
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint | Qt.WindowTitleHint)

        spinner_filename = os.path.join(SubmitWindowController._get_self_dir(),
                                        SPINNER_GIF_FILE_NAME)
        self.spinner_movie = QMovie(spinner_filename)
        self.spinner_movie.setScaledSize(QSize(40, 40))
        self.spinner_label.setMovie(self.spinner_movie)

      def show(self):
        super(SpinnerDialog, self).show()
        self.spinner_movie.start()

    SubmitWindowController.spinner_dialog = SpinnerDialog(None)

  def _loadSubmitDialog(self):
    ui_file_name = os.path.join(SubmitWindowController._get_self_dir(), SUBMIT_DIALOG_FILE_NAME)
    SubmitDialogType, BaseType = MaxPlus.LoadUiType(ui_file_name)

    class SubmitDialog(SubmitDialogType, BaseType):
      def __init__(self, parent=None):
        SubmitDialogType.__init__(self, parent)
        BaseType.__init__(self, parent)
        self.setupUi(self)

    SubmitWindowController.submit_dialog = SubmitDialog(None)
    SubmitWindowController.submit_dialog.setWindowTitle('Zync Submit (version %s)' % __version__)

  def _init_controls(self):
    self._init_num_instances()
    self._init_instance_types()
    self._init_projects()
    self._init_cameras()
    self._init_frange()
    self._init_xy_res()
    self._init_estimated_cost()
    self._init_extra_assets()
    self._init_paths()
    self._init_logged_as()

    SubmitWindowController.submit_dialog.submit_button.clicked.connect(
        lambda: self._on_submit_job())
    SubmitWindowController.submit_dialog.logout_button.clicked.connect(
        lambda: self._on_logout())
    SubmitWindowController.submit_dialog.upload_only.clicked.connect(
        lambda: self._on_upload_only())

  def _init_num_instances(self):
    SubmitWindowController.submit_dialog.num_instances.setValidator(QIntValidator(1, 100))
    SubmitWindowController.submit_dialog.num_instances.setText(str(self._num_instances))
    SubmitWindowController.submit_dialog.num_instances.textChanged.connect(
        lambda: self._on_change_num_instances())

  def _init_instance_types(self):
    SubmitWindowController.submit_dialog.instance_type.clear()
    for instance_label in self._zync_conn.get_machine_type_labels(self._get_max_renderer()):
      SubmitWindowController.submit_dialog.instance_type.addItem(instance_label)
    SubmitWindowController.submit_dialog.instance_type.setCurrentIndex(-1)
    SubmitWindowController.submit_dialog.instance_type.currentIndexChanged.connect(
        lambda: self._on_change_instance_type())

  def _init_frame_specs(self):
    SubmitWindowController.submit_dialog.frame_step.setValidator(QIntValidator(1, sys.maxint))
    SubmitWindowController.submit_dialog.chunk_size.setValidator(QIntValidator(1, sys.maxint))

  def _init_projects(self):
    SubmitWindowController.submit_dialog.new_project.setChecked(True)
    SubmitWindowController.submit_dialog.existing_project_name.setEnabled(False)
    SubmitWindowController.submit_dialog.new_project_name.setEnabled(True)
    for counter, project in enumerate(self._zync_conn.get_project_list()):
      SubmitWindowController.submit_dialog.existing_project_name.addItem(project['name'])
      if self._project == project['name']:
        SubmitWindowController.submit_dialog.existing_project.setChecked(True)
        SubmitWindowController.submit_dialog.existing_project_name.setEnabled(True)
        SubmitWindowController.submit_dialog.new_project_name.setEnabled(False)
        SubmitWindowController.submit_dialog.existing_project_name.setCurrentIndex(counter)
    SubmitWindowController.submit_dialog.existing_project.clicked.connect(
        lambda: self._on_select_project_type())
    SubmitWindowController.submit_dialog.new_project.clicked.connect(
        lambda: self._on_select_project_type())

  def _init_extra_assets(self):
    SubmitWindowController.submit_dialog.sync_extra_assets.setCheckState(
        Qt.CheckState.Checked if self._sync_extra_assets else Qt.CheckState.Unchecked)
    SubmitWindowController.submit_dialog.sync_extra_assets.clicked.connect(
        lambda: self._on_sync_extra_assets())
    SubmitWindowController.submit_dialog.select_files.clicked.connect(
        lambda: self._on_select_files())

  def _init_paths(self):
    SubmitWindowController.submit_dialog.output_name.setText(self._output_name)

  def _init_cameras(self):
    cameras = []
    self._get_cameras(MaxPlus.Core.GetRootNode(), cameras)
    for camera in cameras:
      SubmitWindowController.submit_dialog.camera.addItem(camera)

  def _init_frange(self):
    ticks_per_frame = MaxPlus.Animation.GetTicksPerFrame()
    interval = MaxPlus.Animation.GetAnimRange()
    first_frame = int(interval.Start() / ticks_per_frame)
    last_frame = int(interval.End() / ticks_per_frame)
    if first_frame == last_frame:
      self._frange = str(first_frame)
    else:
      self._frange = "%d-%d" % (first_frame, last_frame)

    SubmitWindowController.submit_dialog.frange.setText(self._frange)
    SubmitWindowController.submit_dialog.chunk_size.setText(str(self._chunk_size))

  def _init_xy_res(self):
    validator = QIntValidator(1, 1000000)
    SubmitWindowController.submit_dialog.x_res.setValidator(validator);
    SubmitWindowController.submit_dialog.x_res.setText("1920")
    SubmitWindowController.submit_dialog.y_res.setValidator(validator);
    SubmitWindowController.submit_dialog.y_res.setText("1080")

  def _init_estimated_cost(self):
    if not self._instance_type_label:
      estimated_cost = 'unknown'
    else:
      renderer = "%s-3dsmax" % self._renderer
      machine_type = self._zync_conn.machine_type_from_label(self._instance_type_label,
                                                             self._get_max_renderer())
      machine_type_price = self._zync_conn.get_machine_type_price(machine_type, renderer)
      if machine_type_price:
        estimated_cost = "$ %.2f" % (machine_type_price * self._num_instances)
      else:
        estimated_cost = 'unknown'
    text = 'Est. Cost per Hour: %s' % estimated_cost
    SubmitWindowController.submit_dialog.est_cost.setText(text)
    renderers = {
      'arnold': 'Arnold',
      'vray': 'V-Ray',
      'scanline': 'Scanline Renderer',
    }
    SubmitWindowController.submit_dialog.renderer.setText(renderers[self._renderer])

  def _init_logged_as(self):
    SubmitWindowController.submit_dialog.logged_as.setText(
        "Logged in as %s" % self._zync_conn.email)

  @show_exceptions
  def _on_init_done(self, e):
    SubmitWindowController.spinner_dialog.close()
    self._init_thread = None

    if e:
      raise e
    else:
      self._init_controls()

      SubmitWindowController.submit_dialog.setParent(None)
      MaxPlus.AttachQWidgetToMax(SubmitWindowController.submit_dialog, False)
      SubmitWindowController.submit_dialog.show()
      SubmitWindowController.submit_dialog.setModal(True)


  def _on_change_num_instances(self):
    try:
      self._num_instances = int(SubmitWindowController.submit_dialog.num_instances.text())
    except:
      return
    self._init_estimated_cost()

  def _on_change_instance_type(self):
    self._instance_type_label = SubmitWindowController.submit_dialog.instance_type.currentText()
    self._init_estimated_cost()

  def _on_select_project_type(self):
    existing_project = SubmitWindowController.submit_dialog.existing_project.isChecked()
    SubmitWindowController.submit_dialog.existing_project_name.setEnabled(existing_project)
    SubmitWindowController.submit_dialog.new_project_name.setEnabled(not existing_project)

  def _on_sync_extra_assets(self):
    self._sync_extra_assets = SubmitWindowController.submit_dialog.sync_extra_assets.isChecked()
    SubmitWindowController.submit_dialog.select_files.setEnabled(self._sync_extra_assets)

  def _on_upload_only(self):
    self._upload_only = SubmitWindowController.submit_dialog.upload_only.isChecked()
    SubmitWindowController.submit_dialog.instance_type.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.num_instances.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.instance_type.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.est_cost.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.priority.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.output_name.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.frange.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.frame_step.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.chunk_size.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.camera.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.x_res.setEnabled(not self._upload_only)
    SubmitWindowController.submit_dialog.y_res.setEnabled(not self._upload_only)

  def _on_select_files(self):
    if SubmitWindowController.submit_dialog.existing_project.isChecked():
      project_name = SubmitWindowController.submit_dialog.existing_project_name.currentText()
    else:
      project_name = SubmitWindowController.submit_dialog.new_project_name.text()
    self.file_select_dialog = file_select_dialog.FileSelectDialog(project_name)
    self.file_select_dialog.show()

  @show_exceptions
  def _on_submit_job(self):
    self._update_data()
    self._check_data()

    scene_file = MaxPlus.FileManager.GetFileNameAndPath().replace('\\', '/')
    if not scene_file:
      raise BadParamException("Scene file name unknown")
    params = self._create_render_params()
    self._zync_conn.submit_job("3dsmax", scene_file, params=params)

    show_info("Job successfully submitted to Zync")

  def _on_logout(self):
    SubmitWindowController.submit_dialog.close()

    SubmitWindowController.spinner_dialog.setWindowTitle("Logging out...")
    SubmitWindowController.spinner_dialog.show()

    def func_logout():
      self._zync_conn.logout()

    @show_exceptions
    def on_logout_done(e):
      SubmitWindowController.spinner_dialog.close()
      self._logout_thread = None

      if e:
        raise e
      else:
        show_info("Logged out")

    self._logout_thread = AsyncThread(lambda: func_logout())
    self._logout_thread.signal_succeeded.connect(lambda: on_logout_done(None))
    self._logout_thread.signal_failed.connect(lambda e: on_logout_done(e))
    self._logout_thread.start()

  def _update_data(self):
    self._instance_type_label = SubmitWindowController.submit_dialog.instance_type.currentText()
    self._num_instances = int(SubmitWindowController.submit_dialog.num_instances.text())
    self._priority = int(SubmitWindowController.submit_dialog.priority.text())
    if SubmitWindowController.submit_dialog.existing_project.isChecked():
      self._project = SubmitWindowController.submit_dialog.existing_project_name.currentText()
    else:
      self._project = SubmitWindowController.submit_dialog.new_project_name.text()
    self._frange = SubmitWindowController.submit_dialog.frange.text()
    self._step = int(SubmitWindowController.submit_dialog.frame_step.text())
    self._camera = SubmitWindowController.submit_dialog.camera.currentText()
    self._x_res = int(SubmitWindowController.submit_dialog.x_res.text())
    self._y_res = int(SubmitWindowController.submit_dialog.y_res.text())
    self._output_name = SubmitWindowController.submit_dialog.output_name.text()
    self._upload_only = int(SubmitWindowController.submit_dialog.upload_only.isChecked())
    self._notify_complete = int(SubmitWindowController.submit_dialog.notify_complete.isChecked())
    self._sync_extra_assets = SubmitWindowController.submit_dialog.sync_extra_assets.isChecked()
    self._chunk_size = int(SubmitWindowController.submit_dialog.chunk_size.text())
    self._upload_only = SubmitWindowController.submit_dialog.upload_only.isChecked()
    if self._sync_extra_assets:
      self._extra_assets = file_select_dialog.FileSelectDialog.get_extra_assets(self._project)
    else:
      self._extra_assets = []

  def _check_data(self):
    if not self._upload_only:
      if not self._instance_type_label:
        raise BadParamException("Please select machine type")
      if not self._output_name:
        raise BadParamException("Please specify output file name")
    if not self._project:
      raise BadParamException("Please specify project name")
    if self._sync_extra_assets and not self._extra_assets:
      raise BadParamException('No extra assets selected')

  def _create_render_params(self):
    params = dict()

    params['proj_name'] = self._project
    params['instance_type'] = self._zync_conn.machine_type_from_label(self._instance_type_label,
                                                                      self._get_max_renderer())
    params['num_instances'] = self._num_instances
    params['distributed'] = 0
    params['frange'] = self._frange
    params['camera'] = self._camera
    params['xres'] = self._x_res
    params['yres'] = self._y_res
    params['step'] = self._step
    params['priority'] = self._priority
    params['renderer'] = self._renderer
    params['chunk_size'] = self._chunk_size
    params['scene_info'] = self._create_scene_info()
    params['plugin_version'] = __version__
    params['output_name'] = self._output_name.replace('\\', '/')
    params['upload_only'] = int(self._upload_only)
    params['notify_complete'] = self._notify_complete
    params['sync_extra_assets'] = self._sync_extra_assets

    return params

  def _create_scene_info(self):
    scene_info = {}

    references = []
    for asset in list(MaxPlus.AssetManager.GetAssets()) + self._extra_assets:
      file_name = asset.GetResolvedFileName().replace('\\', '/')
      references.append(file_name)
    scene_info['references'] = references
    scene_info['xrefs'] = self._xrefs

    return scene_info

  def _get_cameras(self, node, cameras):
    node_object = node.Object
    if node_object and node_object.GetSuperClassID() == MaxPlus.SuperClassIds.Camera:
      cameras.append(node.Name)
    for child_node in node.Children:
      self._get_cameras(child_node, cameras)

  def _get_max_renderer(self):
    return "%s-3dsmax" % self._renderer

  @staticmethod
  def _get_self_dir():
    filename = os.path.realpath(inspect.getfile(sys._getframe(0)))
    return os.path.dirname(filename)


def main():
  if not MaxPlus.FileManager_CheckForSave():
    return
  submit_window_controller = SubmitWindowController()
  submit_window_controller.login()


if __name__ == '__main__':
  main()
