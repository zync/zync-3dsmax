"""Contains the Zync API facade."""


class ZyncApiFacade(object):
  """Zync API facade.

  Implements various operations that require access to Zync API.
  """

  SUPPORTED_STANDALONE_RENDERERS_V2 = ['arnold', 'vray']

  def __init__(self, zync, file_select_dialog_module, settings_module,
               consent_dialog):
    self._consent_dialog = consent_dialog
    self._file_select_dialog = None
    self._file_select_dialog_module = file_select_dialog_module
    self._settings = settings_module
    self._zync = zync

  def estimated_cost(self, instance_type_label, renderer_name, instance_count):
    """Returns a string with estimated rendering cost per hour."""
    if not instance_type_label:
      estimated_cost = 'unknown'
    else:
      renderer_name = ZyncApiFacade._full_renderer_name(renderer_name)
      machine_type = self._zync.machine_type_from_label(instance_type_label,
                                                        renderer_name)
      machine_type_price = self._zync.get_machine_type_price(
          machine_type, renderer_name)
      if machine_type_price:
        estimated_cost = '$ %.2f' % (machine_type_price * instance_count)
      else:
        estimated_cost = 'unknown'
    return estimated_cost

  @staticmethod
  def _full_renderer_name(renderer_name):
    return '%s-3dsmax' % renderer_name

  def logged_as(self):
    """Returns a string identifying logged user."""
    return self._zync.email

  def get_existing_project_names(self):
    """Returns a list of existing project names."""
    return [project['name'] for project in self._zync.get_project_list()]

  def generate_file_path(self, file_name):
    """Generates temporary path prefix with a file name."""
    return self._zync.generate_file_path(file_name).replace('\\', '/')

  def get_pvm_consent(self):
    """Prompts for PVM consent if not already consented."""
    return self._settings.Settings.get().get_pvm_ack(
    ) or self._consent_dialog.prompt()

  def get_selected_files(self, project_name):
    """Returns a list of extra files selected for a given project name."""
    return self._file_select_dialog_module.FileSelectDialog.get_extra_assets(
        project_name)

  def instance_type(self, instance_type_label, renderer_name):
    """Returns the instance type code for a label and renderer name."""
    renderer_name = self._full_renderer_name(renderer_name)
    return self._zync.machine_type_from_label(instance_type_label,
                                              renderer_name)

  def instance_type_labels(self, renderer_name, usage_tag):
    """Returns instance type labels matching the renderer and usage type."""
    renderer_name = self._full_renderer_name(renderer_name)
    self._zync.refresh_instance_types_cache(
        renderer=renderer_name, usage_tag=usage_tag)
    instance_type_labels = []
    for instanceTypeLabel in self._zync.get_machine_type_labels(renderer_name):
      instance_type_labels.append(instanceTypeLabel)
    return instance_type_labels

  def is_renderer_available_as_standalone(self, renderer_name):
    """Checks if API supports standalone rendering for a given renderer."""
    if self.is_v2():
      return renderer_name in ZyncApiFacade.SUPPORTED_STANDALONE_RENDERERS_V2
    return False

  def is_renderer_available_as_non_standalone(self, renderer_name):
    """Checks if API supports non-standalone rendering for a given renderer."""
    return not self.is_v2()

  def is_v2(self):
    """Checks if API is V2."""
    is_v2 = 'ZYNC_BACKEND_VERSION' in self._zync.CONFIG and self._zync.CONFIG[
        'ZYNC_BACKEND_VERSION'] == 2
    return is_v2

  def logout(self):
    """Logs out from Zync API."""
    self._zync.logout()

  def show_selected_files_dialog(self, project_name):
    """Prompts to select extra files."""
    self._file_select_dialog = self._file_select_dialog_module.FileSelectDialog(
        project_name)
    self._file_select_dialog.show()

  def submit_job(self, scene_file, params, job_type='3dsmax'):
    """Submits the job to Zync API."""
    self._zync.submit_job(job_type, scene_file, params=params)
