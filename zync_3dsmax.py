"""Entry point to Zync plugin for 3ds Max."""

import contextlib
import getpass
import inspect
import os
import sys

# importing additional modules requires adding directory
# containing this plugin file to python path
import traceback

sys.path.append(os.path.dirname(__file__))
from zync_3dsmax_facade import MaxApiFacade
from zync_model.arnold_model import ArnoldModel
from zync_model.scanline_model import ScanlineModel
from zync_model.vray_model import VrayModel
from zync_presenter import Presenter
from zync_qt import QtDialogAdapter
from zync_qt import QtGuiUtils
from zync_qt import create_movie_widget
from zync_facade import ZyncApiFacade

__version__ = '0.3.1'

SUBMIT_DIALOG_FILE_NAME = 'submit_dialog.ui'
SPINNER_DIALOG_FILE_NAME = 'spinner_dialog.ui'
SPINNER_GIF_FILE_NAME = 'spinner.gif'


@contextlib.contextmanager
def _zync_module_path():
  """Returns context manager adding dependencies to Python search path."""

  _old_sys_path = sys.path
  try:
    plugin_dir = os.path.dirname(__file__)
    if os.environ.get('ZYNC_API_DIR'):
      api_dir = os.environ.get('ZYNC_API_DIR')
    else:
      config_path = os.path.join(plugin_dir, 'config_3dsmax.py')
      if not os.path.exists(config_path):
        raise Exception(
            'Plugin configuration incomplete: zync-python path not provided.\n\n'
            'Re-installing the plugin may solve the problem.')
      import imp
      config_3dsmax = imp.load_source('config_3dsmax', config_path)
      api_dir = config_3dsmax.API_DIR
      if not isinstance(api_dir, basestring):
        raise Exception('API_DIR defined in config_3dsmax.py is not a string')
    sys.path.append(api_dir)
    yield
  finally:
    sys.path = _old_sys_path


def _get_resource_path(resource_name):
  """Returns the path to the resource file."""
  return os.path.join(_get_module_directory(), 'resources', resource_name)


def _get_module_directory():
  """Returns the path to the directory containing this module."""
  filename = os.path.realpath(inspect.getfile(sys._getframe(0)))
  return os.path.dirname(filename)


def _create_model(max_api, generate_file_path, is_v2):
  actual_renderer_name = max_api.renderer_name

  if ArnoldModel.is_compatible_with_renderer(actual_renderer_name):
    return ArnoldModel(
        max_api.maxtoa_version, generate_file_path, standalone=is_v2)

  if ScanlineModel.is_compatible_with_renderer(actual_renderer_name):
    if is_v2:
      raise ValueError('Scanline renderer is not supported')
    return ScanlineModel()

  if VrayModel.is_compatible_with_renderer(actual_renderer_name):
    rt_engine_type = None
    # GPU for 3ds Max V-Ray is not yet supported in V2
    if max_api.is_renderer_vray_rt_engine and not is_v2:
      rt_engine_type = max_api.vray_rt_engine
    return VrayModel(
        max_api.vray_version,
        rt_engine_type,
        generate_file_path,
        standalone=is_v2)

  raise ValueError('Unknown renderer: %s' % actual_renderer_name)


def _get_user_name():
  return getpass.getuser()


def _create_submit_dialog(max_api):
  submit_dialog_type, submit_base_type = max_api.load_ui_type(
      _get_resource_path(SUBMIT_DIALOG_FILE_NAME))

  class SubmitDialog(submit_dialog_type, submit_base_type):

    def __init__(self, parent=None):
      submit_dialog_type.__init__(self, parent)
      submit_base_type.__init__(self, parent)
      self.setupUi(self)
      self.setModal(True)

  submit_qt_dialog = SubmitDialog()
  max_api.attach_qt_widget_to_max(submit_qt_dialog)
  return QtDialogAdapter(submit_qt_dialog)


def _create_spinner_dialog(max_api):
  spinner_dialog_type, spinner_base_type = max_api.load_ui_type(
      _get_resource_path(SPINNER_DIALOG_FILE_NAME))

  class SpinnerDialog(spinner_dialog_type, spinner_base_type):

    def __init__(self, parent=None):
      spinner_dialog_type.__init__(self, parent)
      spinner_base_type.__init__(self, parent)
      self.setupUi(self)
      self.spinner_movie = create_movie_widget(
          _get_resource_path(SPINNER_GIF_FILE_NAME), 40, 40)
      self.spinner_label.setMovie(self.spinner_movie)

    def show(self):
      super(SpinnerDialog, self).show()
      self.spinner_movie.start()

  return QtDialogAdapter(SpinnerDialog())


def main():
  spinner_dialog = None
  try:
    with _zync_module_path():
      import zync
      import file_select_dialog
      import settings
      import pvm_consent_dialog

    max_api = MaxApiFacade()
    consent_dialog = pvm_consent_dialog.PvmConsentDialog()
    spinner_dialog = _create_spinner_dialog(max_api)
    spinner_dialog.show('Logging into Zync...')

    def initialize():
      zync_api = zync.Zync(application='3dsmax')
      zync_adapter = ZyncApiFacade(zync_api, file_select_dialog, settings,
                                   consent_dialog)
      model = _create_model(max_api, zync_adapter.generate_file_path,
                            zync_adapter.is_v2())
      return zync_adapter, model

    def on_success((zync_api, model)):
      # keep reference to presenter to prevent garbage collection
      global presenter
      presenter = Presenter(
          default_project_name=_get_user_name(),
          version=__version__,
          zync_api=zync_api,
          max_api=max_api,
          model=model,
          spinner_dialog=spinner_dialog,
          submit_dialog=_create_submit_dialog(max_api),
          gui_utils=QtGuiUtils,
          thread_provider=QtGuiUtils.new_thread)
      spinner_dialog.close()
      presenter.start()

    def on_failure(error):
      spinner_dialog.close()
      QtGuiUtils.show_error_message_box(error.message)

    QtGuiUtils.new_thread(initialize, on_success, on_failure).start()

  except Exception as e:
    traceback.print_exc()
    QtGuiUtils.show_error_message_box('Fatal error: %s' % e.message)
    if spinner_dialog is not None:
      spinner_dialog.close()


if __name__ == '__main__':
  main()
