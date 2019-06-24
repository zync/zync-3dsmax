"""Contains the presenter component for 3ds Max Zync plugin."""

import functools
import os
import sys
import traceback

from zync_model.base_model import RendererType


def _show_exceptions(decorated):
  """Decorates a methods of Presenter that need to show exceptions in GUI."""

  @functools.wraps(decorated)
  def wrapped(decorated_self, *args, **kwargs):
    """Wraps a method and displays thrown exceptions in GUI.

    Assumes that decorated_self is instance of Presenter.
    """
    try:
      return decorated(decorated_self, *args, **kwargs)
    except Exception as e:
      traceback.print_exc()
      decorated_self.show_error(e.message)

  return wrapped


# TODO(maciek): add tooltips (b/38194603)
class Presenter(object):
  """Presenter component for 3ds Max Zync plugin."""

  def __init__(self, version, default_project_name, max_api, zync_api, model,
               spinner_dialog, submit_dialog, gui_utils, thread_provider):
    """Class constructor.

    Args:
      version: plugin version string
      default_project_name: default name for the Zync project
      max_api: 3ds Max API
      zync_api: Zync API
      model: data model
      gui: provider of GUI elements
    """
    self._gui_utils = gui_utils
    self._max_api = max_api
    self._model = model
    self._version = version
    self._default_project_name = default_project_name
    self._zync_api = zync_api
    self._spinner_dialog = spinner_dialog
    self._submit_dialog = submit_dialog
    self._thread_provider = thread_provider

  def _call_async(self, func, on_success=None, on_failure=None):
    """Makes an asynchronous call in a separate thread.

    Displays error message if an exception is raised.
    Disables submit dialog for the duration of the call.
    """

    def handle_failure(error):
      self.show_error(error.message)
      if on_failure is not None:
        on_failure(error)

    def runner():
      self._submit_dialog.enabled = False
      try:
        return func()
      finally:
        self._submit_dialog.enabled = True

    self._thread_provider(runner, on_success, handle_failure).start()

  def show_error(self, message):
    """Displays error message box."""
    self._gui_utils.show_error_message_box(message)

  @_show_exceptions
  def start(self):
    """Starts the presenter."""
    if self._max_api.is_save_pending:
      raise RuntimeError('Scene needs to be saved before submitting')
    self._initialize_model()
    self._initialize_gui()
    self._submit_dialog.show('Zync Submit (version %s)' % self._version)

  def _initialize_model(self):
    self._model.plugin_version = self._version
    if self._zync_api.is_v2():
      self._model.max_version = self._max_api.pretty_max_version
    else:
      self._model.max_version = self._max_api.max_version
    self._model.assets = self._max_api.assets
    self._model.project_path = self._max_api.project_path
    self._model.xrefs = self._max_api.xrefs
    self._model.instance_count = 1
    self._model.priority = 50
    self._model.project = self._default_project_name
    self._model.frame_range = self._max_api.frame_range
    self._model.frame_step = 1
    self._model.chunk_size = 10
    self._model.upload_only = False
    self._model.notify_complete = False
    self._model.sync_extra_assets = False
    self._model.extra_assets = []
    self._model.resolution = self._max_api.resolution
    self._model.output_name = self._get_output_name()
    self._model.original_scene_file = self._max_api.scene_file_path

  def _get_output_name(self):
    output_name = self._max_api.output_file_name
    if not output_name:
      output_dir = self._max_api.output_dir_name
      if output_dir:
        output_file = self._max_api.scene_file_name.rstrip('.max') or 'unknown'
        output_file += '.exr'
        output_name = os.path.join(output_dir, output_file)
    return output_name

  def _initialize_gui(self):
    self._estimated_cost_label = self._submit_dialog.get_label('estimated_cost')

    self._existing_project_checkbox = self._submit_dialog.get_checkbox(
        'existing_project')
    self._existing_project_checkbox.set_on_checked(
        self._on_existing_project_names_checked)

    self._logout_button = self._submit_dialog.get_button('logout')
    self._logout_button.set_on_clicked(self._on_logout_clicked)

    self._new_project_checkbox = self._submit_dialog.get_checkbox('new_project')
    self._new_project_checkbox.set_on_checked(self._on_new_project_name_checked)

    self._select_files_button = self._submit_dialog.get_button('select_files')
    self._select_files_button.set_on_clicked(self._on_select_files_clicked)
    self._select_files_button.enabled = self._model.sync_extra_assets

    self._submit_button = self._submit_dialog.get_button('submit')
    self._submit_button.set_on_clicked(self._on_submit_clicked)

    self._sync_extra_assets_checkbox = self._submit_dialog.get_checkbox(
        'sync_extra_assets')
    self._sync_extra_assets_checkbox.set_on_checked(
        self._on_sync_extra_assets_checked)

    self._upload_only_checkbox = self._submit_dialog.get_checkbox('upload_only')
    self._upload_only_checkbox.set_on_checked(self._on_upload_only_checked)

    self._camera_names_combo = self._submit_dialog.get_combobox('camera_names')
    self._camera_names_combo.populate(self._max_api.camera_names)

    self._chunk_size_field = self._submit_dialog.get_numerical_field(
        'chunk_size')
    self._chunk_size_field.set_validation(1, sys.maxint)
    self._chunk_size_field.value = self._model.chunk_size

    self._frame_range_field = self._submit_dialog.get_text_field('frame_range')
    self._frame_range_field.text = self._model.frame_range

    self._frame_step_field = self._submit_dialog.get_numerical_field(
        'frame_step')
    self._frame_step_field.set_validation(1, sys.maxint)
    self._frame_step_field.value = self._model.frame_step

    self._output_name_field = self._submit_dialog.get_text_field('output_name')
    self._output_name_field.text = self._model.output_name

    self._priority_field = self._submit_dialog.get_numerical_field('priority')
    self._priority_field.set_validation(1, sys.maxint)
    self._priority_field.value = self._model.priority

    self._renderer_name_label = self._submit_dialog.get_label('renderer_name')
    self._renderer_name_label.text = self._model.pretty_renderer_name

    self._x_resolution_field = self._submit_dialog.get_numerical_field(
        'x_resolution')
    self._x_resolution_field.set_validation(1, sys.maxint)
    self._x_resolution_field.value = self._model.x_resolution

    self._y_resolution_field = self._submit_dialog.get_numerical_field(
        'y_resolution')
    self._y_resolution_field.set_validation(1, sys.maxint)
    self._y_resolution_field.value = self._model.y_resolution

    self._logged_as_label = self._submit_dialog.get_label('logged_as')
    self._logged_as_label.text = self._provide_logged_as_label()

    self._notify_complete_checkbox = self._submit_dialog.get_checkbox(
        'notify_complete')

    self._use_standalone_checkbox = self._submit_dialog.get_checkbox(
        'use_standalone')
    self._use_standalone_checkbox.enabled = False
    self._use_standalone_checkbox.checked = self._model.is_standalone
    if self._model.is_standalone:
      if self._model.renderer_type == RendererType.ARNOLD:
        self._chunk_size_field.enabled = False
        self._chunk_size_field.value = 1

    self._instance_count_field = self._submit_dialog.get_numerical_field(
        'instance_count')
    self._instance_count_field.set_on_changed(self._on_instance_count_changed)
    self._instance_count_field.set_validation(1, sys.maxint)
    self._instance_count_field.value = self._model.instance_count

    self._instance_types_combo = self._submit_dialog.get_combobox(
        'instance_types')
    self._instance_types_combo.set_on_changed(self._on_instance_type_changed)
    self._instance_types_combo.populate(
        self._zync_api.instance_type_labels(
            self._model.instance_renderer_type, self._model.usage_tag))

    self._new_project_name_field = self._submit_dialog.get_text_field(
        'new_project_name')

    self._existing_project_names_combo = self._submit_dialog.get_combobox(
        'existing_project_names')
    self._existing_project_names_combo.populate(
        self._zync_api.get_existing_project_names())
    if self._existing_project_names_combo.contains_element(self._model.project):
      self._set_existing_project_enabled(True)
      self._set_existing_project_checked(True)
      self._existing_project_names_combo.selected_element = self._model.project
    else:
      self._set_existing_project_enabled(False)
      self._set_existing_project_checked(False)
      self._new_project_name_field.text = self._model.project

  def _provide_logged_as_label(self):
    return 'Logged in as: %s' % self._zync_api.logged_as()

  def _on_new_project_name_checked(self, checked):
    self._set_existing_project_enabled(not checked)
    self._set_existing_project_checked(not checked)

  def _on_existing_project_names_checked(self, checked):
    self._set_existing_project_enabled(checked)
    self._set_existing_project_checked(checked)

  def _set_existing_project_enabled(self, enabled):
    self._existing_project_names_combo.enabled = enabled
    self._new_project_name_field.enabled = not enabled

  def _set_existing_project_checked(self, checked):
    self._existing_project_checkbox.checked = checked
    self._new_project_checkbox.checked = not checked

  def _on_instance_count_changed(self, new_instance_count):
    self._model.instance_count = new_instance_count
    self._estimated_cost_label.text = self._provide_estimated_cost_label()

  def _on_instance_type_changed(self, instance_type_label):
    self._model.instance_type_label = instance_type_label
    self._model.instance_type = self._zync_api.instance_type(
        self._model.instance_type_label, self._model.instance_renderer_type)
    self._estimated_cost_label.text = self._provide_estimated_cost_label()

  def _provide_estimated_cost_label(self):
    return 'Est. Cost per Hour: %s' % self._provide_estimated_cost()

  def _provide_estimated_cost(self):
    return self._zync_api.estimated_cost(self._model.instance_type_label,
                                         self._model.instance_renderer_type,
                                         self._model.instance_count)

  def _on_sync_extra_assets_checked(self, sync_extra_assets):
    self._select_files_button.enabled = sync_extra_assets

  def _on_upload_only_checked(self, upload_only):
    self._instance_types_combo.enabled = not upload_only
    self._instance_count_field.enabled = not upload_only
    self._estimated_cost_label.enabled = not upload_only
    self._priority_field.enabled = not upload_only
    self._output_name_field.enabled = not upload_only
    self._frame_range_field.enabled = not upload_only
    self._frame_step_field.enabled = not upload_only
    self._chunk_size_field.enabled = not upload_only
    self._camera_names_combo.enabled = not upload_only
    self._x_resolution_field.enabled = not upload_only
    self._y_resolution_field.enabled = not upload_only

  def _on_select_files_clicked(self):
    project_name = self._get_project_name()
    self._zync_api.show_selected_files_dialog(project_name)

  def _get_project_name(self):
    if self._existing_project_checkbox.checked:
      project_name = self._existing_project_names_combo.selected_element
    else:
      project_name = self._new_project_name_field.text
    return project_name

  def _on_logout_clicked(self):
    self._submit_dialog.close()
    self._spinner_dialog.show('Logging out...')
    self._call_async(self._zync_api.logout, lambda _: self.on_logout_done(None),
                     self.on_logout_done)

  @_show_exceptions
  def on_logout_done(self, e):
    self._spinner_dialog.close()
    if e is None:
      self._gui_utils.show_info_message_box('Logged out')

  @_show_exceptions
  def _on_submit_clicked(self):
    self._sync_model()
    scene_file, params = self._model.get_submission_params()
    if not self._maybe_show_pvm_warning():
      return
    self._maybe_export_standalone()

    self._spinner_dialog.show('Submitting to Zync...')
    self._call_async(
        lambda: self._zync_api.submit_job(scene_file, params, self._model.
                                          job_type), lambda _: self.
        _on_submit_done(None), self._on_submit_done)

  def _on_submit_done(self, error):
    self._spinner_dialog.close()
    if error is None:
      self._gui_utils.show_info_message_box(
          'Job successfully submitted to Zync')

  def _sync_model(self):
    self._model.project = self._get_project_name()
    self._model.sync_extra_assets = self._sync_extra_assets_checkbox.checked
    self._model.instance_type_label = self._instance_types_combo.selected_element
    self._model.instance_count = self._instance_count_field.value
    self._model.priority = self._priority_field.value
    self._model.frame_range = self._frame_range_field.text
    self._model.frame_step = self._frame_step_field.value
    self._model.camera_name = self._camera_names_combo.selected_element
    self._model.x_resolution = self._x_resolution_field.value
    self._model.y_resolution = self._y_resolution_field.value
    self._model.output_name = self._output_name_field.text
    self._model.upload_only = self._upload_only_checkbox.checked
    self._model.notify_complete = self._notify_complete_checkbox.checked
    self._model.chunk_size = self._chunk_size_field.value

    if self._model.sync_extra_assets:
      extra_assets = self._zync_api.get_selected_files(self._model.project)
      if not extra_assets:
        extra_assets = []
      self._model.extra_assets = extra_assets
    else:
      self._model.extra_assets = []

    self._model.update_scene_file_path()
    if self._model.renderer_type == RendererType.ARNOLD:
      self._model.aovs = self._max_api.arnold_aovs

  def _maybe_export_standalone(self):
    if self._model.is_standalone and not self._model.upload_only:
      frame_range = self._model.full_frame_range
      if self._model.renderer_type == RendererType.VRAY:
        self._export_vray_scene(self._model.standalone_scene_file,
                                self._model.resolution, frame_range.start,
                                frame_range.end)
      elif self._model.renderer_type == RendererType.ARNOLD:
        self._export_arnold_scene(self._model.standalone_scene_file,
                                  self._model.resolution, frame_range.start,
                                  frame_range.end)
      else:
        raise ValueError('Stand-alone mode for %s is not supported' %
                         self._model.pretty_renderer_name)

  def _export_vray_scene(self, scene_file, resolution, frame_start, frame_end):
    with self._max_api.undo():
      self._max_api.resolution = resolution
      self._max_api.set_camera_in_active_viewport(self._model.camera_name)
      self._max_api.export_vrscene(scene_file, frame_start, frame_end)

  def _export_arnold_scene(self, scene_file, resolution, frame_start,
                           frame_end):
    with self._max_api.undo():
      self._max_api.output_file_name = self._model.output_name.replace('\\', '/')
      self._max_api.resolution = resolution
      self._max_api.set_camera_in_active_viewport(self._model.camera_name)
      self._max_api.export_ass(scene_file, frame_start, frame_end)

  def _maybe_show_pvm_warning(self):
    if self._model.upload_only or not self._model.is_instance_type_preemptible:
      return True
    return self._zync_api.get_pvm_consent()
